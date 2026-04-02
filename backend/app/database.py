"""SQLite helpers used by the backend."""

import sqlite3
from pathlib import Path

from .config import SQLITE_PATH


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


def _database_path() -> Path:
    """Return the configured SQLite database path."""
    return Path(SQLITE_PATH)


def init_db() -> None:
    """Create the SQLite database and tables when they are missing."""
    database_path = _database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection configured for dictionary-like row access."""
    init_db()
    connection = sqlite3.connect(_database_path(), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
