from pydantic import BaseModel, BaseSettings
from enum import Enum
from typing import Pattern, List
from ruamel.yaml import YAML

class PlaylistType(Enum):
    Top = 'top'

class FilterConfig(BaseModel):
    blank: Pattern = None

class PlaylistConfig(BaseModel):
    type: PlaylistType = PlaylistType.Top
    days: int = 7
    limit: int = 100

class StationConfig(BaseModel):
    key: str
    name: str
    url: str
    filters: FilterConfig = None

class SpotifyConfig(BaseSettings):
    client_id: str
    client_secret: str

    class Config:
        env_prefix = 'RDB_SPOTIFY_'
        env_file = '.env'

class DatabaseConfig(BaseSettings):
    host: str
    username: str
    password: str
    name: str
    
    class Config:
        env_prefix = 'RDB_DATABASE_'
        env_file = '.env'

class Config(BaseSettings):
    stations: List[StationConfig]
    database: DatabaseConfig = DatabaseConfig()
    spotify: SpotifyConfig = SpotifyConfig()

    class Config:
        env_prefix = 'RDB_'
        env_file = '.env'

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

def from_yaml(file_path):
    with open(file_path, 'r') as f:
        return Config(**YAML().load(f))
