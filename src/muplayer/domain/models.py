from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Song(BaseModel):
    # Permite que o Pydantic leia diretamente objetos de ORM usando `model_validate`
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    title: str
    artist: str
    album: str = "YouTube Audio"
    duration: int = Field(default=0, ge=0)
    source: str | None = None
    added_at: datetime | None = None

    @field_validator("duration", mode="before")
    @classmethod
    def validate_duration(cls, v: int | float | None) -> int:
        """Clamps duration to 0 if None or negative (DT-17)."""
        if v is None:
            return 0
        if isinstance(v, int):
            return v if v >= 0 else 0
        if v < 0:
            return 0
        return int(v)

    @property
    def has_source(self) -> bool:
        """Returns True if the song has a non-empty audio source URL."""
        return bool(self.source and self.source.strip())


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

    @property
    def total_duration(self) -> int:
        """Returns total duration of all songs in the playlist in seconds."""
        return sum(s.duration for s in self.songs)

    def contains_song(self, song_id: int) -> bool:
        """Checks if a song with the given ID exists in the playlist."""
        if song_id is None:
            return False
        return any(s.id == song_id for s in self.songs)
