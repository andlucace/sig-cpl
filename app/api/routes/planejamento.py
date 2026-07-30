import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import (
    PAPEIS_GESTAO,
    PAPEIS_GOVERNANCA_LEITURA,
    PAPEIS_GOVERNANCA_PARTICIPACAO,
    PAPEIS_TAREFA_EXECUCAO,
    verificar_papel,
)
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.planejamento import (
    DiagnosticoItem,
    IndicadorEstrategico,
    IniciativaEstrategica,
    MetaEstrategica,
    ObjetivoEstrategico,
    PlanejamentoEstrategico,
)
from app.models.usuario import Usuario
from app.schemas.planejamento import (
    DiagnosticoItemCreate,
    DiagnosticoItemRead,
    IndicadorEstrategicoCreate,
    IndicadorEstrategicoRead,
    IndicadorValorUpdate,
    IniciativaEstrategicaCreate,
    IniciativaEstrategicaRead,
    IniciativaStatusUpdate,
    MetaEstrategicaCreate,
    MetaEstrategicaRead,
    MetaStatusUpdate,
    ObjetivoEstrategicoCreate,
    ObjetivoEstrategicoRead,
    ObjetivoStatusUpdate,
    PlanejamentoEstrategicoCreate,
    PlanejamentoEstrategicoRead,
    PlanejamentoStatusUpdate,
)

router = APIRouter(prefix="/planejamento", tags=["Estratégia e maturidade"])


def _get_cpl_or_404(db: Session, cpl_id: uuid.UUID) -> CPL:
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    return cpl


def _get_planejamento_or_404(db: Session, planejamento_id: uuid.UUID) -> PlanejamentoEstrategico:
    planejamento = db.get(PlanejamentoEstrategico, planejamento_id)
    if planejamento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento estratégico não encontrado.")
    return planejamento


def _get_objetivo_or_404(db: Session, objetivo_id: uuid.UUID) -> ObjetivoEstrategico:
    objetivo = db.get(ObjetivoEstrategico, objetivo_id)
    if objetivo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Objetivo estratégico não encontrado.")
    return objetivo


def _pode_executar(usuario: Usuario, responsavel_id: uuid.UUID | None) -> bool:
    return usuario.pessoa_id is not None and usuario.pessoa_id == responsavel_id


# --- Planejamento Estratégico (RF-021) --------------------------------------


