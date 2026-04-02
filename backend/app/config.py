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
    allow_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])

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
ALLOW_ORIGINS = settings.allow_origins
