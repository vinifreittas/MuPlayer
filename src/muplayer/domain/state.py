from pydantic import BaseModel

from muplayer.domain.models import Song


class QueueState(BaseModel):
    songs: list[Song] = []
    current_index: int = -1
    active_song: Song | None = None
