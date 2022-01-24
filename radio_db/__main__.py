import asyncio
import base64
import json
import logging
import sys
from functools import wraps

import typer
from spotipy import CacheHandler, Spotify, SpotifyOAuth
from typer import Option

from . import playlists
from .config import from_yaml as config_from_yaml
from .monitor import run as run_monitor

log = logging.getLogger('__name__')

app = typer.Typer()

config = None

def run_sync(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrap

@app.callback()
def read_config(
    config_file='config.yml', 
    verbosity: int = Option(0, '--verbose', '-v', count=True),
):
    global config
    config = config_from_yaml(config_file)

    level = max(logging.WARNING - verbosity * 10, 0)
    logging.basicConfig(level=level)
    log.debug('Debug logging is enabled')

@app.command()
@run_sync
async def monitor():
    await run_monitor(config)

@app.command()
@run_sync
async def update_playlists(station_key: str = typer.Argument(None)):
    if not config:
        log.error('Config not loaded')
        return

    for station in config.stations:
        if not station_key or station.key == station_key:
            await playlists.update(config, station.key)

@app.command()
def authorise():
    """Authorise Spotify. Run this on something with a browser."""

    if not config:
        log.error('Config not loaded')
        return

    def err(msg):
        print(msg, file=sys.stderr)

    class TokenEchoer(CacheHandler):
        
        def get_cached_token(self):
            return {}
        
        def save_token_to_cache(self, token_info):
            err('Set this as the spotify.auth_seed (env: RDB_SPOTIFY_AUTH_SEED) config value:')
            print(base64.b64encode(json.dumps(token_info).encode()).decode())

    err("We've opened Spotify in your browser. Please authorise and then return here.")

    sp_conf = config.spotify
    sp = Spotify(auth_manager=SpotifyOAuth(
        scope='playlist-modify-private,playlist-modify-public', 
        redirect_uri='http://localhost:9090', 
        client_id=sp_conf.client_id, 
        client_secret=sp_conf.client_secret,
        cache_handler=TokenEchoer())
    )
    sp.current_user()

if __name__ == '__main__':
    app()
