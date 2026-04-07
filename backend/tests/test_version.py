"""Tests for backend version resolution."""

from pathlib import Path

from backend.app import version


def test_get_app_version_uses_environment_variable_when_present(monkeypatch):
    """Prefer the deployment-provided version when available."""
    version.get_app_version.cache_clear()
    monkeypatch.setenv("APP_VERSION", "2.3.4")
    monkeypatch.setattr(version, "_resolve_version_file", lambda: Path("missing"))

    assert version.get_app_version() == "2.3.4"

    version.get_app_version.cache_clear()


def test_get_app_version_returns_dev_when_no_file_exists(monkeypatch):
    """Fallback to a safe default when no version file can be located."""
    version.get_app_version.cache_clear()
    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.setattr(version, "_resolve_version_file", lambda: Path("missing"))

    assert version.get_app_version() == "dev"

    version.get_app_version.cache_clear()
