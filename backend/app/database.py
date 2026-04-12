"""SQLite helpers used by the backend."""

import logging
import sqlite3
import threading
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .config import SQLITE_GCS_BUCKET, SQLITE_GCS_OBJECT, SQLITE_PATH


logger = logging.getLogger("ludostock.backend.sqlite")
_DB_INIT_LOCK = threading.RLock()
_DB_SYNC_LOCK = threading.RLock()
_DB_INITIALIZED = False
_REMOTE_GENERATION: int | None = None
_HAS_UNSYNCED_LOCAL_CHANGES = False


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS editors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS distributors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        username TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        extension_of_id INTEGER,
        creation_year INTEGER,
        min_players INTEGER,
        max_players INTEGER,
        min_age INTEGER,
        duration_minutes INTEGER,
        url TEXT,
        image_url TEXT,
        FOREIGN KEY(extension_of_id) REFERENCES games(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_authors (
        game_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        PRIMARY KEY (game_id, author_id),
        FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
        FOREIGN KEY(author_id) REFERENCES authors(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_artists (
        game_id INTEGER NOT NULL,
        artist_id INTEGER NOT NULL,
        PRIMARY KEY (game_id, artist_id),
        FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
        FOREIGN KEY(artist_id) REFERENCES artists(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_editors (
        game_id INTEGER NOT NULL,
        editor_id INTEGER NOT NULL,
        PRIMARY KEY (game_id, editor_id),
        FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
        FOREIGN KEY(editor_id) REFERENCES editors(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_distributors (
        game_id INTEGER NOT NULL,
        distributor_id INTEGER NOT NULL,
        PRIMARY KEY (game_id, distributor_id),
        FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
        FOREIGN KEY(distributor_id) REFERENCES distributors(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        owner_id TEXT NOT NULL,
        share_token TEXT,
        share_enabled INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS collection_shares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collection_id INTEGER NOT NULL,
        shared_with TEXT NOT NULL,
        permission TEXT NOT NULL,
        UNIQUE (collection_id, shared_with),
        FOREIGN KEY(collection_id) REFERENCES collections(id) ON DELETE CASCADE,
        FOREIGN KEY(shared_with) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        UNIQUE (user_id, name),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS collection_games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collection_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        location_id INTEGER,
        quantity INTEGER DEFAULT 1,
        UNIQUE (collection_id, game_id, location_id),
        FOREIGN KEY(collection_id) REFERENCES collections(id) ON DELETE CASCADE,
        FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
        FOREIGN KEY(location_id) REFERENCES user_locations(id) ON DELETE SET NULL
    )
    """,
)


class SyncedSQLiteConnection(sqlite3.Connection):
    """SQLite connection that republishes a snapshot to GCS after each write commit."""

    def commit(self) -> None:
        """Commit the current transaction and upload the new snapshot when needed."""
        had_transaction = self.in_transaction
        super().commit()
        if had_transaction:
            sync_sqlite_to_gcs(reason="commit")


def _database_path() -> Path:
    """Return the configured SQLite database path."""
    return Path(SQLITE_PATH)


def _sqlite_gcs_sync_enabled() -> bool:
    """Return whether SQLite snapshot sync to Google Cloud Storage is enabled."""
    return bool(SQLITE_GCS_BUCKET and SQLITE_GCS_OBJECT)


def _temporary_database_copy_path(label: str) -> Path:
    """Return a temporary path stored next to the live SQLite file."""
    database_path = _database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        delete=False,
        dir=database_path.parent,
        prefix=f"{database_path.stem}.{label}.",
        suffix=".db",
    ) as handle:
        return Path(handle.name)


def _get_storage_client_and_exceptions():
    """Return the Google Cloud Storage client class and relevant exceptions."""
    from google.api_core.exceptions import NotFound, PreconditionFailed
    from google.cloud import storage

    return storage.Client, NotFound, PreconditionFailed


def _read_blob_generation(blob: Any, not_found_exception: type[Exception]) -> int | None:
    """Return the current GCS object generation when the snapshot exists."""
    try:
        blob.reload()
    except not_found_exception:
        return None

    generation = getattr(blob, "generation", None)
    return int(generation) if generation is not None else None


def _create_database_snapshot(snapshot_path: Path) -> None:
    """Create a consistent copy of the live SQLite database using SQLite backup."""
    source = sqlite3.connect(_database_path(), check_same_thread=False)
    target = sqlite3.connect(snapshot_path, check_same_thread=False)
    try:
        source.backup(target)
        target.commit()
    finally:
        target.close()
        source.close()


def _download_database_from_gcs() -> bool:
    """Download the latest SQLite snapshot from GCS when it exists."""
    global _REMOTE_GENERATION

    if not _sqlite_gcs_sync_enabled():
        return False

    client_class, not_found_exception, _ = _get_storage_client_and_exceptions()
    blob = client_class().bucket(SQLITE_GCS_BUCKET).blob(SQLITE_GCS_OBJECT)
    generation = _read_blob_generation(blob, not_found_exception)
    if generation is None:
        logger.info(
            "sqlite.remote_snapshot_missing bucket=%s object=%s local_path=%s",
            SQLITE_GCS_BUCKET,
            SQLITE_GCS_OBJECT,
            _database_path(),
        )
        return False

    temporary_path = _temporary_database_copy_path("download")
    try:
        blob.download_to_filename(temporary_path)
        temporary_path.replace(_database_path())
    finally:
        temporary_path.unlink(missing_ok=True)

    _REMOTE_GENERATION = generation
    logger.info(
        "sqlite.remote_snapshot_downloaded bucket=%s object=%s generation=%s local_path=%s",
        SQLITE_GCS_BUCKET,
        SQLITE_GCS_OBJECT,
        generation,
        _database_path(),
    )
    return True


def _upload_database_to_gcs(reason: str) -> bool:
    """Upload a consistent SQLite snapshot to GCS using optimistic concurrency."""
    global _REMOTE_GENERATION

    if not _sqlite_gcs_sync_enabled() or not _database_path().exists():
        return False

    client_class, not_found_exception, precondition_failed_exception = _get_storage_client_and_exceptions()
    blob = client_class().bucket(SQLITE_GCS_BUCKET).blob(SQLITE_GCS_OBJECT)
    expected_generation = _REMOTE_GENERATION
    if expected_generation is None:
        expected_generation = _read_blob_generation(blob, not_found_exception)

    temporary_path = _temporary_database_copy_path("upload")
    try:
        _create_database_snapshot(temporary_path)
        blob.upload_from_filename(
            temporary_path,
            if_generation_match=expected_generation if expected_generation is not None else 0,
        )
        _REMOTE_GENERATION = _read_blob_generation(blob, not_found_exception)
    except precondition_failed_exception:
        _REMOTE_GENERATION = _read_blob_generation(blob, not_found_exception)
        logger.error(
            "sqlite.remote_snapshot_conflict reason=%s bucket=%s object=%s local_path=%s expected_generation=%s remote_generation=%s",
            reason,
            SQLITE_GCS_BUCKET,
            SQLITE_GCS_OBJECT,
            _database_path(),
            expected_generation if expected_generation is not None else 0,
            _REMOTE_GENERATION if _REMOTE_GENERATION is not None else "-",
        )
        return False
    finally:
        temporary_path.unlink(missing_ok=True)

    logger.info(
        "sqlite.remote_snapshot_uploaded reason=%s bucket=%s object=%s generation=%s local_path=%s",
        reason,
        SQLITE_GCS_BUCKET,
        SQLITE_GCS_OBJECT,
        _REMOTE_GENERATION if _REMOTE_GENERATION is not None else "-",
        _database_path(),
    )
    return True


def _table_has_column(connection: sqlite3.Connection, table: str, column: str) -> bool:
    """Return whether a SQLite table already exposes a column."""
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _ensure_schema_migrations(connection: sqlite3.Connection) -> None:
    """Apply lightweight SQLite migrations required by newer app versions."""
    if not _table_has_column(connection, "collections", "share_token"):
        connection.execute("ALTER TABLE collections ADD COLUMN share_token TEXT")

    if not _table_has_column(connection, "collections", "share_enabled"):
        connection.execute("ALTER TABLE collections ADD COLUMN share_enabled INTEGER NOT NULL DEFAULT 0")

    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_collections_share_token
        ON collections (share_token)
        WHERE share_token IS NOT NULL
        """
    )


def sync_sqlite_to_gcs(reason: str = "manual") -> bool:
    """Upload the local SQLite file to GCS when snapshot sync is enabled."""
    global _HAS_UNSYNCED_LOCAL_CHANGES

    if not _sqlite_gcs_sync_enabled():
        return False

    with _DB_SYNC_LOCK:
        try:
            synced = _upload_database_to_gcs(reason=reason)
        except Exception:
            _HAS_UNSYNCED_LOCAL_CHANGES = True
            logger.exception(
                "sqlite.remote_snapshot_upload_failed reason=%s bucket=%s object=%s local_path=%s",
                reason,
                SQLITE_GCS_BUCKET,
                SQLITE_GCS_OBJECT,
                _database_path(),
            )
            return False

        _HAS_UNSYNCED_LOCAL_CHANGES = not synced
        return synced


def init_db() -> None:
    """Create the SQLite database, optionally hydrate it from GCS, and apply schema migrations."""
    global _DB_INITIALIZED

    if _DB_INITIALIZED:
        return

    with _DB_INIT_LOCK:
        if _DB_INITIALIZED:
            return

        database_path = _database_path()
        database_path.parent.mkdir(parents=True, exist_ok=True)
        download_failed = False
        downloaded = False

        if _sqlite_gcs_sync_enabled():
            try:
                downloaded = _download_database_from_gcs()
            except Exception:
                download_failed = True
                logger.exception(
                    "sqlite.remote_snapshot_download_failed bucket=%s object=%s local_path=%s",
                    SQLITE_GCS_BUCKET,
                    SQLITE_GCS_OBJECT,
                    database_path,
                )

        with sqlite3.connect(database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            _ensure_schema_migrations(connection)
            connection.commit()

        if _sqlite_gcs_sync_enabled() and not download_failed:
            sync_sqlite_to_gcs(reason="startup" if downloaded else "bootstrap")

        _DB_INITIALIZED = True


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection configured for row access and GCS snapshot sync."""
    init_db()
    connection = sqlite3.connect(
        _database_path(),
        check_same_thread=False,
        factory=SyncedSQLiteConnection,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
