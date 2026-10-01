"""Application settings loaded from environment variables, never from source code."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the single-store application."""

    app_env: str = "development"
    database_url: str
    secret_key: str = "development-only-placeholder"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def database_url_uses_the_supported_driver(cls, value: str) -> str:
        """Reject stale PostgreSQL or unqualified MySQL URLs early."""
        if not value.startswith("mysql+pymysql://"):
            raise ValueError("DATABASE_URL must use the mysql+pymysql:// scheme")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached settings without logging sensitive values."""
    return Settings()
