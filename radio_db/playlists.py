most_played = """\
    select max(p.at), count(p.id), s.artist, s.title, s.spotify_uri from play p
    left join song s on s.id = p.song
    where p.at > (p.at - interval '7 days')
    group by s.id
    order by count(p.id) desc, max(p.id) desc
    limit 100;
"""

import asyncio
from sqlalchemy import func, desc, and_
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from .db import RadioDatabase, Play, Song, Station, Playlist
from datetime import datetime, timedelta
from .config import Config, PlaylistConfig, PlaylistType, StationConfig
from spotipy import Spotify, SpotifyOAuth

import logging

log = logging.getLogger(__name__)

PLAYLISTS = {
    'top': {
        'name': "{station} most played",
        'description': "The most played songs on {station} for the last {days} days. Not official. Might have mistakes."
    }
}

async def get_playlist_uri(db: RadioDatabase, spotify: Spotify, station_id: int, type: PlaylistType):
    get_query = (
        select(Playlist)
        .where(and_(Playlist.station == station_id, Playlist.type_ == type))
    )
    playlist = await db.first(get_query)
    if playlist and playlist.spotify_uri:
        return playlist.spotify_uri
    if not playlist:
        async with db.transaction():
            playlist = Playlist(
                station = station_id,
                type_ = type
            )
            await db.add(playlist)
    async with db.transaction():
        playlist = await db.first(get_query.with_for_update())
        spotify_user = spotify.current_user()
        print(spotify_user)
        # spotify.user_playlist_create()


async def update_top(db: RadioDatabase, spotify: Spotify, station: StationConfig, station_id: int, playlist_config: PlaylistConfig):
    log.info(f'Updating top playlist for {station.name}')
    TOP = PLAYLISTS['top']

    playlist_name = TOP['name'].format(station=station.name)
    playlist_desc = TOP['description'].format(station=station.name, days=playlist_config.days)

    await get_playlist_uri(db, spotify, station_id, PlaylistType.Top)

    results = await db.exec(
        select(func.max(Play.at).label('last_played'), func.count(Play.id).label('play_count'), Song)
        .join(Song)
        .where(and_(Play.at > (datetime.now() - timedelta(days=7)), Play.station == station_id))
        .group_by(Song.id)
        .order_by(desc('play_count'), desc('last_played'))
    )
    for n, (last_played, play_count, song) in enumerate(results):
        print(f'{last_played} {play_count} {song.artist} - {song.title}')
        if n + 1 >= 100:
            break

async def update(config: Config, station_key: str):
    sp_conf = config.spotify
    sp = Spotify(auth_manager=SpotifyOAuth(
        scope='playlist-modify-private', 
        redirect_uri='http://localhost:9090', 
        client_id=sp_conf.client_id, 
        client_secret=sp_conf.client_secret)
    )
    sp.current_user()

    db_conf = config.database
    rdb = RadioDatabase(db_conf.host, db_conf.username, db_conf.password, db_conf.name)
    await rdb.connect()
    async with rdb.session():
        station = await rdb.first(
            select(Station)
            .where(Station.key == station_key)
        )
        if not station:
            raise Exception(f'{station_key} is not a known station')

        station_config: StationConfig = next(( s for s in config.stations if s.key == station_key ))

        for playlist in station_config.playlists:
            log.info(f'Updating playlists for {station_config.name}')
            if playlist.type == PlaylistType.Top:
                await update_top(rdb, sp, station_config, station.id, playlist)
