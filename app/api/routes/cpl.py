import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_GOVERNANCA_LEITURA, cpl_ids_visiveis, verificar_papel
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.enums import Papel
from app.models.usuario import Usuario
from app.schemas.cpl import CPLCreate, CPLRead, CPLUpdate

router = APIRouter(prefix="/cpls", tags=["Plataforma e configuração"])


def _cpls_visiveis(db: Session, usuario: Usuario) -> list[CPL]:
    ids = cpl_ids_visiveis(db, usuario)
    if ids is None:
        return db.query(CPL).order_by(CPL.nome).all()
    if not ids:
        return []
    return db.query(CPL).filter(CPL.id.in_(ids)).order_by(CPL.nome).all()


@router.post("", response_model=CPLRead, status_code=status.HTTP_201_CREATED)
def criar_cpl(
    dados: CPLCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> CPL:
    """RF-001: cadastra uma nova CPL, mantendo isolamento lógico de dados
    e parâmetros por CPL (multi-tenant). Restrito a administrador da
    plataforma — criar uma CPL nova é uma ação de nível de plataforma,
    não algo que uma entidade gestora faz sozinha."""

    verificar_papel(db, usuario_atual, {Papel.ADMINISTRADOR_PLATAFORMA})

    if db.query(CPL).filter(CPL.sigla == dados.sigla).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sigla já utilizada por outra CPL.")

    cpl = CPL(**dados.model_dump())
    db.add(cpl)
    db.commit()
    db.refresh(cpl)
    return cpl


@router.get("", response_model=list[CPLRead])
def listar_cpls(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[CPL]:
    """Lista apenas as CPLs às quais o usuário tem algum papel vinculado
    (administrador vê todas)."""

    return _cpls_visiveis(db, usuario_atual)


@router.get("/{cpl_id}", response_model=CPLRead)
def obter_cpl(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> CPL:
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return cpl


@router.patch("/{cpl_id}", response_model=CPLRead)
def atualizar_cpl(
    cpl_id: uuid.UUID,
    dados: CPLUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> CPL:
    """RF-001: edita dados cadastrais da CPL — mesma restrição da criação
    (administrador da plataforma), já que sigla/entidade gestora/status
    ativo são decisões de nível de plataforma, não de quem gere uma CPL
    específica no dia a dia."""

    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario_atual, {Papel.ADMINISTRADOR_PLATAFORMA})

    dados_dict = dados.model_dump(exclude_unset=True)
    nova_sigla = dados_dict.get("sigla")
    if nova_sigla and nova_sigla != cpl.sigla:
        if db.query(CPL).filter(CPL.sigla == nova_sigla, CPL.id != cpl_id).first():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sigla já utilizada por outra CPL.")

    for campo, valor in dados_dict.items():
        setattr(cpl, campo, valor)
    db.commit()
    db.refresh(cpl)
    return cpl
