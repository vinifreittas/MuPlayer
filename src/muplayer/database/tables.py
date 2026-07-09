from tortoise import fields
from tortoise.models import Model


class Song(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255, index=True)  # Added index for faster search
    artist = fields.CharField(max_length=255, index=True)  # Added index for faster search
    album = fields.CharField(max_length=255)
    duration = fields.IntField()  # Kept as IntField (seconds)
    source = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "songs"
        unique_together = ("title", "artist", "album", "duration")

    def __str__(self) -> str:
        return f"{self.title} - {self.artist}"


class Playlist(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    songs = fields.ManyToManyField("models.Song", through="playlist_songs", related_name="playlists")

    class Meta:
        table = "playlists"

    def __str__(self) -> str:
        return self.name


class PlaylistSong(Model):
    id = fields.IntField(pk=True)
    playlist = fields.ForeignKeyField("models.Playlist", on_delete=fields.CASCADE)
    song = fields.ForeignKeyField("models.Song", on_delete=fields.CASCADE)

    order = fields.IntField()
    added_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "playlist_songs"
        unique_together = (("playlist", "order"),)
        ordering = ("order",)

    def __str__(self) -> str:
        return f"Playlist {self.playlist_id} - Song {self.song_id} (#{self.order})"
