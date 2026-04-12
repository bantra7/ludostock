import shutil
import sqlite3
from pathlib import Path

from backend.app import database


class FakeNotFound(Exception):
    """Raised when the fake blob is missing."""


class FakePreconditionFailed(Exception):
    """Raised when the fake blob generation check fails."""


class FakeStorageState:
    """Store the remote blob path and its fake generation number."""

    def __init__(self, remote_path: Path):
        self.remote_path = remote_path
        self.generation = 1 if remote_path.exists() else None


class FakeBlob:
    """Minimal blob implementation used by the database sync tests."""

    def __init__(self, state: FakeStorageState):
        self._state = state
        self.generation = None

    def reload(self):
        """Refresh the blob metadata from the fake remote store."""
        if not self._state.remote_path.exists():
            raise FakeNotFound
        if self._state.generation is None:
            self._state.generation = 1
        self.generation = str(self._state.generation)

    def download_to_filename(self, filename: str | Path):
        """Copy the fake remote object to a local file."""
        self.reload()
        shutil.copyfile(self._state.remote_path, filename)

    def upload_from_filename(self, filename: str | Path, if_generation_match: int | None = None):
        """Copy a local file into the fake remote object with generation guards."""
        exists = self._state.remote_path.exists()
        current_generation = self._state.generation if self._state.generation is not None else (1 if exists else None)
        expected_generation = current_generation if current_generation is not None else 0

        if if_generation_match is not None and if_generation_match != expected_generation:
            raise FakePreconditionFailed

        self._state.remote_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(filename, self._state.remote_path)
        self._state.generation = (current_generation or 0) + 1
        self.generation = str(self._state.generation)


class FakeBucket:
    """Return the same fake blob for the requested object name."""

    def __init__(self, state: FakeStorageState):
        self._state = state

    def blob(self, _name: str) -> FakeBlob:
        """Return the fake blob instance."""
        return FakeBlob(self._state)


class FakeStorageClient:
    """Small fake Google Cloud Storage client used in tests."""

    state: FakeStorageState | None = None

    def __init__(self):
        if self.state is None:
            raise RuntimeError("Fake storage state must be configured before use")

    def bucket(self, _name: str) -> FakeBucket:
        """Return the fake bucket instance."""
        return FakeBucket(self.state)


def configure_fake_storage(monkeypatch, tmp_path: Path, remote_exists: bool):
    """Prepare the database module to use a temp SQLite path and fake GCS client."""
    local_path = tmp_path / "local.db"
    remote_path = tmp_path / "remote" / "ludostock.db"

    if remote_exists:
        remote_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(remote_path) as connection:
            connection.execute("CREATE TABLE authors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)")
            connection.execute("INSERT INTO authors (name) VALUES (?)", ("Remote Author",))
            connection.commit()

    FakeStorageClient.state = FakeStorageState(remote_path)

    monkeypatch.setattr(database, "SQLITE_PATH", str(local_path))
    monkeypatch.setattr(database, "SQLITE_GCS_BUCKET", "ludostock-data")
    monkeypatch.setattr(database, "SQLITE_GCS_OBJECT", "ludostock.db")
    monkeypatch.setattr(database, "_DB_INITIALIZED", False)
    monkeypatch.setattr(database, "_REMOTE_GENERATION", None)
    monkeypatch.setattr(database, "_HAS_UNSYNCED_LOCAL_CHANGES", False)
    monkeypatch.setattr(
        database,
        "_get_storage_client_and_exceptions",
        lambda: (FakeStorageClient, FakeNotFound, FakePreconditionFailed),
    )

    return local_path, remote_path


def test_init_db_downloads_remote_snapshot_before_migrations(tmp_path, monkeypatch):
    local_path, _ = configure_fake_storage(monkeypatch, tmp_path, remote_exists=True)

    database.init_db()

    with sqlite3.connect(local_path) as connection:
        author_name = connection.execute("SELECT name FROM authors").fetchone()[0]

    assert author_name == "Remote Author"


def test_write_commit_uploads_new_snapshot_to_remote_storage(tmp_path, monkeypatch):
    _, remote_path = configure_fake_storage(monkeypatch, tmp_path, remote_exists=False)

    database.init_db()

    with database.get_connection() as connection:
        connection.execute("INSERT INTO authors (name) VALUES (?)", ("Uploaded Author",))
        connection.commit()

    with sqlite3.connect(remote_path) as connection:
        author_name = connection.execute("SELECT name FROM authors").fetchone()[0]

    assert author_name == "Uploaded Author"
