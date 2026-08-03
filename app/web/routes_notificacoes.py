import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.db.session import get_db
from app.models.notificacao import Notificacao
from app.models.usuario import Usuario
from app.services.notificacoes import (
    gerar_notificacoes,
    listar_notificacoes,
    marcar_como_lida,
    marcar_todas_como_lidas,
)
from app.web.templates import templates

router = APIRouter(prefix="/painel/notificacoes", tags=["Área restrita — Notificações"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


@router.get("")
def listar(
    request: Request, db: Session = Depends(get_db), usuario=Depends(get_current_user_optional)
):
    if redir := _exigir_login(usuario):
        return redir
    gerar_notificacoes(db)
    notificacoes = listar_notificacoes(db, usuario.id)
    return templates.TemplateResponse(
        request,
        "restrito/notificacoes/lista.html",
        {"notificacoes": notificacoes, "usuario": usuario, "pagina_ativa": "notificacoes"},
    )


@router.post("/{notificacao_id}/marcar-lida")
def marcar_lida(
    notificacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    notificacao = db.get(Notificacao, notificacao_id)
    if notificacao is None or notificacao.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notificação não encontrada.")
    marcar_como_lida(db, notificacao)
    return RedirectResponse("/painel/notificacoes", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/marcar-todas-lidas")
def marcar_todas_lidas(
    db: Session = Depends(get_db), usuario=Depends(get_current_user_optional)
):
    if redir := _exigir_login(usuario):
        return redir
    marcar_todas_como_lidas(db, usuario.id)
    return RedirectResponse("/painel/notificacoes", status_code=status.HTTP_303_SEE_OTHER)
