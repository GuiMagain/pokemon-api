from pydantic import BaseModel


class Sprites(BaseModel):
    front_default: str | None = None
    back_default: str | None = None


class PokemonDetail(BaseModel):
    name: str
    id: int
    height: int
    weight: int
    types: list[str]
    sprites: Sprites


class Pagination(BaseModel):
    total: int
    limit: int
    offset: int
    next: str | None = None
    previous: str | None = None


class PokemonList(BaseModel):
    data: list[PokemonDetail]
    pagination: Pagination
