import os

# Garante que os testes não tentem falar com Redis/Kafka reais
for _var in ("REDIS_URL", "KAFKA_BOOTSTRAP_SERVERS"):
    os.environ.pop(_var, None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def raw_pikachu() -> dict:
    """Recorte do JSON real de GET https://pokeapi.co/api/v2/pokemon/25"""
    return {
        "name": "pikachu",
        "id": 25,
        "height": 4,
        "weight": 60,
        "types": [{"slot": 1, "type": {"name": "electric"}}],
        "sprites": {
            "front_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png",
            "back_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/25.png",
        },
    }
