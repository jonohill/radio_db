# pyright: strict

# import asyncio

from typing import Iterator

import inquirer
from sqlalchemy import select

from radio_db import db
from radio_db.config import Config
from radio_db.db import RadioDatabase, Station
from radio_db.stations import get_station, get_top_songs


async def fix_match_by_matched_song_name(db: RadioDatabase):
    ...


async def fix_match_by_seen_song_name(db: RadioDatabase):
    ...


async def fix_match_by_station(db: RadioDatabase):
    ...


async def fix_match(db: RadioDatabase):
    task = inquirer.list_input('Find match to fix by', choices=[
        ('Station', fix_match_by_station),
        ('Seen song name', fix_match_by_seen_song_name),
        ('Matched song name', fix_match_by_matched_song_name),
    ])
    await task(db)


async def show_top_songs(db: RadioDatabase, station: Station):
    n = 1
    async for last_played, play_count, song in get_top_songs(db, station):
        print(f'{song.artist} - {song.title}: {play_count} plays, last played {last_played}')
        n += 1
        if n > 10:
            break


async def manage_station(rdb: RadioDatabase, station_id: int):
    station = await get_station(rdb, station_id)
    assert station is not None
    task = inquirer.list_input('See what?', choices=[
        ('Top songs', show_top_songs)
    ])

    await task(rdb, station)


async def show_stations(rdb: RadioDatabase):
    stations: Iterator[Station] = await rdb.query(
        select(db.Station)
    )
    chosen = inquirer.list_input('Manage station', choices=[ (s.name, s.id) for s in stations ])
    await manage_station(rdb, chosen)


async def quit(_: RadioDatabase):
    print('Bye!')
    exit(0)


async def list_tasks(db: RadioDatabase):
    while True:
        task = inquirer.list_input('Manage what?', choices=[
            ('Matches', fix_match),
            ('Stations', show_stations),
            ('Quit', quit)
        ])
        await task(db)


async def run(config: Config):
    db_conf = config.database
    rdb = db.RadioDatabase(db_conf.connection_string)
    await rdb.connect()

    await list_tasks(rdb)

