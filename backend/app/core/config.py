from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "TicketHub API"
    app_version: str = "0.1.0"
    database_url: str = (
        "postgresql+psycopg://tickethub:change-me-for-local-development"
        "@postgres:5432/tickethub"
    )
    jwt_secret_key: str = "replace-this-with-a-long-random-local-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
