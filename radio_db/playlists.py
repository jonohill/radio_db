import asyncio
import json
import logging
from base64 import b64decode
from datetime import datetime, timedelta
from typing import Any, List, Tuple

from spotipy import Spotify, SpotifyOAuth, cache_handler
from sqlalchemy import and_, desc, func
from sqlalchemy.future import select

from .config import Config, PlaylistConfig, PlaylistType, StationConfig
from .db import Play, Playlist, RadioDatabase, Song, State, StateKey, Station

log = logging.getLogger(__name__)

PLAYLISTS = {
    PlaylistType.Top: {
        'name': "{station} most played",
        'description': "The most played songs on {station} for the last {days} days. Not official. Might have mistakes."
    }
}


class DbCacheHandler(cache_handler.CacheHandler):

    def __init__(self, db: RadioDatabase) -> None:
        super().__init__()
        self.db = db
        self.token: Any = {}
        self.needs_save = asyncio.Event()

    def get_cached_token(self):
        return self.token

    def save_token_to_cache(self, token_info: Any):
        self.token = token_info
        self.needs_save.set()

    async def populate_from_db(self, seed: str):
        token_row: State = await self.db.first(
            select(State).where(State.key == StateKey.SpotifyAuth)
        )
        if token_row:
            self.token = json.loads(token_row.value)
        else:
            token = json.loads(b64decode(seed).decode())
            self.save_token_to_cache(token)

    async def save_as_needed(self):
        log.debug('save_as_needed running')
        last_run = False
        while True:
            try:
                if not last_run:
                    await self.needs_save.wait()
                log.debug('needs_save set')
                self.needs_save.clear()
                async with self.db.transaction():
                    token_row: State = await self.db.first(
                        select(State).where(State.key == StateKey.SpotifyAuth).with_for_update()
                    )
                    if token_row:
                        token_row.value = json.dumps(self.token) # type: ignore
                    else:
                        token_row = State(key=StateKey.SpotifyAuth, value=json.dumps(self.token))
                    await self.db.add(token_row)
                    log.debug('added')
                if last_run:
                    break
            except asyncio.exceptions.CancelledError:
                log.debug('set last run')
                last_run = True

async def get_playlist_uri(db: RadioDatabase, spotify: Spotify, station: Station, type: PlaylistType, name: str, desc: str):
    get_query = (
        select(Playlist)
        .where(and_(Playlist.station == station.id, Playlist.type_ == type))
    )
    playlist = await db.first(get_query)
    if playlist and playlist.spotify_uri:
        return playlist.spotify_uri
    if not playlist:
        async with db.transaction():
            playlist = Playlist(
                station = station.id,
                type_ = type
            )
            await db.add(playlist)
    async with db.transaction():
        playlist: Playlist = await db.first(get_query.with_for_update())
        if not playlist.spotify_uri:
            user = spotify.current_user()
            assert user
            sp_playlist = spotify.user_playlist_create(user['id'], name, public=False, description=desc)
            assert sp_playlist
            playlist.spotify_uri = sp_playlist['uri']
            await db.add(playlist)
    return playlist.spotify_uri


async def update_top(db: RadioDatabase, spotify: Spotify, station: Station, playlist_config: PlaylistConfig):
    log.info(f'Updating top playlist for {station.name}')
    TOP = PLAYLISTS[PlaylistType.Top]

    playlist_name = TOP['name'].format(station=station.name)
    playlist_desc = TOP['description'].format(station=station.name, days=playlist_config.days)

    playlist_uri = await get_playlist_uri(db, spotify, station, PlaylistType.Top, playlist_name, playlist_desc)

    results: List[Tuple[datetime, int, Song]] = await db.exec(
        select(func.max(Play.at).label('last_played'), func.count(Play.id).label('play_count'), Song)
        .join(Song)
        .where(and_(Play.at > (datetime.now() - timedelta(days=7)), Play.station == station.id))
        .group_by(Song.id)
        .order_by(desc('play_count'), desc('last_played'))
    )
    items = []
    for n, (last_played, play_count, song) in enumerate(results):
        log.debug(f'Add to playlist: {last_played} {play_count} {song.artist} - {song.title}')
        items.append(song.spotify_uri)
        if n + 1 >= 100:
            break
    spotify.playlist_replace_items(playlist_uri, items)

async def update(config: Config, station_key: str):
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

        sp_conf = config.spotify
        cache_handler = DbCacheHandler(rdb)

        async def _update():
            log.debug('_update running')
            await cache_handler.populate_from_db(sp_conf.auth_seed)
            sp = Spotify(auth_manager=SpotifyOAuth(
                scope='playlist-modify-private', 
                redirect_uri='http://localhost:9090', 
                client_id=sp_conf.client_id, 
                client_secret=sp_conf.client_secret,
                cache_handler=cache_handler)
            )

            for playlist in station_config.playlists:
                log.info(f'Updating playlists for {station_config.name}')
                if playlist.type == PlaylistType.Top:
                    await update_top(rdb, sp, station, playlist)

        cache_save_task = asyncio.create_task(cache_handler.save_as_needed())
        update_task = asyncio.create_task(_update())
        await asyncio.wait([ update_task, cache_save_task ], return_when=asyncio.FIRST_COMPLETED)
        cache_save_task.cancel()
        await cache_save_task
