import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_EDITAL_GESTAO, PAPEIS_IMPEDIMENTO_LEITURA, verificar_papel
from app.db.session import get_db
from app.models.auditoria import RegistroAuditoria
from app.models.cpl import CPL
from app.models.enums import AcaoAuditoria
from app.models.usuario import Usuario
from app.schemas.auditoria import RegistroAuditoriaRead
from app.services.auditoria import LIMITE_PADRAO, consultar_registros

router = APIRouter(prefix="/auditoria", tags=["Auditoria"])


@router.get("/cpls/{cpl_id}", response_model=list[RegistroAuditoriaRead])
def listar_registros(
    cpl_id: uuid.UUID,
    response: Response,
    acao: AcaoAuditoria | None = None,
    entidade_tipo: str | None = None,
    offset: int = 0,
    limite: int = LIMITE_PADRAO,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[RegistroAuditoria]:
    """RF-056/RNF-003: trilha de auditoria de uma CPL — leitura restrita a
    gestão e auditoria/controle (RN-014-like: dado sensível)."""

    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_IMPEDIMENTO_LEITURA, cpl_id=cpl_id)

    registros, total = consultar_registros(
        db,
        cpl_id=cpl_id,
        acao=acao,
        entidade_tipo=entidade_tipo,
        offset=offset,
        limite=limite,
    )
    response.headers["X-Total-Count"] = str(total)
    return registros


@router.get("/global", response_model=list[RegistroAuditoriaRead])
def listar_registros_globais(
    response: Response,
    acao: AcaoAuditoria | None = None,
    entidade_tipo: str | None = None,
    offset: int = 0,
    limite: int = LIMITE_PADRAO,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[RegistroAuditoria]:
    """RF-056: eventos sem CPL resolvível (login, criação de Usuario/Pessoa/
    CPL em si) — restrito a administrador da plataforma, já que cruza
    dados de todas as CPLs."""

    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO)
    registros, total = consultar_registros(
        db,
        somente_global=True,
        acao=acao,
        entidade_tipo=entidade_tipo,
        offset=offset,
        limite=limite,
    )
    response.headers["X-Total-Count"] = str(total)
    return registros


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
