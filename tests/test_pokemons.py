from app.models.schemas import PokemonDetail, Sprites
from app.services import pokeapi
from app.services.pokeapi import PokeAPIError, PokemonNotFound
from app.tasks import warm_cache


def _detail(id_: int, name: str) -> PokemonDetail:
    return PokemonDetail(
        name=name,
        id=id_,
        height=4,
        weight=60,
        types=["electric"],
        sprites=Sprites(front_default="https://exemplo/front.png", back_default=None),
    )


def test_lista_paginada_com_links(client, monkeypatch):
    async def fake_list(limit, offset):
        return 1281, [_detail(1, "bulbasaur")]

    monkeypatch.setattr(pokeapi, "list_pokemons", fake_list)
    r = client.get("/pokemons", params={"limit": 20, "offset": 0})

    assert r.status_code == 200
    body = r.json()
    assert body["pagination"] == {
        "total": 1281,
        "limit": 20,
        "offset": 0,
        "next": "/pokemons?limit=20&offset=20",
        "previous": None,
    }
    assert body["data"][0]["name"] == "bulbasaur"


def test_links_de_paginacao_no_meio(client, monkeypatch):
    async def fake_list(limit, offset):
        return 100, []

    monkeypatch.setattr(pokeapi, "list_pokemons", fake_list)
    pagination = client.get("/pokemons", params={"limit": 20, "offset": 40}).json()["pagination"]

    assert pagination["previous"] == "/pokemons?limit=20&offset=20"
    assert pagination["next"] == "/pokemons?limit=20&offset=60"


def test_limit_acima_do_maximo_retorna_422(client):
    assert client.get("/pokemons", params={"limit": 500}).status_code == 422


def test_detalhe_de_um_pokemon(client, monkeypatch):
    async def fake_get(ident):
        return _detail(25, "pikachu")

    monkeypatch.setattr(pokeapi, "get_pokemon", fake_get)
    r = client.get("/pokemons/25")

    assert r.status_code == 200
    assert r.json()["name"] == "pikachu"


def test_pokemon_inexistente_retorna_404(client, monkeypatch):
    async def fake_get(ident):
        raise PokemonNotFound(ident)

    monkeypatch.setattr(pokeapi, "get_pokemon", fake_get)
    assert client.get("/pokemons/99999").status_code == 404


def test_falha_na_pokeapi_retorna_502(client, monkeypatch):
    async def fake_list(limit, offset):
        raise PokeAPIError("timeout")

    monkeypatch.setattr(pokeapi, "list_pokemons", fake_list)
    assert client.get("/pokemons").status_code == 502


def test_warm_cache_enfileira_tarefa(client, monkeypatch):
    class FakeResult:
        id = "abc-123"

    calls = {}

    def fake_delay(start, end):
        calls["args"] = (start, end)
        return FakeResult()

    monkeypatch.setattr(warm_cache, "delay", fake_delay)
    r = client.post("/pokemons/warm-cache", params={"start": 1, "end": 151})

    assert r.status_code == 202
    assert r.json() == {"task_id": "abc-123", "status": "enqueued"}
    assert calls["args"] == (1, 151)


def test_warm_cache_com_intervalo_invalido(client):
    assert client.post("/pokemons/warm-cache", params={"start": 10, "end": 5}).status_code == 400


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
