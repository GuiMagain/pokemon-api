from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.orm import PokemonRecord
from app.models.schemas import Pagination, PokemonCreate, PokemonRegistro, PokemonUpdate, RegistroList

router = APIRouter(prefix="/registros", tags=["registros (CRUD)"])

CAMPOS_OBRIGATORIOS = {"name", "height", "weight", "types"}
NOME_DUPLICADO = "Já existe um pokémon com esse nome"


def _buscar_ou_404(db: Session, registro_id: int) -> PokemonRecord:
    record = db.get(PokemonRecord, registro_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return record


@router.post(
    "",
    response_model=PokemonRegistro,
    status_code=status.HTTP_201_CREATED,
    summary="Criar registro",
    responses={
        409: {"description": "Nome já existe", "content": {"application/json": {"example": {"detail": "Já existe um pokémon com esse nome"}}}},
    },
)
def criar_registro(payload: PokemonCreate, db: Session = Depends(get_db)) -> PokemonRecord:
    dados = payload.model_dump()
    dados["name"] = dados["name"].strip().lower()
    record = PokemonRecord(**dados)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=NOME_DUPLICADO)
    db.refresh(record)
    return record


@router.get("", response_model=RegistroList, summary="Listar registros (paginado)")
def listar_registros(
    limit: int = Query(settings.default_limit, ge=1, le=settings.max_limit),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> RegistroList:
    total = db.scalar(select(func.count()).select_from(PokemonRecord)) or 0
    rows = db.scalars(
        select(PokemonRecord).order_by(PokemonRecord.id).limit(limit).offset(offset)
    ).all()

    next_link = f"/registros?limit={limit}&offset={offset + limit}" if offset + limit < total else None
    prev_link = f"/registros?limit={limit}&offset={max(0, offset - limit)}" if offset > 0 else None
    return RegistroList(
        data=rows,
        pagination=Pagination(total=total, limit=limit, offset=offset, next=next_link, previous=prev_link),
    )


@router.get("/{registro_id}", response_model=PokemonRegistro, summary="Buscar registro por id")
def buscar_registro(registro_id: int, db: Session = Depends(get_db)) -> PokemonRecord:
    return _buscar_ou_404(db, registro_id)


@router.put(
    "/{registro_id}",
    response_model=PokemonRegistro,
    summary="Atualizar registro (parcial)",
    responses={
        404: {"description": "Registro não encontrado", "content": {"application/json": {"example": {"detail": "Registro não encontrado"}}}},
        409: {"description": "Nome já usado por outro registro", "content": {"application/json": {"example": {"detail": "Já existe um pokémon com esse nome"}}}},
    },
)
def atualizar_registro(
    registro_id: int, payload: PokemonUpdate, db: Session = Depends(get_db)
) -> PokemonRecord:
    record = _buscar_ou_404(db, registro_id)
    # envia só o que veio no corpo; null em campo obrigatório é ignorado
    alteracoes = {
        k: v
        for k, v in payload.model_dump(exclude_unset=True).items()
        if not (v is None and k in CAMPOS_OBRIGATORIOS)
    }
    if "name" in alteracoes:
        alteracoes["name"] = alteracoes["name"].strip().lower()
    for campo, valor in alteracoes.items():
        setattr(record, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=NOME_DUPLICADO)
    db.refresh(record)
    return record


@router.delete("/{registro_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir registro")
def excluir_registro(registro_id: int, db: Session = Depends(get_db)) -> Response:
    record = _buscar_ou_404(db, registro_id)
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
