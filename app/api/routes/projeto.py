import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_PROJETO_GESTAO, PAPEIS_PROJETO_LEITURA, verificar_papel
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.enums import StatusDemanda
from app.models.projeto import DemandaProjeto, Projeto
from app.models.usuario import Usuario
from app.schemas.projeto import (
    DemandaProjetoCreate,
    DemandaProjetoRead,
    ProjetoCreate,
    ProjetoRead,
    ProjetoUpdate,
)

router = APIRouter(prefix="/projetos", tags=["Projetos"])


def _get_cpl_or_404(db: Session, cpl_id: uuid.UUID) -> CPL:
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    return cpl


def _get_demanda_or_404(db: Session, demanda_id: uuid.UUID) -> DemandaProjeto:
    demanda = db.get(DemandaProjeto, demanda_id)
    if demanda is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demanda de projeto não encontrada.")
    return demanda


def _get_projeto_or_404(db: Session, projeto_id: uuid.UUID) -> Projeto:
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    return projeto


# --- Demandas (RF-031) -------------------------------------------------------


@router.post(
    "/cpls/{cpl_id}/demandas", response_model=DemandaProjetoRead, status_code=status.HTTP_201_CREATED
)
def criar_demanda(
    cpl_id: uuid.UUID,
    dados: DemandaProjetoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> DemandaProjeto:
    """RF-031: registra uma demanda coletiva/oportunidade de projeto,
    antes de virar um `Projeto` formal."""

    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=cpl_id)
    demanda = DemandaProjeto(
        cpl_id=cpl_id,
        registrado_por_id=usuario_atual.id,
        **dados.model_dump(),
    )
    db.add(demanda)
    db.commit()
    db.refresh(demanda)
    return demanda


@router.get("/cpls/{cpl_id}/demandas", response_model=list[DemandaProjetoRead])
def listar_demandas(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[DemandaProjeto]:
    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=cpl_id)
    return (
        db.query(DemandaProjeto)
        .filter(DemandaProjeto.cpl_id == cpl_id)
        .order_by(DemandaProjeto.created_at.desc())
        .all()
    )


@router.get("/demandas/{demanda_id}", response_model=DemandaProjetoRead)
def obter_demanda(
    demanda_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> DemandaProjeto:
    demanda = _get_demanda_or_404(db, demanda_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=demanda.cpl_id)
    return demanda


@router.post(
    "/demandas/{demanda_id}/converter", response_model=ProjetoRead, status_code=status.HTTP_201_CREATED
)
def converter_demanda_em_projeto(
    demanda_id: uuid.UUID,
    dados: ProjetoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Projeto:
    """RF-031/032: converte uma demanda registrada em projeto formal do
    portfólio — a demanda não é apagada, fica com status
    CONVERTIDA_EM_PROJETO e um vínculo 1:1 com o projeto criado."""

    demanda = _get_demanda_or_404(db, demanda_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=demanda.cpl_id)
    if demanda.status == StatusDemanda.CONVERTIDA_EM_PROJETO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Demanda já foi convertida em projeto.")

    projeto = Projeto(cpl_id=demanda.cpl_id, demanda_origem_id=demanda.id, **dados.model_dump())
    demanda.status = StatusDemanda.CONVERTIDA_EM_PROJETO
    db.add(projeto)
    db.commit()
    db.refresh(projeto)
    return projeto


# --- Projetos / portfólio (RF-032) ------------------------------------------


@router.post("/cpls/{cpl_id}/projetos", response_model=ProjetoRead, status_code=status.HTTP_201_CREATED)
def criar_projeto(
    cpl_id: uuid.UUID,
    dados: ProjetoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Projeto:
    """RF-032: cria um projeto direto no portfólio, sem passar por uma
    demanda registrada antes (atalho pra quando já se sabe que é um
    projeto, sem precisar do passo intermediário do RF-031)."""

    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=cpl_id)
    projeto = Projeto(cpl_id=cpl_id, **dados.model_dump())
    db.add(projeto)
    db.commit()
    db.refresh(projeto)
    return projeto


@router.get("/cpls/{cpl_id}/projetos", response_model=list[ProjetoRead])
def listar_projetos(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Projeto]:
    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=cpl_id)
    return db.query(Projeto).filter(Projeto.cpl_id == cpl_id).order_by(Projeto.created_at.desc()).all()


@router.get("/{projeto_id}", response_model=ProjetoRead)
def obter_projeto(
    projeto_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Projeto:
    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=projeto.cpl_id)
    return projeto


@router.patch("/{projeto_id}", response_model=ProjetoRead)
def atualizar_projeto(
    projeto_id: uuid.UUID,
    dados: ProjetoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Projeto:
    """RF-032: atualiza campos de portfólio — estágio, prioridade, eixo,
    responsável, vínculo ao planejamento estratégico."""

    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(projeto, campo, valor)
    db.commit()
    db.refresh(projeto)
    return projeto
