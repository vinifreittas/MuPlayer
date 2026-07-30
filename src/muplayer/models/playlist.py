from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .song import Song


class Playlist(BaseModel):
    # Permite que o Pydantic leia diretamente objetos de ORM usando `model_validate`
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str
    songs: list[Song] = []
    created_at: datetime | None = None

    @property
    def song_count(self) -> int:
        """Returns the number of songs in the playlist."""
        return len(self.songs)
