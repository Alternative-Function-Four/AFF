from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    database_url: str = "sqlite+aiosqlite:///./aff.db"
    source_discovery_model: str = "gpt-4o-mini"
    source_discovery_max_new_per_topic: int = 5
    source_discovery_max_new_per_domain: int = 3
    openai_api_key: SecretStr | None = None

    def normalized_database_url(self) -> str:
        return _normalize_database_url(self.database_url)


def _normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return "postgresql+asyncpg://" + value[len("postgres://") :]
    if value.startswith("postgresql://"):
        return "postgresql+asyncpg://" + value[len("postgresql://") :]
    if value.startswith("sqlite:///"):
        return "sqlite+aiosqlite:///" + value[len("sqlite:///") :]
    return value


settings = Settings()
