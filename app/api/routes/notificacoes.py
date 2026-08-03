import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.notificacao import Notificacao
from app.models.usuario import Usuario
from app.schemas.notificacao import NotificacaoRead
from app.services.notificacoes import (
    contar_nao_lidas,
    gerar_notificacoes,
    listar_notificacoes,
    marcar_como_lida,
    marcar_todas_como_lidas,
)

router = APIRouter(prefix="/notificacoes", tags=["Notificações"])


@router.get("", response_model=list[NotificacaoRead])
def listar(
    somente_nao_lidas: bool = False,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Notificacao]:
    """RF-049: notificações do usuário autenticado — reunião próxima,
    tarefa/meta com prazo vencendo, documento perdendo validade e
    recadastramento de CPL vencendo. Gera as pendentes antes de listar
    (não há agendador; a varredura acontece sob demanda)."""

    gerar_notificacoes(db)
    return listar_notificacoes(db, usuario_atual.id, somente_nao_lidas=somente_nao_lidas)


@router.get("/nao-lidas/contagem")
def contagem_nao_lidas(
    db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> dict:
    gerar_notificacoes(db)
    return {"total": contar_nao_lidas(db, usuario_atual.id)}


@router.post("/{notificacao_id}/marcar-lida", response_model=NotificacaoRead)
def marcar_lida(
    notificacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Notificacao:
    notificacao = db.get(Notificacao, notificacao_id)
    if notificacao is None or notificacao.usuario_id != usuario_atual.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notificação não encontrada.")
    marcar_como_lida(db, notificacao)
    return notificacao


@router.post("/marcar-todas-lidas")
def marcar_todas_lidas(
    db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> dict:
    total = marcar_todas_como_lidas(db, usuario_atual.id)
    return {"atualizadas": total}
