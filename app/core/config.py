from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(min_length=1)
    test_database_url: str | None = None
    secret_key: str = Field(min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=15, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)
    cors_origins: list[str] = Field(default_factory=list)
    environment: Literal["dev", "test", "prod"] = "dev"

    @model_validator(mode="after")
    def validar_cors_produccion(self) -> "Settings":
        if self.environment == "prod" and "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS no puede contener * en producción")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]