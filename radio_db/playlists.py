most_played = """\
    select max(p.at), count(p.id), s.artist, s.title, s.spotify_uri from play p
    left join song s on s.id = p.song
    where p.at > (p.at - interval '7 days')
    group by s.id
    order by count(p.id) desc, max(p.id) desc
    limit 100;
"""

import asyncio
from sqlalchemy import func, desc
from sqlalchemy.future import select

from db import RadioDatabase, Play, Song, Station
from datetime import datetime, timedelta

async def main(station_key: str):
    rdb = RadioDatabase('127.0.0.1', 'postgres', 'postgres', 'postgres')
    await rdb.connect()
    async with rdb.session():
        station = await rdb.first(
            select(Station)
            .where(Station.key == station_key)
        )
        if not station:
            raise Exception(f'{station_key} is not a known station')

        results = await rdb.exec(
            select(func.max(Play.at).label('last_played'), func.count(Play.id).label('play_count'), Song)
            .join(Song)
            .where(Play.at > (datetime.now() - timedelta(days=7)))
            .group_by(Song.id)
            .order_by(desc('play_count'), desc('last_played'))
        )
        for n, (last_played, play_count, song) in enumerate(results):
            print(f'{last_played} {play_count} {song.artist} - {song.title}')
            if n + 1 >= 100:
                break

asyncio.run(main('hauraki'))
