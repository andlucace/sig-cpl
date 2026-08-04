import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_EDITAL_GESTAO, PAPEIS_PROJETO_GESTAO, PAPEIS_PROJETO_LEITURA, verificar_papel
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.enums import EstagioProjeto, StatusDemanda
from app.models.projeto import (
    DemandaProjeto,
    EditalFomento,
    EquipeProjeto,
    EtapaProjeto,
    IndicadorProjeto,
    MetaProjeto,
    OrigemRecursoProjeto,
    Projeto,
    RecursoSubmissaoProjeto,
    RiscoProjeto,
)
from app.models.usuario import Usuario
from app.schemas.projeto import (
    DemandaProjetoCreate,
    DemandaProjetoRead,
    EditalFomentoCreate,
    EditalFomentoRead,
    EditalFomentoUpdate,
    EquipeProjetoCreate,
    EquipeProjetoRead,
    EquipeProjetoUpdate,
    EtapaProjetoCreate,
    EtapaProjetoRead,
    EtapaProjetoUpdate,
    IndicadorProjetoCreate,
    IndicadorProjetoRead,
    IndicadorProjetoUpdate,
    MetaProjetoCreate,
    MetaProjetoRead,
    MetaProjetoUpdate,
    OrigemRecursoProjetoCreate,
    OrigemRecursoProjetoRead,
    OrigemRecursoProjetoUpdate,
    ProjetoCreate,
    ProjetoRead,
    ProjetoUpdate,
    RecursoSubmissaoProjetoCreate,
    RecursoSubmissaoProjetoDecisao,
    RecursoSubmissaoProjetoRead,
    RiscoProjetoCreate,
    RiscoProjetoRead,
    RiscoProjetoUpdate,
    SubmissaoProjetoCreate,
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


def _get_etapa_or_404(db: Session, etapa_id: uuid.UUID) -> EtapaProjeto:
    etapa = db.get(EtapaProjeto, etapa_id)
    if etapa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Etapa de projeto não encontrada.")
    return etapa


def _get_meta_or_404(db: Session, meta_id: uuid.UUID) -> MetaProjeto:
    meta = db.get(MetaProjeto, meta_id)
    if meta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Meta de projeto não encontrada.")
    return meta


def _get_indicador_or_404(db: Session, indicador_id: uuid.UUID) -> IndicadorProjeto:
    indicador = db.get(IndicadorProjeto, indicador_id)
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador de projeto não encontrado.")
    return indicador


def _get_risco_or_404(db: Session, risco_id: uuid.UUID) -> RiscoProjeto:
    risco = db.get(RiscoProjeto, risco_id)
    if risco is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Risco de projeto não encontrado.")
    return risco


def _get_membro_equipe_or_404(db: Session, membro_id: uuid.UUID) -> EquipeProjeto:
    membro = db.get(EquipeProjeto, membro_id)
    if membro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Membro de equipe do projeto não encontrado.")
    return membro


def _get_origem_recurso_or_404(db: Session, origem_id: uuid.UUID) -> OrigemRecursoProjeto:
    origem = db.get(OrigemRecursoProjeto, origem_id)
    if origem is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Origem de recurso do projeto não encontrada.")
    return origem


def _get_edital_fomento_or_404(db: Session, edital_id: uuid.UUID) -> EditalFomento:
    edital = db.get(EditalFomento, edital_id)
    if edital is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Edital de fomento não encontrado.")
    return edital


def _get_recurso_submissao_or_404(db: Session, recurso_id: uuid.UUID) -> RecursoSubmissaoProjeto:
    recurso = db.get(RecursoSubmissaoProjeto, recurso_id)
    if recurso is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recurso de submissão não encontrado.")
    return recurso


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


# --- Editais de fomento (RF-029) ---------------------------------------------
# Registrado antes de "Projetos / portfólio" propositalmente: as rotas GET
# aqui (`/editais-fomento`, `/editais-fomento/{edital_id}`) precisam vir
# antes de `GET /{projeto_id}` na tabela de rotas, senão o FastAPI casa
# "editais-fomento" com o path param `projeto_id` primeiro (erro 422 de
# UUID inválido) — rotas são casadas na ordem em que são registradas.


@router.post("/editais-fomento", response_model=EditalFomentoRead, status_code=status.HTTP_201_CREATED)
def criar_edital_fomento(
    dados: EditalFomentoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> EditalFomento:
    """RF-029: edital de fomento — global, não escopado a uma CPL, mesmo
    padrão de `Edital` de maturidade."""

    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    edital = EditalFomento(**dados.model_dump())
    db.add(edital)
    db.commit()
    db.refresh(edital)
    return edital


@router.get("/editais-fomento", response_model=list[EditalFomentoRead])
def listar_editais_fomento(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[EditalFomento]:
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=None)
    return db.query(EditalFomento).order_by(EditalFomento.data_abertura.desc().nullslast()).all()


@router.get("/editais-fomento/{edital_id}", response_model=EditalFomentoRead)
def obter_edital_fomento(
    edital_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> EditalFomento:
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=None)
    return _get_edital_fomento_or_404(db, edital_id)


@router.patch("/editais-fomento/{edital_id}", response_model=EditalFomentoRead)
def atualizar_edital_fomento(
    edital_id: uuid.UUID,
    dados: EditalFomentoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> EditalFomento:
    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    edital = _get_edital_fomento_or_404(db, edital_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(edital, campo, valor)
    db.commit()
    db.refresh(edital)
    return edital


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


# --- Etapas do plano de trabalho (RF-034) -----------------------------------


@router.post(
    "/{projeto_id}/etapas", response_model=EtapaProjetoRead, status_code=status.HTTP_201_CREATED
)
def criar_etapa(
    projeto_id: uuid.UUID,
    dados: EtapaProjetoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> EtapaProjeto:
    """RF-034: etapa (ou atividade — mesmo nível, ver docstring do
    modelo) do plano de trabalho, com cronograma previsto. Entra no
    fim da lista (maior `ordem` + 1)."""

    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    maior_ordem = (
        db.query(EtapaProjeto)
        .filter(EtapaProjeto.projeto_id == projeto_id)
        .count()
    )
    etapa = EtapaProjeto(projeto_id=projeto_id, ordem=maior_ordem, **dados.model_dump())
    db.add(etapa)
    db.commit()
    db.refresh(etapa)
    return etapa


@router.get("/{projeto_id}/etapas", response_model=list[EtapaProjetoRead])
def listar_etapas(
    projeto_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[EtapaProjeto]:
    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=projeto.cpl_id)
    return (
        db.query(EtapaProjeto)
        .filter(EtapaProjeto.projeto_id == projeto_id)
        .order_by(EtapaProjeto.ordem)
        .all()
    )


@router.patch("/etapas/{etapa_id}", response_model=EtapaProjetoRead)
def atualizar_etapa(
    etapa_id: uuid.UUID,
    dados: EtapaProjetoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> EtapaProjeto:
    etapa = _get_etapa_or_404(db, etapa_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=etapa.projeto.cpl_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(etapa, campo, valor)
    db.commit()
    db.refresh(etapa)
    return etapa


# --- Metas do plano de trabalho (RF-034) ------------------------------------


@router.post("/{projeto_id}/metas", response_model=MetaProjetoRead, status_code=status.HTTP_201_CREATED)
def criar_meta(
    projeto_id: uuid.UUID,
    dados: MetaProjetoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> MetaProjeto:
    """RF-034: meta quantitativa ou qualitativa do plano de trabalho."""

    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    meta = MetaProjeto(projeto_id=projeto_id, **dados.model_dump())
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta


@router.get("/{projeto_id}/metas", response_model=list[MetaProjetoRead])
def listar_metas(
    projeto_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[MetaProjeto]:
    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=projeto.cpl_id)
    return (
        db.query(MetaProjeto)
        .filter(MetaProjeto.projeto_id == projeto_id)
        .order_by(MetaProjeto.created_at)
        .all()
    )


@router.patch("/metas/{meta_id}", response_model=MetaProjetoRead)
def atualizar_meta(
    meta_id: uuid.UUID,
    dados: MetaProjetoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> MetaProjeto:
    meta = _get_meta_or_404(db, meta_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=meta.projeto.cpl_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(meta, campo, valor)
    db.commit()
    db.refresh(meta)
    return meta


# --- Indicadores do plano de trabalho (RF-034) ------------------------------


@router.post(
    "/{projeto_id}/indicadores", response_model=IndicadorProjetoRead, status_code=status.HTTP_201_CREATED
)
def criar_indicador(
    projeto_id: uuid.UUID,
    dados: IndicadorProjetoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> IndicadorProjeto:
    """RF-034: indicador de acompanhamento do projeto."""

    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    indicador = IndicadorProjeto(projeto_id=projeto_id, **dados.model_dump())
    db.add(indicador)
    db.commit()
    db.refresh(indicador)
    return indicador


@router.get("/{projeto_id}/indicadores", response_model=list[IndicadorProjetoRead])
def listar_indicadores(
    projeto_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[IndicadorProjeto]:
    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=projeto.cpl_id)
    return (
        db.query(IndicadorProjeto)
        .filter(IndicadorProjeto.projeto_id == projeto_id)
        .order_by(IndicadorProjeto.created_at)
        .all()
    )


@router.patch("/indicadores/{indicador_id}", response_model=IndicadorProjetoRead)
def atualizar_indicador(
    indicador_id: uuid.UUID,
    dados: IndicadorProjetoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> IndicadorProjeto:
    indicador = _get_indicador_or_404(db, indicador_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=indicador.projeto.cpl_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(indicador, campo, valor)
    db.commit()
    db.refresh(indicador)
    return indicador


# --- Riscos do plano de trabalho (RF-034) -----------------------------------


@router.post("/{projeto_id}/riscos", response_model=RiscoProjetoRead, status_code=status.HTTP_201_CREATED)
def criar_risco(
    projeto_id: uuid.UUID,
    dados: RiscoProjetoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> RiscoProjeto:
    """RF-034/040: risco identificado do projeto — modelo pensado para
    ser reaproveitado pelo RF-040 (Execução) quando for construído."""

    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    risco = RiscoProjeto(projeto_id=projeto_id, **dados.model_dump())
    db.add(risco)
    db.commit()
    db.refresh(risco)
    return risco


@router.get("/{projeto_id}/riscos", response_model=list[RiscoProjetoRead])
def listar_riscos(
    projeto_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[RiscoProjeto]:
    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=projeto.cpl_id)
    return (
        db.query(RiscoProjeto)
        .filter(RiscoProjeto.projeto_id == projeto_id)
        .order_by(RiscoProjeto.created_at)
        .all()
    )


@router.patch("/riscos/{risco_id}", response_model=RiscoProjetoRead)
def atualizar_risco(
    risco_id: uuid.UUID,
    dados: RiscoProjetoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> RiscoProjeto:
    risco = _get_risco_or_404(db, risco_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=risco.projeto.cpl_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(risco, campo, valor)
    db.commit()
    db.refresh(risco)
    return risco


# --- Equipe do projeto (RF-035) ---------------------------------------------


@router.post("/{projeto_id}/equipe", response_model=EquipeProjetoRead, status_code=status.HTTP_201_CREATED)
def adicionar_membro_equipe(
    projeto_id: uuid.UUID,
    dados: EquipeProjetoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> EquipeProjeto:
    """RF-035: adiciona uma pessoa à equipe do projeto, com função e
    vigência — mesmo padrão de `MembroOrgao` (RF-016)."""

    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    membro = EquipeProjeto(projeto_id=projeto_id, **dados.model_dump())
    db.add(membro)
    db.commit()
    db.refresh(membro)
    return membro


@router.get("/{projeto_id}/equipe", response_model=list[EquipeProjetoRead])
def listar_equipe(
    projeto_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[EquipeProjeto]:
    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=projeto.cpl_id)
    return (
        db.query(EquipeProjeto)
        .filter(EquipeProjeto.projeto_id == projeto_id)
        .order_by(EquipeProjeto.created_at)
        .all()
    )


@router.patch("/equipe/{membro_id}", response_model=EquipeProjetoRead)
def atualizar_membro_equipe(
    membro_id: uuid.UUID,
    dados: EquipeProjetoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> EquipeProjeto:
    membro = _get_membro_equipe_or_404(db, membro_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=membro.projeto.cpl_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(membro, campo, valor)
    db.commit()
    db.refresh(membro)
    return membro


# --- Origem dos recursos do projeto (RF-035) --------------------------------


@router.post(
    "/{projeto_id}/origens-recurso",
    response_model=OrigemRecursoProjetoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_origem_recurso(
    projeto_id: uuid.UUID,
    dados: OrigemRecursoProjetoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> OrigemRecursoProjeto:
    """RF-035: registra uma fonte de recursos do projeto (própria, edital,
    parceria etc.) e o valor previsto."""

    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    origem = OrigemRecursoProjeto(projeto_id=projeto_id, **dados.model_dump())
    db.add(origem)
    db.commit()
    db.refresh(origem)
    return origem


@router.get("/{projeto_id}/origens-recurso", response_model=list[OrigemRecursoProjetoRead])
def listar_origens_recurso(
    projeto_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[OrigemRecursoProjeto]:
    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=projeto.cpl_id)
    return (
        db.query(OrigemRecursoProjeto)
        .filter(OrigemRecursoProjeto.projeto_id == projeto_id)
        .order_by(OrigemRecursoProjeto.created_at)
        .all()
    )


@router.patch("/origens-recurso/{origem_id}", response_model=OrigemRecursoProjetoRead)
def atualizar_origem_recurso(
    origem_id: uuid.UUID,
    dados: OrigemRecursoProjetoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> OrigemRecursoProjeto:
    origem = _get_origem_recurso_or_404(db, origem_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=origem.projeto.cpl_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(origem, campo, valor)
    db.commit()
    db.refresh(origem)
    return origem


# --- Submissão a edital de fomento e recursos (RF-030) ----------------------


@router.post("/{projeto_id}/submeter", response_model=ProjetoRead)
def submeter_projeto(
    projeto_id: uuid.UUID,
    dados: SubmissaoProjetoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Projeto:
    """RF-029/030: submete o projeto a um edital de fomento — vincula
    `edital_fomento_id` e move `estagio` para `SUBMETIDO` na mesma ação,
    já que submeter é o evento que causa essa transição de estágio."""

    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    _get_edital_fomento_or_404(db, dados.edital_fomento_id)
    projeto.edital_fomento_id = dados.edital_fomento_id
    projeto.estagio = EstagioProjeto.SUBMETIDO
    db.commit()
    db.refresh(projeto)
    return projeto


@router.post(
    "/{projeto_id}/recursos-submissao",
    response_model=RecursoSubmissaoProjetoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_recurso_submissao(
    projeto_id: uuid.UUID,
    dados: RecursoSubmissaoProjetoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> RecursoSubmissaoProjeto:
    """RF-030: recurso, contrarrazão ou diligência no processo de
    submissão do projeto a um edital de fomento."""

    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    recurso = RecursoSubmissaoProjeto(
        projeto_id=projeto_id, solicitado_por_id=usuario_atual.id, **dados.model_dump()
    )
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


@router.get("/{projeto_id}/recursos-submissao", response_model=list[RecursoSubmissaoProjetoRead])
def listar_recursos_submissao(
    projeto_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[RecursoSubmissaoProjeto]:
    projeto = _get_projeto_or_404(db, projeto_id)
    verificar_papel(db, usuario_atual, PAPEIS_PROJETO_LEITURA, cpl_id=projeto.cpl_id)
    return (
        db.query(RecursoSubmissaoProjeto)
        .filter(RecursoSubmissaoProjeto.projeto_id == projeto_id)
        .order_by(RecursoSubmissaoProjeto.created_at)
        .all()
    )


@router.post("/recursos-submissao/{recurso_id}/decidir", response_model=RecursoSubmissaoProjetoRead)
def decidir_recurso_submissao(
    recurso_id: uuid.UUID,
    dados: RecursoSubmissaoProjetoDecisao,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> RecursoSubmissaoProjeto:
    """Decisão é de quem administra o edital de fomento — autoridade
    diferente de quem gere o projeto que solicitou, mesmo raciocínio do
    RF-027 (`RecursoAvaliacao`)."""

    recurso = _get_recurso_submissao_or_404(db, recurso_id)
    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    recurso.status = dados.status
    recurso.parecer_decisao = dados.parecer_decisao
    recurso.decidido_por_id = usuario_atual.id
    recurso.data_decisao = date.today()
    db.commit()
    db.refresh(recurso)
    return recurso
