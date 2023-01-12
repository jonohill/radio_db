from datetime import datetime, timedelta
from typing import Iterable, Tuple
from pydantic import BaseModel

from sqlalchemy import and_, desc, func, select

from radio_db import db
from radio_db.db import RadioDatabase





async def get_station(rdb: RadioDatabase, id: int):
    station: db.Station | None = await rdb.first(
        select(db.Station).where(db.Station.id == id)
    )
    return station


async def get_stations(rdb: RadioDatabase):
    stations: Iterable[db.Station] = await rdb.query(
        select(db.Station)
    )
    return stations


async def get_top_songs(rdb: RadioDatabase, station_id: int):
    results: Iterable[Tuple[datetime, int, db.Song]] = await rdb.exec(
        select(func.max(db.Play.at).label('last_played'), func.count(db.Play.id).label('play_count'), db.Song)
            .join(db.Song)
            .where(and_(Play.at > (datetime.now() - timedelta(days=7)), Play.station == station_id)) # type: ignore
            .group_by(db.Song.id)
            .order_by(desc('play_count'), desc('last_played'))
    )
    for result in results:
        yield result


async def get_last_played(rdb: RadioDatabase, station_id: int):
    results: Iterable[Tuple[datetime, db.Song]] = await rdb.exec( # type: ignore
        select(db.Play.at.label('last_played'), db.Song)
            .join(db.Song)
            .where(db.Play.station == station_id)
            .order_by(desc(db.Play.at))
    )
    for result in results:
        yield result
