import contextvars
import logging
from asyncio import Lock
from contextlib import asynccontextmanager

from sqlalchemy import BigInteger, Column, DateTime, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql.schema import ForeignKey, Index

log = logging.getLogger(__name__)

Base = declarative_base()

class Station(Base):
    __tablename__ = 'station'

    id      = Column(BigInteger, primary_key=True, autoincrement=True)
    key     = Column(String, unique=True)
    name    = Column(String, nullable=False)
    url     = Column(String, nullable=False)

class Pending(Base):
    """A flat record of seen plays so that they can be processed in the background"""
    __tablename__ = 'pending'

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    station     = Column(ForeignKey('station.id'))
    artist      = Column(String)
    title       = Column(String)
    seen_at     = Column(DateTime)
    picked_at   = Column(DateTime)

class Song(Base):
    __tablename__ = 'song'

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    # first 64 bits of sha256 of lower case artist and title sans puctuation
    key         = Column(BigInteger, nullable=False, unique=True)
    artist      = Column(String, nullable=False)
    title       = Column(String, nullable=False)
    spotify_uri = Column(String, unique=True)

    __table_args__ = (
        Index('artist_title_index', 'artist', 'title', unique=True),
    )

class Play(Base):
    __tablename__ = 'play'

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    station     = Column(ForeignKey('station.id'))
    song        = Column(ForeignKey('song.id'))
    at          = Column(DateTime, nullable=False)

class RadioDatabase:
    
    def __init__(self, db_file):
        self.db_file = db_file
        self._session = contextvars.ContextVar('session')
        self._lock = Lock()

        # TODO schema?

    async def connect(self):
        engine = self._engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/postgres', echo=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self):
        try:
            # subsequent
            session = self._session.get()
            log.debug('using existing session')
            yield session
        except LookupError:
            # first
            async with self._engine.connect() as connection:
                async with AsyncSession(bind=connection, expire_on_commit=False) as session:
                    log.debug('created new session')
                    token = self._session.set(session)
                    try:
                        yield session
                    finally:
                        self._session.reset(token)

    @asynccontextmanager
    async def transaction(self):
        async with self.session() as session:
            try:
                yield
                await session.commit()
            except:
                await session.rollback()
                raise

    async def add(self, item: Base):
        async with self.session() as session:
            session.add(item)            

    async def exec(self, query):
        # async with self._lock:
        async with self.session() as session:
            return await session.execute(query)

    async def first(self, query):
        result = await self.exec(query)
        return result.scalars().first()
