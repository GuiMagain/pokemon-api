import asyncio
from collections.abc import Iterable

import httpx

from app.config import settings
from app.models.schemas import PokemonDetail, Sprites
from app.services import cache

CHUNK_SIZE = 20


class PokeAPIError(Exception):
    """Falha ao consumir a PokeAPI (rede, timeout, erro 5xx)."""


class PokemonNotFound(Exception):
    """Pokémon inexistente na PokeAPI."""


def _to_detail(raw: dict) -> PokemonDetail:
    """Converte o JSON cru da PokeAPI no formato que a nossa API devolve."""
    sprites = raw.get("sprites") or {}
    return PokemonDetail(
        name=raw["name"],
        id=raw["id"],
        height=raw["height"],
        weight=raw["weight"],
        types=[t["type"]["name"] for t in raw["types"]],
        sprites=Sprites(
            front_default=sprites.get("front_default"),
            back_default=sprites.get("back_default"),
        ),
    )


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=settings.pokeapi_base_url, timeout=10.0)


async def _fetch_detail(client: httpx.AsyncClient, ident: str) -> PokemonDetail:
    key = f"pokemon:{ident}"
    cached = await cache.get_json(key)
    if cached is not None:
        return PokemonDetail(**cached)

    try:
        response = await client.get(f"/pokemon/{ident}")
    except httpx.HTTPError as exc:
        raise PokeAPIError(str(exc)) from exc
    if response.status_code == 404:
        raise PokemonNotFound(ident)
    if response.status_code >= 400:
        raise PokeAPIError(f"PokeAPI respondeu {response.status_code}")

    detail = _to_detail(response.json())
    await cache.set_json(key, detail.model_dump(), settings.cache_ttl)
    return detail


async def list_pokemons(limit: int, offset: int) -> tuple[int, list[PokemonDetail]]:
    async with _client() as client:
        try:
            response = await client.get("/pokemon", params={"limit": limit, "offset": offset})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PokeAPIError(str(exc)) from exc

        payload = response.json()
        # a PokeAPI devolve só nome e URL; o id é o último segmento da URL
        idents = [item["url"].rstrip("/").split("/")[-1] for item in payload["results"]]
        details = await asyncio.gather(*(_fetch_detail(client, i) for i in idents))
    return payload["count"], list(details)


async def get_pokemon(ident: str) -> PokemonDetail:
    async with _client() as client:
        return await _fetch_detail(client, ident)


async def prefetch(ids: Iterable[int]) -> int:
    """Aquece o cache. Chamado pelo worker Celery."""
    ids = list(ids)
    async with _client() as client:
        for i in range(0, len(ids), CHUNK_SIZE):
            chunk = ids[i : i + CHUNK_SIZE]
            await asyncio.gather(*(_fetch_detail(client, str(p)) for p in chunk))
    return len(ids)