@router.post(
    "/cpls/{cpl_id}/planejamentos",
    response_model=PlanejamentoEstrategicoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_planejamento(
    cpl_id: uuid.UUID,
    dados: PlanejamentoEstrategicoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> PlanejamentoEstrategico:
    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)
    planejamento = PlanejamentoEstrategico(cpl_id=cpl_id, **dados.model_dump())
    db.add(planejamento)
    db.commit()
    db.refresh(planejamento)
    return planejamento


@router.get("/cpls/{cpl_id}/planejamentos", response_model=list[PlanejamentoEstrategicoRead])
def listar_planejamentos(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[PlanejamentoEstrategico]:
    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return (
        db.query(PlanejamentoEstrategico)
        .filter(PlanejamentoEstrategico.cpl_id == cpl_id)
        .order_by(PlanejamentoEstrategico.ciclo.desc())
        .all()
    )


@router.get("/planejamentos/{planejamento_id}", response_model=PlanejamentoEstrategicoRead)
def obter_planejamento(
    planejamento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> PlanejamentoEstrategico:
    planejamento = _get_planejamento_or_404(db, planejamento_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=planejamento.cpl_id)
    return planejamento


@router.patch("/planejamentos/{planejamento_id}", response_model=PlanejamentoEstrategicoRead)
def atualizar_status_planejamento(
    planejamento_id: uuid.UUID,
    dados: PlanejamentoStatusUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> PlanejamentoEstrategico:
    planejamento = _get_planejamento_or_404(db, planejamento_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=planejamento.cpl_id)
    for campo, valor in dados.model_dump().items():
        setattr(planejamento, campo, valor)
    db.commit()
    db.refresh(planejamento)
    return planejamento


# --- Diagnóstico (RF-022) ---------------------------------------------------


@router.post(
    "/planejamentos/{planejamento_id}/diagnosticos",
    response_model=DiagnosticoItemRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_diagnostico(
    planejamento_id: uuid.UUID,
    dados: DiagnosticoItemCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> DiagnosticoItem:
    planejamento = _get_planejamento_or_404(db, planejamento_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_PARTICIPACAO, cpl_id=planejamento.cpl_id)
    item = DiagnosticoItem(planejamento_id=planejamento_id, **dados.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/planejamentos/{planejamento_id}/diagnosticos", response_model=list[DiagnosticoItemRead])
def listar_diagnosticos(
    planejamento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[DiagnosticoItem]:
    planejamento = _get_planejamento_or_404(db, planejamento_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=planejamento.cpl_id)
    return db.query(DiagnosticoItem).filter(DiagnosticoItem.planejamento_id == planejamento_id).all()


# --- Objetivos (RF-023) ------------------------------------------------------


@router.post(
    "/planejamentos/{planejamento_id}/objetivos",
    response_model=ObjetivoEstrategicoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_objetivo(
    planejamento_id: uuid.UUID,
    dados: ObjetivoEstrategicoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> ObjetivoEstrategico:
    planejamento = _get_planejamento_or_404(db, planejamento_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=planejamento.cpl_id)
    objetivo = ObjetivoEstrategico(planejamento_id=planejamento_id, **dados.model_dump())
    db.add(objetivo)
    db.commit()
    db.refresh(objetivo)
    return objetivo


@router.get("/planejamentos/{planejamento_id}/objetivos", response_model=list[ObjetivoEstrategicoRead])
def listar_objetivos(
    planejamento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[ObjetivoEstrategico]:
    planejamento = _get_planejamento_or_404(db, planejamento_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=planejamento.cpl_id)
    return db.query(ObjetivoEstrategico).filter(ObjetivoEstrategico.planejamento_id == planejamento_id).all()


@router.get("/objetivos/{objetivo_id}", response_model=ObjetivoEstrategicoRead)
def obter_objetivo(
    objetivo_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> ObjetivoEstrategico:
    objetivo = _get_objetivo_or_404(db, objetivo_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=objetivo.planejamento.cpl_id)
    return objetivo


@router.patch("/objetivos/{objetivo_id}", response_model=ObjetivoEstrategicoRead)
def atualizar_status_objetivo(
    objetivo_id: uuid.UUID,
    dados: ObjetivoStatusUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> ObjetivoEstrategico:
    objetivo = _get_objetivo_or_404(db, objetivo_id)
    if not _pode_executar(usuario_atual, objetivo.responsavel_id):
        verificar_papel(db, usuario_atual, PAPEIS_TAREFA_EXECUCAO, cpl_id=objetivo.planejamento.cpl_id)
    objetivo.status = dados.status
    db.commit()
    db.refresh(objetivo)
    return objetivo


# --- Metas (RF-023/RN-010) ---------------------------------------------------


@router.post(
    "/objetivos/{objetivo_id}/metas", response_model=MetaEstrategicaRead, status_code=status.HTTP_201_CREATED
)
def criar_meta(
    objetivo_id: uuid.UUID,
    dados: MetaEstrategicaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> MetaEstrategica:
    objetivo = _get_objetivo_or_404(db, objetivo_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=objetivo.planejamento.cpl_id)
    meta = MetaEstrategica(objetivo_id=objetivo_id, **dados.model_dump())
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta


@router.get("/objetivos/{objetivo_id}/metas", response_model=list[MetaEstrategicaRead])
def listar_metas(
    objetivo_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[MetaEstrategica]:
    objetivo = _get_objetivo_or_404(db, objetivo_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=objetivo.planejamento.cpl_id)
    return db.query(MetaEstrategica).filter(MetaEstrategica.objetivo_id == objetivo_id).all()


@router.patch("/metas/{meta_id}", response_model=MetaEstrategicaRead)
def atualizar_status_meta(
    meta_id: uuid.UUID,
    dados: MetaStatusUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> MetaEstrategica:
    meta = db.get(MetaEstrategica, meta_id)
    if meta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Meta não encontrada.")
    if not _pode_executar(usuario_atual, meta.responsavel_id):
        verificar_papel(db, usuario_atual, PAPEIS_TAREFA_EXECUCAO, cpl_id=meta.objetivo.planejamento.cpl_id)
    for campo, valor in dados.model_dump().items():
        setattr(meta, campo, valor)
    db.commit()
    db.refresh(meta)
    return meta


# --- Iniciativas (RF-023) ----------------------------------------------------


@router.post(
    "/objetivos/{objetivo_id}/iniciativas",
    response_model=IniciativaEstrategicaRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_iniciativa(
    objetivo_id: uuid.UUID,
    dados: IniciativaEstrategicaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> IniciativaEstrategica:
    objetivo = _get_objetivo_or_404(db, objetivo_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=objetivo.planejamento.cpl_id)
    iniciativa = IniciativaEstrategica(objetivo_id=objetivo_id, **dados.model_dump())
    db.add(iniciativa)
    db.commit()
    db.refresh(iniciativa)
    return iniciativa


@router.get("/objetivos/{objetivo_id}/iniciativas", response_model=list[IniciativaEstrategicaRead])
def listar_iniciativas(
    objetivo_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[IniciativaEstrategica]:
    objetivo = _get_objetivo_or_404(db, objetivo_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=objetivo.planejamento.cpl_id)
    return db.query(IniciativaEstrategica).filter(IniciativaEstrategica.objetivo_id == objetivo_id).all()


@router.patch("/iniciativas/{iniciativa_id}", response_model=IniciativaEstrategicaRead)
def atualizar_status_iniciativa(
    iniciativa_id: uuid.UUID,
    dados: IniciativaStatusUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> IniciativaEstrategica:
    iniciativa = db.get(IniciativaEstrategica, iniciativa_id)
    if iniciativa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Iniciativa não encontrada.")
    if not _pode_executar(usuario_atual, iniciativa.responsavel_id):
        verificar_papel(
            db, usuario_atual, PAPEIS_TAREFA_EXECUCAO, cpl_id=iniciativa.objetivo.planejamento.cpl_id
        )
    iniciativa.status = dados.status
    db.commit()
    db.refresh(iniciativa)
    return iniciativa


# --- Indicadores (RF-023) ----------------------------------------------------


@router.post(
    "/objetivos/{objetivo_id}/indicadores",
    response_model=IndicadorEstrategicoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_indicador(
    objetivo_id: uuid.UUID,
    dados: IndicadorEstrategicoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> IndicadorEstrategico:
    objetivo = _get_objetivo_or_404(db, objetivo_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=objetivo.planejamento.cpl_id)
    indicador = IndicadorEstrategico(objetivo_id=objetivo_id, **dados.model_dump())
    db.add(indicador)
    db.commit()
    db.refresh(indicador)
    return indicador


@router.get("/objetivos/{objetivo_id}/indicadores", response_model=list[IndicadorEstrategicoRead])
def listar_indicadores(
    objetivo_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[IndicadorEstrategico]:
    objetivo = _get_objetivo_or_404(db, objetivo_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=objetivo.planejamento.cpl_id)
    return db.query(IndicadorEstrategico).filter(IndicadorEstrategico.objetivo_id == objetivo_id).all()


@router.patch("/indicadores/{indicador_id}", response_model=IndicadorEstrategicoRead)
def atualizar_valor_indicador(
    indicador_id: uuid.UUID,
    dados: IndicadorValorUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> IndicadorEstrategico:
    indicador = db.get(IndicadorEstrategico, indicador_id)
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador não encontrado.")
    verificar_papel(
        db, usuario_atual, PAPEIS_TAREFA_EXECUCAO, cpl_id=indicador.objetivo.planejamento.cpl_id
    )
    indicador.valor_atual = dados.valor_atual
    db.commit()
    db.refresh(indicador)
    return indicador
