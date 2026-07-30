import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_GESTAO, PAPEIS_GOVERNANCA_LEITURA, verificar_papel
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.entidade import Entidade, EntidadeCPL
from app.models.usuario import Usuario
from app.schemas.entidade import EntidadeCPLRead, EntidadeCreate, EntidadeRead

router = APIRouter(prefix="/entidades", tags=["Cadastro e cadeia"])
cpl_router = APIRouter(prefix="/cpls", tags=["Cadastro e cadeia"])


@router.post("", response_model=EntidadeRead, status_code=status.HTTP_201_CREATED)
def criar_entidade(
    dados: EntidadeCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Entidade:
    """RF-006/RF-008: cadastra empresa, órgão, universidade, ICT, associação,
    prestador ou ambiente de inovação.

    Nota de escopo do RBAC: Entidade ainda não carrega um `cpl_id` próprio
    neste esqueleto (o vínculo é feito à parte via `EntidadeCPL`), então a
    checagem aqui é só por papel, sem escopo de CPL — qualquer usuário com
    papel de gestão em QUALQUER CPL pode cadastrar. Revisitar quando houver
    endpoint para `EntidadeCPL`."""

    verificar_papel(db, usuario_atual, PAPEIS_GESTAO)

    entidade = Entidade(**dados.model_dump())
    db.add(entidade)
    db.commit()
    db.refresh(entidade)
    return entidade


@router.get("", response_model=list[EntidadeRead])
def listar_entidades(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Entidade]:
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA)
    return db.query(Entidade).order_by(Entidade.razao_social).all()


@router.get("/{entidade_id}", response_model=EntidadeRead)
def obter_entidade(
    entidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Entidade:
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA)
    entidade = db.get(Entidade, entidade_id)
    if entidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    return entidade


# --- Vínculo Entidade <-> CPL (RN-003) --------------------------------------


@cpl_router.post(
    "/{cpl_id}/entidades/{entidade_id}/vinculo",
    response_model=EntidadeCPLRead,
    status_code=status.HTTP_201_CREATED,
)
def vincular_entidade_a_cpl(
    cpl_id: uuid.UUID,
    entidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> EntidadeCPL:
    """RN-003: uma organização pode participar de mais de uma CPL; o
    vínculo (não a entidade em si) é escopado por CPL no RBAC."""

    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    if db.get(Entidade, entidade_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)

    vinculo = (
        db.query(EntidadeCPL)
        .filter(EntidadeCPL.cpl_id == cpl_id, EntidadeCPL.entidade_id == entidade_id)
        .first()
    )
    if vinculo is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Entidade já vinculada a esta CPL.")

    vinculo = EntidadeCPL(cpl_id=cpl_id, entidade_id=entidade_id, data_vinculo=date.today())
    db.add(vinculo)
    db.commit()
    db.refresh(vinculo)
    return vinculo


@cpl_router.get("/{cpl_id}/entidades", response_model=list[EntidadeCPLRead])
def listar_entidades_da_cpl(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[EntidadeCPL]:
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return (
        db.query(EntidadeCPL)
        .filter(EntidadeCPL.cpl_id == cpl_id, EntidadeCPL.ativo.is_(True))
        .all()
    )
