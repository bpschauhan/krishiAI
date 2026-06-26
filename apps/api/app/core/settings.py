from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "KrishiAI API"
    SERVICE_NAME: str = "krishiai-api"
    VERSION: str = "0.1.0"
    APP_ENV: Literal["local", "development", "staging", "production"] = "local"

    DATABASE_URL: str = Field(
        default="postgresql+psycopg://krishiai:krishiai_local_password@db:5432/krishiai"
    )
    REDIS_URL: str = "redis://redis:6379/0"

    CLERK_ISSUER_URL: str | None = None
    CLERK_JWKS_URL: str | None = None
    CLERK_JWT_AUDIENCE: str | None = None
    CLERK_DEFAULT_ROLE_SLUG: str = "farmer"
    CSRF_TRUSTED_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    OPENAI_API_KEY: str | None = None
    BHASHINI_API_KEY: str | None = None
    WHATSAPP_TOKEN: str | None = None

    @property
    def is_local(self) -> bool:
        return self.APP_ENV == "local"

    @property
    def clerk_jwks_url(self) -> str | None:
        if self.CLERK_JWKS_URL:
            return self.CLERK_JWKS_URL
        if self.CLERK_ISSUER_URL:
            return f"{self.CLERK_ISSUER_URL.rstrip('/')}/.well-known/jwks.json"
        return None

    @property
    def csrf_trusted_origins(self) -> set[str]:
        return {origin.strip() for origin in self.CSRF_TRUSTED_ORIGINS.split(",") if origin.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
