from tortoise import fields
from tortoise.models import Model


class SongTable(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=255, db_index=True)
    artist = fields.CharField(max_length=255, db_index=True)
    album = fields.CharField(max_length=255, default="YouTube Audio")
    duration = fields.IntField(default=0)
    source = fields.CharField(max_length=2048, null=True)  # URLs can be long

    class Meta:
        table = "songs"
        unique_together = (("title", "artist", "album", "duration"),)

    def __str__(self) -> str:
        return f"{self.title} - {self.artist}"


class PlaylistTable(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    songs = fields.ManyToManyField("models.SongTable", through="playlist_songs", related_name="playlists")

    class Meta:
        table = "playlists"

    def __str__(self) -> str:
        return self.name


class PlaylistSongTable(Model):
    id = fields.IntField(primary_key=True)
    playlist = fields.ForeignKeyField("models.PlaylistTable", on_delete=fields.CASCADE)
    song = fields.ForeignKeyField("models.SongTable", on_delete=fields.CASCADE)

    order = fields.IntField()
    added_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "playlist_songs"
        ordering = ("order",)

    def __str__(self) -> str:
        return f"Playlist {self.playlist_id} - Song {self.song_id} (#{self.order})"
