import asyncio

from app.services import cache, events


def test_cache_sem_redis_nao_faz_nada():
    assert asyncio.run(cache.get_json("qualquer-chave")) is None
    asyncio.run(cache.set_json("qualquer-chave", {"a": 1}, ttl=10))


def test_publish_sem_kafka_nao_falha():
    asyncio.run(events.publish("pokemon.queried", {"endpoint": "/pokemons"}))
