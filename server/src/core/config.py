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

    app_name: str = "Ganesh API"
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
    # Le compte que la porte ouverte remet, en developpement. Deux publics
    # lisent l'application — l'equipe, et qui vient seulement demander — et
    # passer de l'un a l'autre doit tenir dans cette ligne, jamais dans un
    # role reecrit en base. Sans effet des que REQUIRE_AUTH est vrai.
    dev_email: str = "j.buget@waat.fr"

    # La porte de secours, le temps qu'Entra declare l'application. Entra
    # eteint, un seul compte entre, avec le mot de passe donne ici. Sans mot
    # de passe, la porte reste close : on n'ouvre pas a qui laisse le champ
    # vide.
    auth_entra: bool = True
    auth_login: str = ""
    auth_password: str = ""
    auth_local_email: str = "j.buget@waat.fr"
    # Signe les jetons de cette porte. Propre a chaque environnement : une
    # clef partagee laisserait forger une session ailleurs.
    secret_key: str = ""

    # La Gazette's chapeau. Without a key nothing breaks: numéros go out on
    # their facts alone, which is what they are made of.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    # Where the files a mission carries are put down. In production the
    # instance carries an IAM role and the two keys stay empty; on a laptop
    # `s3_endpoint_url` points at the MinIO of docker-compose, which answers
    # the same API. One adapter, two addresses.
    s3_bucket: str = "ganesh-attachments"
    s3_region: str = "eu-west-3"
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    # What a whole request may weigh, envelope included. A guard rail, not a
    # business rule: what a *file* may weigh is the domain's business and
    # lives in the entity, at ten megabytes. This is the margin around it —
    # the multipart wrapper, and the JSON of a bulk import. Caddy is told the
    # same number, and it is Caddy that actually keeps the bytes off the host.
    max_request_bytes: int = 12 * 1024 * 1024

    # How often one API key may call, as a token bucket. Counted per process:
    # behind several workers the effective allowance is multiplied by their
    # number. Generous on purpose — this is a guard rail against a runaway
    # client or a leaked key, not a quota anyone should feel.
    api_key_rate_allowance: int = 120
    api_key_rate_window_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    """Returns the settings, cached for the lifetime of the process."""
    return Settings()
