import asyncio
import contextvars
import enum
import logging
from asyncio import Lock
from contextlib import asynccontextmanager
from urllib.parse import quote_plus

from sqlalchemy import BigInteger, Column, DateTime, Enum, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql.schema import ForeignKey, Index

from radio_db.config import PlaylistType

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

class Playlist(Base):
    __tablename__ = 'playlist'

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    station     = Column(ForeignKey('station.id'))
    type_       = Column(Enum(PlaylistType))
    spotify_uri = Column(String, unique=True)

class StateKey(enum.Enum):
    SpotifyAuth = 'spotify_auth'

class State(Base):
    __tablename__ = 'state'

    key         = Column(Enum(StateKey), primary_key=True)
    value       = Column(String)


class RadioDatabase:
    
    def __init__(self, host, user, password, db):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self._tx_lock = asyncio.Lock()
        self._session = contextvars.ContextVar('session')
        self._lock = Lock()

    def get_url(self):
        q = quote_plus
        return f'postgresql+asyncpg://{q(self.user)}:{q(self.password)}@{q(self.host)}:5432/{q(self.db)}'

    def create_engine(self):
        engine = self._engine = create_async_engine(self.get_url())
        return engine

    async def connect(self):
        engine = self.create_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self):
        try:
            # subsequent
            session = self._session.get()
            log.debug('using existing session')
            yield session
            return
        except LookupError:
            pass
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
        async with self._tx_lock, self.session() as session:
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
