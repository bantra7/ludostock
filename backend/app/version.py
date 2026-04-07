"""Utilities for reading the shared application version."""

from functools import lru_cache
import os
from pathlib import Path


def _resolve_version_file() -> Path | None:
    """Locate the shared VERSION file by walking up from the backend package."""
    current_file = Path(__file__).resolve()

    for parent in current_file.parents:
        candidate = parent / "VERSION"
        if candidate.is_file():
            return candidate

    return None


@lru_cache(maxsize=1)
def get_app_version() -> str:
    """Return the application version from env, VERSION file, or a safe fallback."""
    app_version = os.getenv("APP_VERSION")
    if app_version:
        return app_version.strip()

    version_file = _resolve_version_file()
    if version_file is not None and version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()

    return "dev"
