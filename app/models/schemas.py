from pydantic import BaseModel, ConfigDict, Field


# ---------- Leitura a partir da PokeAPI ----------

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


# ---------- CRUD de registros (banco relacional) ----------

class PokemonBase(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["pikachu"])
    height: int = Field(ge=0, examples=[4])
    weight: int = Field(ge=0, examples=[60])
    types: list[str] = Field(default_factory=list, examples=[["electric"]])
    front_sprite: str | None = Field(default=None, max_length=500)
    back_sprite: str | None = Field(default=None, max_length=500)


class PokemonCreate(PokemonBase):
    pass


class PokemonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    height: int | None = Field(default=None, ge=0)
    weight: int | None = Field(default=None, ge=0)
    types: list[str] | None = None
    front_sprite: str | None = Field(default=None, max_length=500)
    back_sprite: str | None = Field(default=None, max_length=500)


class PokemonRegistro(PokemonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class RegistroList(BaseModel):
    data: list[PokemonRegistro]
    pagination: Pagination
