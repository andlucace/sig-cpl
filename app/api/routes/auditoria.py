import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_IMPEDIMENTO_LEITURA, verificar_papel
from app.db.session import get_db
from app.models.auditoria import RegistroAuditoria
from app.models.cpl import CPL
from app.models.enums import AcaoAuditoria
from app.models.usuario import Usuario
from app.schemas.auditoria import RegistroAuditoriaRead

router = APIRouter(prefix="/auditoria", tags=["Auditoria"])

LIMITE_PADRAO = 200


@router.get("/cpls/{cpl_id}", response_model=list[RegistroAuditoriaRead])
def listar_registros(
    cpl_id: uuid.UUID,
    acao: AcaoAuditoria | None = None,
    entidade_tipo: str | None = None,
    limite: int = LIMITE_PADRAO,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[RegistroAuditoria]:
    """RF-056/RNF-003: trilha de auditoria de uma CPL — leitura restrita a
    gestão e auditoria/controle (RN-014-like: dado sensível)."""

    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_IMPEDIMENTO_LEITURA, cpl_id=cpl_id)

    query = db.query(RegistroAuditoria).filter(RegistroAuditoria.cpl_id == cpl_id)
    if acao is not None:
        query = query.filter(RegistroAuditoria.acao == acao)
    if entidade_tipo:
        query = query.filter(RegistroAuditoria.entidade_tipo == entidade_tipo)
    return (
        query.order_by(RegistroAuditoria.created_at.desc())
        .limit(min(limite, 1000))
        .all()
    )


@router.get("/{registro_id}", response_model=RegistroAuditoriaRead)
def obter_registro(
    registro_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> RegistroAuditoria:
    registro = db.get(RegistroAuditoria, registro_id)
    if registro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro de auditoria não encontrado.")
    verificar_papel(db, usuario_atual, PAPEIS_IMPEDIMENTO_LEITURA, cpl_id=registro.cpl_id)
    return registro
