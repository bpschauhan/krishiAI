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

    OPENAI_API_KEY: str | None = None
    BHASHINI_API_KEY: str | None = None
    WHATSAPP_TOKEN: str | None = None

    @property
    def is_local(self) -> bool:
        return self.APP_ENV == "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
