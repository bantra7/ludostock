from backend.app.config import Settings


def test_settings_defaults_to_sqlite_path():
    settings = Settings.model_construct(sqlite_path="backend/app/ludostock.db")

    assert settings.sqlite_path == "backend/app/ludostock.db"


def test_parse_allow_origins_accepts_csv():
    parsed = Settings.parse_allow_origins("http://localhost:3000,http://127.0.0.1:3000")

    assert parsed == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_settings_accepts_sqlite_gcs_snapshot_location():
    settings = Settings.model_construct(
        sqlite_path="backend/app/ludostock.db",
        sqlite_gcs_bucket="ludostock-data",
        sqlite_gcs_object="ludostock.db",
    )

    assert settings.sqlite_gcs_bucket == "ludostock-data"
    assert settings.sqlite_gcs_object == "ludostock.db"
