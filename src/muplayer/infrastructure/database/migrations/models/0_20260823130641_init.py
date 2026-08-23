from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "playlists" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "songs" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "artist" VARCHAR(255) NOT NULL,
    "album" VARCHAR(255) NOT NULL  DEFAULT 'YouTube Audio',
    "duration" INT NOT NULL  DEFAULT 0,
    "source" VARCHAR(2048),
    CONSTRAINT "uid_songs_title_f5e244" UNIQUE ("title", "artist", "album", "duration")
);
CREATE INDEX IF NOT EXISTS "idx_songs_title_01b785" ON "songs" ("title");
CREATE INDEX IF NOT EXISTS "idx_songs_artist_919d90" ON "songs" ("artist");
CREATE TABLE IF NOT EXISTS "playlist_songs" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "order" INT NOT NULL,
    "added_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "playlist_id" INT NOT NULL REFERENCES "playlists" ("id") ON DELETE CASCADE,
    "song_id" INT NOT NULL REFERENCES "songs" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmVtT4jAUx78K06d1xnWQxcvsW0UcWRdwpHvTcTqhDaVDm2CarjIO332T9BKaFiwqCi"
    "svCifntDm/npz8Gx41H9vQC/YuPTDx3ID2MHIM0Peg9rXyqCHg8w/znXYrGhiPpQs30Dhc"
    "G8fuZsD8xRDoB5QAi7LRAfACyEw2DCzijqmLEbOi0PO4EVvM0UWONIXIvQuhSbED6RASNn"
    "Bzy8wusuEDDJKv45E5cKFnZ2bv2vzewm7SyVjYWoieCUd+t75pYS/0kXQeT+gQo9TbRZRb"
    "HYggARTyy1MS8unz2cX5JhlFM5Uu0RRnYmw4AKFHZ9ItycDCiPNjswlEgg6/y+fafv2ofv"
    "zlsH7MXMRMUsvRNEpP5h4FCgIdQ5uKcUBB5CEwSm6Y2Ax0eXSp/9P0ElaL8CUGyU/WzDoB"
    "lMCAbUPbBDTP7JTlTV0fFoObjVPY2XHgXvJhTUkSCOwu8iZxlS/AZrTazZ6hty95Jn4Q3H"
    "kCkG40+UhNWCeK9dPhDrdj1jui1pJepPKrZZxX+NfKdbfTFARxQB0i7ij9jGuNzwmEFJsI"
    "35sMuVyQiTUBk3moaRdbqo0oUR91RfDOvxy4mYiPBI1vXoNRYRtOSikP8QwT6DroAk4Eyx"
    "abFUAWLGCnbODp5r1+MKdJQSRWuUwJuE93d3WBsVxZhpCKbBt6r6GfNrVcKb4Cwoz22Vx8"
    "M8usGB0vyD6wRveA2GamMvkIrmHFkvrmh/yar1oAAo7In2fB51xYoAsk6BLyc6s8N055iv"
    "85co0hIMXoEn8FHpvyc1bpyun54MH0IHLokCM7OFjA6qd+1TjXrz4xrx1lb7WY5qLP0pvZ"
    "yK3iXAPFmdv/5/ffAmkqXrCDfBmcxBc4u7iCHhCIn9QGG7rBTV+4LWWFQgHLNkATA/O//7"
    "1SEAmYys6bSYfwcmIdRK3EiBsmAvkIThKeYlOO9Ub6SOLxNDYep0OCQ2eYL/C5YoXZzRzg"
    "6UKhsfCcq+T51oqOtW406tL43oTGwh94/dAXjTwk0UK+3YqQ1YqQ9CmUVSFpwOvIkHwLWE"
    "8dIou0LCgZ8cFIJYu4NKgkYFWc8puK9geHRtiHFT20Xay9O7O035XvYbMhb3eGVH3vTjar"
    "YEJiLdW6ZMSzKi1ebm8p/7PVVa0flykv5rZTdNi2FdvvJbazwvFlgnuzTzcLRXcuJVV4y5"
    "eVrOhWRbUqulVR/nLRndbFXM2tQ+JaQ61AcMcjC9U2kD7bs7wNktF/IQkK9+/5u9FMyNsJ"
    "n/VQiKz8l9GHkftmQtqvVktAYl65g0+MKEQFbxzfet3OnBNPGaLA+oFYEje2a9HdCu96t+"
    "uJbgEpnnXmZLOTsGvrv5VTzE7je/dEPbLkFzhZTha9/m9A03++gtrE"
)
