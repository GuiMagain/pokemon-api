import logging
import time

from fastapi import Request

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.db import init_db
from app.routes.pokemons import router as pokemons_router
from app.routes.registros import router as registros_router
from app.services import cache, events
from app.services.pokeapi import PokeAPIError, PokemonNotFound
from app.utils.log import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield
    await cache.close()
    await events.close()


app = FastAPI(
    title="API Pokémon",
    version="1.1.0",
    description="CRUD de registros de pokémons em banco relacional e consumo da PokeAPI.",
    lifespan=lifespan,
)
app.include_router(registros_router)
app.include_router(pokemons_router)

request_log = logging.getLogger("app.request")

@app.middleware("http")
async def registrar_requisicoes(request: Request, call_next):
    inicio = time.perf_counter()
    response = await call_next(request)
    if request.url.path != "/health":
        duracao_ms = round((time.perf_counter() - inicio) * 1000, 2)
        request_log.info(
            f"{request.method} {request.url.path} -> {response.status_code} em {duracao_ms} ms"
        )
    return response


@app.exception_handler(PokemonNotFound)
async def not_found_handler(_: Request, exc: PokemonNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"Pokémon '{exc}' não encontrado"})


@app.exception_handler(PokeAPIError)
async def upstream_handler(_: Request, exc: PokeAPIError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": "Falha ao consultar a PokeAPI"})


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
