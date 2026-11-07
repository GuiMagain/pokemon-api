from app.config import _normalize_db_url


def test_normaliza_url_postgres_do_render():
    assert _normalize_db_url("postgres://u:p@host/db") == "postgresql+psycopg://u:p@host/db"


def test_normaliza_postgresql_sem_driver():
    assert _normalize_db_url("postgresql://u:p@host/db") == "postgresql+psycopg://u:p@host/db"


def test_mantem_url_sqlite():
    assert _normalize_db_url("sqlite:///./x.db") == "sqlite:///./x.db"
