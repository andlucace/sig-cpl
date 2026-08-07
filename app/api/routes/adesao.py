import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_GESTAO, verificar_papel
from app.db.session import get_db
from app.models.adesao import SolicitacaoAdesao
from app.models.cpl import CPL
from app.models.usuario import Usuario
from app.schemas.adesao import SolicitacaoAdesaoAnalise, SolicitacaoAdesaoCreate, SolicitacaoAdesaoRead
from app.services.adesao import (
    SolicitacaoInvalida,
    aprovar_solicitacao,
    criar_solicitacao,
    rejeitar_solicitacao,
)

router = APIRouter(tags=["Adesão de membro (F01)"])
cpl_router = APIRouter(prefix="/cpls", tags=["Adesão de membro (F01)"])


@cpl_router.post(
    "/{cpl_id}/solicitacoes-adesao",
    response_model=SolicitacaoAdesaoRead,
    status_code=status.HTTP_201_CREATED,
)
def solicitar_adesao(cpl_id: uuid.UUID, dados: SolicitacaoAdesaoCreate, db: Session = Depends(get_db)):
    """F01: rota pública — sem autenticação nenhuma, é justamente a porta
    de entrada de quem ainda não tem vínculo com o sistema."""

    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    try:
        return criar_solicitacao(db, cpl_id, dados)
    except SolicitacaoInvalida as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@cpl_router.get("/{cpl_id}/solicitacoes-adesao", response_model=list[SolicitacaoAdesaoRead])
def listar_solicitacoes_adesao(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[SolicitacaoAdesao]:
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)
    return (
        db.query(SolicitacaoAdesao)
        .filter(SolicitacaoAdesao.cpl_id == cpl_id)
        .order_by(SolicitacaoAdesao.created_at.desc())
        .all()
    )


def _obter_solicitacao_com_permissao(
    db: Session, solicitacao_id: uuid.UUID, usuario_atual: Usuario
) -> SolicitacaoAdesao:
    solicitacao = db.get(SolicitacaoAdesao, solicitacao_id)
    if solicitacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Solicitação de adesão não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=solicitacao.cpl_id)
    return solicitacao


@router.post("/solicitacoes-adesao/{solicitacao_id}/aprovar", response_model=SolicitacaoAdesaoRead)
def aprovar(
    solicitacao_id: uuid.UUID,
    dados: SolicitacaoAdesaoAnalise,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    solicitacao = _obter_solicitacao_com_permissao(db, solicitacao_id, usuario_atual)
    try:
        return aprovar_solicitacao(db, solicitacao, usuario_atual.id, dados.parecer)
    except SolicitacaoInvalida as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.post("/solicitacoes-adesao/{solicitacao_id}/rejeitar", response_model=SolicitacaoAdesaoRead)
def rejeitar(
    solicitacao_id: uuid.UUID,
    dados: SolicitacaoAdesaoAnalise,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    solicitacao = _obter_solicitacao_com_permissao(db, solicitacao_id, usuario_atual)
    try:
        return rejeitar_solicitacao(db, solicitacao, usuario_atual.id, dados.parecer)
    except SolicitacaoInvalida as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
