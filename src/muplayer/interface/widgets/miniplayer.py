from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Label, ProgressBar

from muplayer.interface.helpers import format_time
from muplayer.models import Song
from muplayer.utils.i18n import t


class MiniPlayer(Horizontal):
    """Isolated Widget responsible for playback controls and status."""

    current_song = reactive[Song | None](None)
    time_elapsed = reactive(0)
    is_playing = reactive(False)
    volume = reactive(50)

    class TogglePlay(Message):
        """Custom event sent to coordinate playback state with the app root."""

    class NextTrack(Message):
        """Event to request the next track."""

    class PrevTrack(Message):
        """Event to request the previous track."""

    class ToggleShuffle(Message):
        """DT-11: Fired when the shuffle button is pressed. Replaces direct app.action_* call."""

    class ToggleRepeat(Message):
        """DT-11: Fired when the repeat button is pressed. Replaces direct app.action_* call."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="now-playing"):
            yield Label("💿", id="track-art")
            with Vertical(id="track-info"):
                yield Label("", id="track-title")
                yield Label("", id="track-artist")

        with Vertical(id="player-controls"):
            with Horizontal(id="control-buttons"):
                yield Button("⏮", id="prev-button", classes="control-btn")
                yield Button("▶", id="play-button", classes="control-btn play-btn")
                yield Button("⏭", id="next-button", classes="control-btn")
            with Horizontal(id="progress-area"):
                yield Label("0:00", id="time-elapsed")
                yield ProgressBar(total=100, show_bar=True, show_percentage=False, show_eta=False, id="progress-bar")
                yield Label("0:00", id="time-total")

        with Vertical(id="extra-controls"):
            with Horizontal(id="volume-area"):
                yield Label("🔊", id="volume-icon")
                yield ProgressBar(total=100, show_bar=True, show_percentage=False, show_eta=False, id="volume-bar")
            with Horizontal(id="repeat-shuffle"):
                yield Button("🔁", id="repeat-btn", classes="icon-btn")
                yield Button("🔀", id="shuffle-btn", classes="icon-btn")

    def update_translations(self) -> None:
        """Update fallback track title when language changes if no song is playing."""
        if self.current_song is None:
            self.watch_current_song(None)

    def watch_current_song(self, current_song: Song | None) -> None:
        song_data = current_song or Song(title=t("no_track_playing"), artist="", album="", duration=0)

        self.query_one("#track-title", Label).update(song_data.title)
        self.query_one("#track-artist", Label).update(song_data.artist)
        self.query_one("#time-total", Label).update(format_time(song_data.duration))
        # Setting time_elapsed to 0 automatically triggers watch_time_elapsed(0),
        # which resets both the time label and the progress bar — no manual update needed.
        self.time_elapsed = 0

    def watch_is_playing(self, is_playing: bool) -> None:
        self.query_one("#play-button", Button).label = "⏸" if is_playing else "▶"

    def watch_time_elapsed(self, seconds: int) -> None:
        self.query_one("#time-elapsed", Label).update(format_time(seconds))

        if self.current_song and self.current_song.duration > 0:
            percentage = (seconds / self.current_song.duration) * 100
            self.query_one("#progress-bar", ProgressBar).update(progress=percentage)

    def watch_volume(self, volume: int) -> None:
        self.query_one("#volume-bar", ProgressBar).update(progress=volume)

    @on(Button.Pressed, "#play-button")
    def _on_play_press(self) -> None:
        self.post_message(self.TogglePlay())

    @on(Button.Pressed, "#next-button")
    def _on_next_press(self) -> None:
        self.post_message(self.NextTrack())

    @on(Button.Pressed, "#prev-button")
    def _on_prev_press(self) -> None:
        self.post_message(self.PrevTrack())

    @on(Button.Pressed, "#shuffle-btn")
    def _on_shuffle_press(self) -> None:
        """DT-11: Post message instead of calling self.app.action_toggle_shuffle() directly."""
        self.post_message(self.ToggleShuffle())

    @on(Button.Pressed, "#repeat-btn")
    def _on_repeat_press(self) -> None:
        """DT-11: Post message instead of calling self.app.action_toggle_repeat() directly."""
        self.post_message(self.ToggleRepeat())
