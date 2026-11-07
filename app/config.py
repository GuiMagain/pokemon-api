import os
from dataclasses import dataclass


def _normalize_db_url(url: str) -> str:
    """O Render entrega 'postgres://'; o SQLAlchemy exige o dialeto explícito do driver."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


@dataclass(frozen=True)
class Settings:
    database_url: str = _normalize_db_url(os.getenv("DATABASE_URL", "sqlite:///./pokemon.db"))
    pokeapi_base_url: str = os.getenv("POKEAPI_BASE_URL", "https://pokeapi.co/api/v2")
    redis_url: str | None = os.getenv("REDIS_URL") or None
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))
    kafka_bootstrap: str | None = os.getenv("KAFKA_BOOTSTRAP_SERVERS") or None
    celery_broker: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    celery_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    default_limit: int = 20
    max_limit: int = 100


settings = Settings()
