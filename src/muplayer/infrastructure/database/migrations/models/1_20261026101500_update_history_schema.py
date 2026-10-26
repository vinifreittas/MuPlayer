from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    res, _ = await db.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='history';")
    if not res:
        return """
        CREATE TABLE IF NOT EXISTS "history" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "artist" VARCHAR(255) NOT NULL,
    "album" VARCHAR(255) NOT NULL DEFAULT 'YouTube Audio',
    "duration" INT NOT NULL DEFAULT 0,
    "source" VARCHAR(2048) NOT NULL,
    "played_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_history_title_72d0ea" ON "history" ("title");
CREATE INDEX IF NOT EXISTS "idx_history_artist_f58209" ON "history" ("artist");
CREATE INDEX IF NOT EXISTS "idx_history_source_c6e08f" ON "history" ("source");
CREATE INDEX IF NOT EXISTS "idx_history_played__c71bb4" ON "history" ("played_at");
"""

    return """
        CREATE TABLE IF NOT EXISTS "history_new" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "artist" VARCHAR(255) NOT NULL,
    "album" VARCHAR(255) NOT NULL DEFAULT 'YouTube Audio',
    "duration" INT NOT NULL DEFAULT 0,
    "source" VARCHAR(2048) NOT NULL,
    "played_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_history_title_72d0ea" ON "history_new" ("title");
CREATE INDEX IF NOT EXISTS "idx_history_artist_f58209" ON "history_new" ("artist");
CREATE INDEX IF NOT EXISTS "idx_history_source_c6e08f" ON "history_new" ("source");
CREATE INDEX IF NOT EXISTS "idx_history_played__c71bb4" ON "history_new" ("played_at");

INSERT INTO "history_new" ("id", "title", "artist", "album", "duration", "source", "played_at")
SELECT
    "id",
    CASE
        WHEN (SELECT count(*) FROM pragma_table_info('history') WHERE name = 'title') > 0 THEN "title"
        ELSE "song_title"
    END,
    CASE
        WHEN (SELECT count(*) FROM pragma_table_info('history') WHERE name = 'artist') > 0 THEN "artist"
        ELSE "song_artist"
    END,
    'YouTube Audio',
    0,
    "source",
    "played_at"
FROM "history";

DROP TABLE IF EXISTS "history";
ALTER TABLE "history_new" RENAME TO "history";
"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "history";
"""
