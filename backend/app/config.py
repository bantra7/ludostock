"""Application settings for the FastAPI backend."""

import json
import os
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import NoDecode


ENV_PATH = os.environ.get("ENV_PATH", ".env")


class Settings(BaseSettings):
    """Load backend settings from the selected environment file."""

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    sqlite_path: str = "backend/app/ludostock.db"
    sqlite_gcs_bucket: str = ""
    sqlite_gcs_object: str = ""
    allow_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    auth_service_url: str = "http://localhost:3001"
    auth_internal_secret: str = ""
    auth_service_timeout_seconds: float = 5.0

    @field_validator("allow_origins", mode="before")
    @classmethod
    def parse_allow_origins(cls, value):
        """Accept a JSON array or a comma-separated CORS origin list."""
        if isinstance(value, list):
            return value
        if value is None:
            return ["*"]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return ["*"]
            if stripped.startswith("["):
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value


settings = Settings()


ENVIRONMENT = settings.environment
SQLITE_PATH = settings.sqlite_path
SQLITE_GCS_BUCKET = settings.sqlite_gcs_bucket
SQLITE_GCS_OBJECT = settings.sqlite_gcs_object
ALLOW_ORIGINS = settings.allow_origins
AUTH_SERVICE_URL = settings.auth_service_url
AUTH_INTERNAL_SECRET = settings.auth_internal_secret
AUTH_SERVICE_TIMEOUT_SECONDS = settings.auth_service_timeout_seconds
