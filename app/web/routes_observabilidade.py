from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user_optional
from app.core.rbac import PAPEIS_EDITAL_GESTAO, verificar_papel
from app.db.session import get_db
from app.models.usuario import Usuario
from app.services.observabilidade import (
    falhas_recentes,
    metricas_requisicoes,
    verificar_banco,
    verificar_e_alertar,
)
from app.web.templates import templates

router = APIRouter(prefix="/painel/administracao", tags=["Área restrita — Administração"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


@router.get("/saude")
def painel_saude(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RNF-012: painel de saúde — status do banco, métricas de
    requisição desde o último deploy e falhas recentes, com banner de
    alerta quando a contagem cruza o limiar configurado
    (`observabilidade_alerta_limiar_falhas`). Restrito a
    `PAPEIS_EDITAL_GESTAO` (administrador da plataforma) — mesmo grupo
    que já administra edital/configuração compartilhada, não algo
    escopado a uma CPL."""

    if redir := _exigir_login(usuario):
        return redir
    try:
        verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO)
    except HTTPException:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Painel de saúde restrito ao administrador da plataforma."
        )

    settings = get_settings()
    janela = settings.observabilidade_alerta_janela_minutos
    contagem_alerta = verificar_e_alertar(db)

    return templates.TemplateResponse(
        request,
        "restrito/administracao/saude.html",
        {
            "banco_ok": verificar_banco(db),
            "metricas": metricas_requisicoes(),
            "falhas": falhas_recentes(db, minutos=janela),
            "janela_minutos": janela,
            "limiar_falhas": settings.observabilidade_alerta_limiar_falhas,
            "alerta_ativo": contagem_alerta >= settings.observabilidade_alerta_limiar_falhas,
            "usuario": usuario,
            "pagina_ativa": "saude",
        },
    )
