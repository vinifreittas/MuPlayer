import random

from pydantic import BaseModel

from muplayer.domain.models import Song


class QueueState(BaseModel):
    songs: list[Song] = []
    current_index: int = -1
    active_song: Song | None = None
    is_shuffling: bool = False
    is_repeating: bool = False

    def toggle_shuffle(self) -> bool:
        """Toggles shuffle mode and returns new state."""
        self.is_shuffling = not self.is_shuffling
        return self.is_shuffling

    def toggle_repeat(self) -> bool:
        """Toggles repeat mode and returns new state."""
        self.is_repeating = not self.is_repeating
        return self.is_repeating

    def set_songs(self, songs: list[Song], start_song: Song | None = None) -> int:
        """Updates queue songs and returns the index of the selected starting song."""
        self.songs = songs
        if start_song:
            if start_song.id is not None:
                for idx, s in enumerate(songs):
                    if s.id == start_song.id:
                        self.current_index = idx
                        return idx
            elif start_song.source:
                for idx, s in enumerate(songs):
                    if s.source == start_song.source:
                        self.current_index = idx
                        return idx
            try:
                self.current_index = self.songs.index(start_song)
            except ValueError:
                self.current_index = 0
        else:
            self.current_index = 0
        return self.current_index

    def select_track(self, index: int) -> Song | None:
        """Validates and sets the active song at the specified index."""
        if not self.songs or not (0 <= index < len(self.songs)):
            self.active_song = None
            return None

        self.current_index = index
        self.active_song = self.songs[index]
        return self.active_song

    def get_next_index(self, is_shuffling: bool | None = None, is_repeating: bool | None = None) -> int | None:
        """Calculates next track index based on shuffle and repeat rules."""
        if not self.songs:
            return None

        use_shuffle = self.is_shuffling if is_shuffling is None else is_shuffling
        use_repeat = self.is_repeating if is_repeating is None else is_repeating

        if use_shuffle and len(self.songs) > 1:
            idx = random.randrange(len(self.songs) - 1)
            if idx >= self.current_index:
                idx += 1
            next_idx = idx
        else:
            next_idx = self.current_index + 1

        if next_idx >= len(self.songs):
            if use_repeat:
                return 0
            return None

        return next_idx

    def get_prev_index(self, current_time: int = 0) -> int:
        """Returns previous track index considering elapsed playback time."""
        if current_time > 3 or self.current_index <= 0:
            return self.current_index
        return self.current_index - 1

    def clear(self) -> None:
        """Resets the queue state."""
        self.songs = []
        self.current_index = -1
        self.active_song = None
