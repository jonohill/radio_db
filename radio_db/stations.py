from datetime import datetime, timedelta
from typing import Iterable, Tuple

from sqlalchemy import and_, desc, func, select
from radio_db.db import Play, RadioDatabase, Song, Station


async def get_station(rdb: RadioDatabase, id: int):
    station: Station | None = await rdb.first(
        select(Station).where(Station.id == id)
    )
    return station


async def get_top_songs(db: RadioDatabase, station: Station):
    results: Iterable[Tuple[datetime, int, Song]] = await db.exec(
        select(func.max(Play.at).label('last_played'), func.count(Play.id).label('play_count'), Song)
            .join(Song)
            .where(and_(Play.at > (datetime.now() - timedelta(days=7)), Play.station == station.id)) # type: ignore
            .group_by(Song.id)
            .order_by(desc('play_count'), desc('last_played'))
    )
    for result in results:
        yield result




