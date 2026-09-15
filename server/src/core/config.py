"""Configuration applicative, chargee depuis l'environnement."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parametres de l'application."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Timesheet API"
    environment: str = "development"
    debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://timesheet:timesheet@localhost:5433/timesheet"
    )

    # Microsoft Entra ID
    entra_tenant_id: str = ""
    entra_client_id: str = ""
    entra_audience: str = ""

    # Origines autorisees pour le BFF Next.js
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """Retourne les parametres, mis en cache pour toute la duree du process."""
    return Settings()
