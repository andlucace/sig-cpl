from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_EDITAL_GESTAO, verificar_papel
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.observabilidade import SaudeSistemaRead
from app.services.observabilidade import (
    falhas_recentes,
    metricas_requisicoes,
    verificar_banco,
    verificar_e_alertar,
)

router = APIRouter(prefix="/metricas", tags=["Administração"])


@router.get("", response_model=SaudeSistemaRead)
def metricas(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> SaudeSistemaRead:
    """RNF-012: métricas de requisição (em memória, desde o último
    deploy), status do banco e falhas recentes — dado de operação
    interna do sistema, não de um recurso de negócio, então gated ao
    mesmo grupo que administra a plataforma (`PAPEIS_EDITAL_GESTAO`),
    chamado com `cpl_id=None` já que não há CPL nenhuma envolvida."""

    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)

    settings = get_settings()
    janela = settings.observabilidade_alerta_janela_minutos
    contagem_alerta = verificar_e_alertar(db)
    recentes = falhas_recentes(db, minutos=janela)

    return SaudeSistemaRead(
        banco_ok=verificar_banco(db),
        falhas_recentes=recentes,
        total_falhas_recentes=contagem_alerta,
        janela_minutos=janela,
        alerta_ativo=contagem_alerta >= settings.observabilidade_alerta_limiar_falhas,
        **metricas_requisicoes(),
    )
