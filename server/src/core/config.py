"""Application settings, loaded from the environment.

Variable names and URL conventions follow WAATcher.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parametres de l'application."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Janus API"
    environment: str = "development"
    debug: bool = False

    api_prefix: str = "/api/v1"
    api_url: str = "http://localhost:8000"
    allowed_origins: list[str] = ["http://localhost:3000"]

    database_url: str = (
        "postgresql+asyncpg://timesheet:timesheet@localhost:5432/timesheet"
    )

    # Microsoft Entra ID (nommage AZURE_AD_*, identique a WAATcher)
    azure_ad_tenant_id: str = ""
    azure_ad_client_id: str = ""
    require_auth: bool = True


@lru_cache
def get_settings() -> Settings:
    """Returns the settings, cached for the lifetime of the process."""
    return Settings()
