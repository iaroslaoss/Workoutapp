from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Lift & Move API"
    secret_key: str
    access_token_expire_minutes: int = 60 * 24
    database_url: str
    cors_origins: str = "http://localhost:5173"

    @field_validator("cors_origins")
    @classmethod
    def normalize_cors(cls, value: str) -> str:
        return ",".join([item.strip() for item in value.split(",") if item.strip()])

    @property
    def cors_origins_list(self) -> List[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
