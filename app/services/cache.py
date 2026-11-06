import json
import logging
from typing import Any

from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)
_client: Redis | None = None


def _get_client() -> Redis | None:
    global _client
    if not settings.redis_url:
        return None
    if _client is None:
        _client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def get_json(key: str) -> Any | None:
    client = _get_client()
    if client is None:
        return None
    try:
        raw = await client.get(key)
    except Exception:  # Redis fora do ar não deve derrubar a API
        logger.warning("Falha ao ler cache", extra={"key": key}, exc_info=True)
        return None
    return json.loads(raw) if raw else None


async def set_json(key: str, value: Any, ttl: int) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        await client.set(key, json.dumps(value), ex=ttl)
    except Exception:
        logger.warning("Falha ao gravar cache", extra={"key": key}, exc_info=True)


async def close() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
