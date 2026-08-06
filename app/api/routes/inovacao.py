import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_PROJETO_GESTAO, PAPEIS_PROJETO_LEITURA, verificar_papel
from app.db.session import get_db
from app.models.entidade import Entidade
from app.models.enums import TipoEntidade
from app.models.inovacao import MatchInovacao
from app.models.projeto import DemandaProjeto
from app.models.usuario import Usuario
from app.schemas.entidade import EntidadeRead
from app.schemas.inovacao import MatchInovacaoAtualizar, MatchInovacaoCreate, MatchInovacaoRead
from app.services.inovacao import buscar_competencias

router = APIRouter(prefix="/inovacao", tags=["Matchmaking de inovação (RF-052)"])


def _get_demanda_or_404(db: Session, demanda_id: uuid.UUID) -> DemandaProjeto:
    demanda = db.get(DemandaProjeto, demanda_id)
    if demanda is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demanda não encontrada.")
    return demanda


@router.get("/competencias", response_model=list[EntidadeRead])
def listar_competencias(
    termo: str | None = None,
    tipo: TipoEntidade | None = None,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Entidade]:
    """RF-052: busca de candidatos a competência — universidade, ICT,
    prestador/fornecedor ou ambiente de inovação cujo nome ou oferta
    combine com o termo. Leitura ampla (mesmo grupo de RF-031/032), não
    escopada por CPL — competências de qualquer lugar do ecossistema
    podem suprir uma demanda."""

    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA)
    return buscar_competencias(db, termo=termo, tipos=[tipo] if tipo else None)


@router.post(
    "/demandas/{demanda_id}/matches", response_model=MatchInovacaoRead, status_code=status.HTTP_201_CREATED
)
def sugerir_match(
    demanda_id: uuid.UUID,
    dados: MatchInovacaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> MatchInovacao:
    demanda = _get_demanda_or_404(db, demanda_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=demanda.cpl_id)

    if db.get(Entidade, dados.entidade_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    ja_existe = (
        db.query(MatchInovacao)
        .filter(MatchInovacao.demanda_id == demanda_id, MatchInovacao.entidade_id == dados.entidade_id)
        .first()
    )
    if ja_existe is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Já existe um match sugerido com esta entidade.")

    match = MatchInovacao(
        demanda_id=demanda_id,
        entidade_id=dados.entidade_id,
        oferta_id=dados.oferta_id,
        observacao=dados.observacao,
        sugerido_por_id=usuario_atual.id,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.get("/demandas/{demanda_id}/matches", response_model=list[MatchInovacaoRead])
def listar_matches(
    demanda_id: uuid.UUID, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> list[MatchInovacao]:
    demanda = _get_demanda_or_404(db, demanda_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=demanda.cpl_id)
    return (
        db.query(MatchInovacao)
        .filter(MatchInovacao.demanda_id == demanda_id)
        .order_by(MatchInovacao.created_at.desc())
        .all()
    )


@router.patch("/matches/{match_id}", response_model=MatchInovacaoRead)
def atualizar_match(
    match_id: uuid.UUID,
    dados: MatchInovacaoAtualizar,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> MatchInovacao:
    match = db.get(MatchInovacao, match_id)
    if match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Match não encontrado.")
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=match.demanda.cpl_id)

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(match, campo, valor)
    db.commit()
    db.refresh(match)
    return match
