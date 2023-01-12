import asyncio
import os
from typing import Optional

import hypercorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from hypercorn.asyncio import serve
from pydantic import BaseModel
from radio_db import db
from radio_db.config import from_yaml as config_from_yaml

from . import stations


async def run(config, rdb):

    app = FastAPI()

    app.mount('/api/stations', stations.get_app(rdb))

    app.mount('/', StaticFiles(html=True, directory=os.path.join(os.path.dirname(__file__), 'ui/build')), name='ui')

    hc_config = hypercorn.config.Config()
    hc_config.bind = f'0.0.0.0:{config.admin_port}'
    await serve(app, hc_config) # type: ignore


if __name__ == '__main__':
    config = config_from_yaml()
    db_conf = config.database
    rdb = db.RadioDatabase(db_conf.host, db_conf.username, db_conf.password, db_conf.name)
    
    async def main():
        await rdb.connect()
        await run(config, rdb)

    asyncio.run(main())
