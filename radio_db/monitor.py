import asyncio
import logging
import re
from asyncio import to_thread
from datetime import datetime, timedelta
from hashlib import sha256
from typing import List

from pydantic import BaseModel
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from sqlalchemy import and_, delete, null, or_, update
from sqlalchemy.future import select

from . import db, stream
from .config import StationConfig
from .db import Pending, Play, RadioDatabase, Song, Station

log = logging.getLogger(__name__)

class SpotifyArtist(BaseModel):
    name: str

class SpotifyTrack(BaseModel):
    name: str
    artists: List[SpotifyArtist]
    uri: str

class SpotifyTracks(BaseModel):
    items: List[SpotifyTrack]

class SpotifyResult(BaseModel):
    tracks: SpotifyTracks

async def process_pending(rdb: RadioDatabase, client_id, client_secret, stations: List[StationConfig]):
    spotify_auth = SpotifyClientCredentials(client_id, client_secret)
    spotify = Spotify(auth_manager=spotify_auth)

    RE_NO_PUNC = re.compile(r'[^\w\s]')
    RE_SPACES = re.compile(r'\s+')

    async with rdb.session():
        while True:
            next_pending: Pending = await rdb.first(
                select(Pending)
                .where(
                    or_(
                        Pending.picked_at == null(),
                        Pending.picked_at <= (datetime.now() - timedelta(minutes=5))
                    )
                )
                .order_by(Pending.seen_at)
            )
            if not next_pending:
                await asyncio.sleep(180)
                continue
            async with rdb.transaction():
                # Take ownership by setting picked_at
                result = await rdb.exec(
                    update(Pending)
                    .where(
                        and_(
                            Pending.id == next_pending.id,
                            Pending.picked_at == next_pending.picked_at
                        )
                    )
                    .values(picked_at=datetime.now())
                    .execution_options(synchronize_session='fetch')
                )
            if result.rowcount == 0:
                # If the picked_at has changed then someone else picked it up in the mean time
                continue

            async def _process_song():
                station = await rdb.first(
                    select(Station)
                    .where(Station.id == next_pending.station)
                )
                station_config = next(( s for s in stations if s.key == station.key ))
                
                # Try for an exact match in the database
                artist = next_pending.artist
                title = next_pending.title
                normalised = f'{next_pending.artist} {next_pending.title}'.replace(' - ', ' ').lower()

                filters = station_config.filters
                if filters:
                    if filters.ignore and filters.ignore.search(normalised):
                        log.info(f'Ignoring {normalised}')
                        return
                    if filters.blank:
                        normalised = filters.blank.sub('', normalised)
                
                key_input = RE_NO_PUNC.sub('', normalised)
                key = int.from_bytes(sha256(RE_SPACES.sub(' ', key_input).encode()).digest()[:8], 'little', signed=True)
                song = await rdb.first(
                    select(Song)
                    .where(Song.key == key)
                )

                # Failing that, try to find it on Spotify
                if not song:
                    response = await to_thread(lambda: spotify.search(q=normalised, type='track'))
                    result = SpotifyResult(**response)
                    items = result.tracks.items
                    if len(items) > 0:
                        item = items[0]
                        artist = item.artists[0].name
                        title = item.name
                        uri = item.uri
        
                        # And check - maybe it actually is in the database
                        song = await rdb.first(
                            select(Song)
                            .where(Song.spotify_uri == uri)
                        )
                        # Or not
                        if not song:
                            song = Song(key=key, artist=artist, title=title, spotify_uri=uri)
                            async with rdb.transaction():
                                await rdb.add(song)
                if not song:
                    log.warning(f'{normalised} was not found on spotify')

            song = await _process_song()

            async with rdb.transaction():
                if song:
                    play = Play(
                        station = next_pending.station,
                        song = song.id,
                        at = next_pending.seen_at
                    )
                    await rdb.add(play)
                await rdb.exec(
                    delete(Pending)
                    .where(Pending.id == next_pending.id)
                )
                

async def monitor_station(rdb: RadioDatabase, station_config: StationConfig):
    async with rdb.session():
        # Fetch and update, or insert station
        station = await rdb.first(
            select(db.Station)
            .where(db.Station.key == station_config.key)
        )

        if station:
            station.name = station_config.name
            station.url = station_config.url
        else:
            station = db.Station(**station_config.dict(exclude={ 'filters', 'playlists' }))
        async with rdb.transaction():
            await rdb.add(station)

        artist = ''
        title = ''
        async for item in stream.read_song_info(station_config.url):
            if 'artist' in item and 'title' in item:
                new_artist = item['artist']
                new_title = item['title']
                if new_artist != artist or new_title != title:
                    artist = new_artist
                    title = new_title
                    pending = db.Pending(artist=artist, title=title, seen_at=datetime.now(), station=station.id)
                    async with rdb.transaction():
                        await rdb.add(pending)

async def run(config):
    db_conf = config.database
    rdb = db.RadioDatabase(db_conf.host, db_conf.username, db_conf.password, db_conf.name)
    await rdb.connect()
    for t in asyncio.as_completed(
        [ monitor_station(rdb, s) for s in config.stations ] + 
        [ process_pending(rdb, config.spotify.client_id, config.spotify.client_secret, config.stations) ]):
        await t

if __name__ == '__main__':
    asyncio.run(run())
