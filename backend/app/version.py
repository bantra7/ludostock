"""Utilities for reading the shared application version."""

from functools import lru_cache
from pathlib import Path


def _resolve_version_file() -> Path:
    """Locate the shared VERSION file by walking up from the backend package."""
    current_file = Path(__file__).resolve()

    for parent in current_file.parents:
        candidate = parent / "VERSION"
        if candidate.is_file():
            return candidate

    raise FileNotFoundError("Unable to locate the shared VERSION file.")


@lru_cache(maxsize=1)
def get_app_version() -> str:
    """Return the shared application version stored in the repository."""
    return _resolve_version_file().read_text(encoding="utf-8").strip()
