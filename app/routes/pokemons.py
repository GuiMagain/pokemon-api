from fastapi import APIRouter, HTTPException, Query, status

from app.config import settings
from app.models.schemas import Pagination, PokemonDetail, PokemonList
from app.services import events, pokeapi
from app.tasks import warm_cache

router = APIRouter(prefix="/pokemons", tags=["pokemons"])


def _page_link(limit: int, offset: int) -> str:
    return f"/pokemons?limit={limit}&offset={offset}"


@router.get("", response_model=PokemonList, summary="Lista paginada de Pokémons")
async def list_pokemons(
    limit: int = Query(settings.default_limit, ge=1, le=settings.max_limit),
    offset: int = Query(0, ge=0),
) -> PokemonList:
    total, items = await pokeapi.list_pokemons(limit, offset)
    await events.publish("pokemon.queried", {"endpoint": "/pokemons", "limit": limit, "offset": offset})

    next_link = _page_link(limit, offset + limit) if offset + limit < total else None
    prev_link = _page_link(limit, max(0, offset - limit)) if offset > 0 else None
    return PokemonList(
        data=items,
        pagination=Pagination(total=total, limit=limit, offset=offset, next=next_link, previous=prev_link),
    )


@router.get("/{pokemon_id}", response_model=PokemonDetail, summary="Detalhes de um Pokémon")
async def get_pokemon(pokemon_id: int) -> PokemonDetail:
    detail = await pokeapi.get_pokemon(str(pokemon_id))
    await events.publish("pokemon.queried", {"endpoint": "/pokemons/{id}", "id": pokemon_id})
    return detail


@router.post(
    "/warm-cache",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enfileira o aquecimento do cache (processamento assíncrono com Celery)",
)
async def enqueue_warm_cache(
    start: int = Query(1, ge=1),
    end: int = Query(151, ge=1, le=1302),
) -> dict[str, str]:
    if start > end:
        raise HTTPException(status_code=400, detail="'start' não pode ser maior que 'end'")
    task = warm_cache.delay(start, end)
    return {"task_id": task.id, "status": "enqueued"}
