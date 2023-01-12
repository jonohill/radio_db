from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from radio_db import stations
from radio_db.db import RadioDatabase


class Station(BaseModel):
    id: str
    key: str
    name: str
    url: str

    class Config:
        orm_mode = True


class Song(BaseModel):
    id: str
    artist: str
    title: str
    spotify_uri: str

    class Config:
        orm_mode = True


class LastPlayed(BaseModel):
    last_played: datetime
    song: Song


def get_app(rdb: RadioDatabase):

    app = FastAPI()

    @app.get('/')
    async def get_stations():
        result = await stations.get_stations(rdb)
        return [ Station.from_orm(station) for station in result ]


    @app.get('/{id}')
    async def get_station(id: int):
        return Station.from_orm(await stations.get_station(rdb, id))


    @app.get('/{id}/last-played')
    async def get_last_played(id: int):
        last_played = []
        async for lp, s in stations.get_last_played(rdb, id):
            last_played.append(LastPlayed(last_played=lp, song=Song.from_orm(s)))
            if len(last_played) >= 10:
                break    
        return last_played
        

    return app
