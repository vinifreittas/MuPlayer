from pydantic import BaseModel

from .song import Song


class Playlist(BaseModel):
    name: str
    songs: list[Song] = []
