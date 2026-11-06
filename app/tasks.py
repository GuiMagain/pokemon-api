import asyncio

from celery import Celery

from app.config import settings
from app.services import cache, pokeapi

celery_app = Celery("pokemon", broker=settings.celery_broker, backend=settings.celery_backend)


@celery_app.task(name="pokemon.warm_cache")
def warm_cache(start: int = 1, end: int = 151) -> int:
    async def _job() -> int:
        try:
            return await pokeapi.prefetch(range(start, end + 1))
        finally:
            await cache.close()  # cada execução usa seu próprio event loop

    return asyncio.run(_job())
