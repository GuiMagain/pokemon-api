import os

for _var in ("REDIS_URL", "KAFKA_BOOTSTRAP_SERVERS"):
    os.environ.pop(_var, None)
# Os testes não usam o banco real: o app sobe em memória e o CRUD usa engine próprio
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models.orm  # noqa: E402,F401  registra as tabelas
from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_client():
    """Cliente com banco SQLite em memória, novo para cada teste."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


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
