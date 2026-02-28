from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    database_url: str = "postgresql+asyncpg://aff:aff@postgres:5432/aff"
    source_discovery_model: str = "gpt-4o-mini"
    source_discovery_max_new_per_topic: int = 5
    source_discovery_max_new_per_domain: int = 3
    event_ingestion_model: str = "gpt-4o-mini"
    event_ingestion_user_agent: str = "AFFEventBot/1.0 (+https://aff.local)"
    event_ingestion_max_pages_per_source: int = 12
    event_ingestion_max_links_per_page: int = 40
    event_ingestion_domain_concurrency: int = 2
    event_ingestion_retry_attempts: int = 3
    event_ingestion_retry_base_seconds: float = 0.5
    event_ingestion_failure_threshold: int = 3
    event_ingestion_past_days_threshold: int = 7
    event_semantic_dedup_threshold: float = 0.92
    event_embedding_model: str = "text-embedding-3-small"
    event_embedding_dimensions: int = 256
    openai_api_key: SecretStr | None = None

    def normalized_database_url(self) -> str:
        normalized = _normalize_database_url(self.database_url)
        if not normalized.startswith("postgresql+asyncpg://"):
            raise ValueError("database_url must target PostgreSQL via asyncpg")
        return normalized


def _normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return "postgresql+asyncpg://" + value[len("postgres://") :]
    if value.startswith("postgresql://"):
        return "postgresql+asyncpg://" + value[len("postgresql://") :]
    return value


settings = Settings()
