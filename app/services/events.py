import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

from app.config import settings

logger = logging.getLogger(__name__)
_producer: AIOKafkaProducer | None = None


async def _get_producer() -> AIOKafkaProducer | None:
    global _producer
    if not settings.kafka_bootstrap:
        return None
    if _producer is None:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await producer.start()
        _producer = producer
    return _producer


async def publish(topic: str, payload: dict[str, Any]) -> None:
    """Publica evento no Kafka. Se o Kafka estiver indisponível, só registra o erro."""
    try:
        producer = await _get_producer()
        if producer is not None:
            await producer.send_and_wait(topic, payload)
    except Exception:
        logger.warning("Falha ao publicar evento no Kafka", exc_info=True)


async def close() -> None:
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
