import asyncio

import httpx
import pytest

from app.services import pokeapi
from app.services.pokeapi import PokeAPIError, PokemonNotFound


def _mock_pokeapi(monkeypatch, handler):
    """Troca o cliente HTTP real por um que usa o handler fake (sem rede)."""
    def fake_client():
        return httpx.AsyncClient(
            base_url="https://pokeapi.test/api/v2",
            transport=httpx.MockTransport(handler),
        )
    monkeypatch.setattr(pokeapi, "_client", fake_client)


def test_get_pokemon_consome_pokeapi(monkeypatch, raw_pikachu):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v2/pokemon/25"
        return httpx.Response(200, json=raw_pikachu)

    _mock_pokeapi(monkeypatch, handler)
    detail = asyncio.run(pokeapi.get_pokemon("25"))
    assert detail.name == "pikachu"
    assert detail.types == ["electric"]


def test_get_pokemon_404_vira_pokemon_not_found(monkeypatch):
    _mock_pokeapi(monkeypatch, lambda r: httpx.Response(404))
    with pytest.raises(PokemonNotFound):
        asyncio.run(pokeapi.get_pokemon("999999"))


def test_get_pokemon_500_vira_erro_de_upstream(monkeypatch):
    _mock_pokeapi(monkeypatch, lambda r: httpx.Response(500))
    with pytest.raises(PokeAPIError):
        asyncio.run(pokeapi.get_pokemon("25"))


def test_erro_de_rede_vira_erro_de_upstream(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("sem conexão", request=request)

    _mock_pokeapi(monkeypatch, handler)
    with pytest.raises(PokeAPIError):
        asyncio.run(pokeapi.list_pokemons(20, 0))


def test_list_pokemons_monta_detalhes_a_partir_das_urls(monkeypatch, raw_pikachu):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/pokemon":
            assert request.url.params["limit"] == "2"
            return httpx.Response(200, json={
                "count": 1281,
                "results": [
                    {"name": "pikachu", "url": "https://pokeapi.co/api/v2/pokemon/25/"},
                    {"name": "pikachu-2", "url": "https://pokeapi.co/api/v2/pokemon/25/"},
                ],
            })
        return httpx.Response(200, json=raw_pikachu)

    _mock_pokeapi(monkeypatch, handler)
    total, items = asyncio.run(pokeapi.list_pokemons(2, 0))
    assert total == 1281
    assert len(items) == 2
    assert items[0].id == 25


def test_prefetch_aquece_os_ids_pedidos(monkeypatch, raw_pikachu):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        return httpx.Response(200, json=raw_pikachu)

    _mock_pokeapi(monkeypatch, handler)
    assert asyncio.run(pokeapi.prefetch(range(1, 4))) == 3
    assert len(seen) == 3
