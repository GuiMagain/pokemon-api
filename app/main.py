from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routes.pokemons import router as pokemons_router
from app.services import cache, events
from app.services.pokeapi import PokeAPIError, PokemonNotFound
from app.utils.log import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await cache.close()
    await events.close()


app = FastAPI(
    title="API Pokémon",
    version="1.0.0",
    description="Consome a PokeAPI e expõe dados de Pokémons paginados.",
    lifespan=lifespan,
)
app.include_router(pokemons_router)


@app.exception_handler(PokemonNotFound)
async def not_found_handler(_: Request, exc: PokemonNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"Pokémon '{exc}' não encontrado"})


@app.exception_handler(PokeAPIError)
async def upstream_handler(_: Request, exc: PokeAPIError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": "Falha ao consultar a PokeAPI"})


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
