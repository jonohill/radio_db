import typer
from functools import wraps
import asyncio
from .monitor import run as run_monitor
from .config import from_yaml as config_from_yaml

app = typer.Typer()

config = None

def run_sync(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrap

@app.callback()
def read_config(config_file='config.yml'):
    global config
    config = config_from_yaml(config_file)

@app.command()
@run_sync
async def monitor():
    await run_monitor()

@app.command()
@run_sync
async def update_playlists():
    print('b')

if __name__ == '__main__':
    app()

