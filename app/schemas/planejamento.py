import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.enums import Elo, PrazoObjetivo, StatusPlanejamento, StatusTarefa, TipoDiagnostico

# Planejamento Estratégico (RF-021)


class PlanejamentoEstrategicoCreate(BaseModel):
    ciclo: str
    caracterizacao: str | None = None
    historico: str | None = None
    mercado: str | None = None
    inovacao: str | None = None
    impactos: str | None = None
    internacionalizacao: str | None = None


class PlanejamentoEstrategicoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    ciclo: str
    status: StatusPlanejamento
    caracterizacao: str | None
    historico: str | None
    mercado: str | None
    inovacao: str | None
    impactos: str | None
    internacionalizacao: str | None
    data_aprovacao: date | None


class PlanejamentoStatusUpdate(BaseModel):
    status: StatusPlanejamento
    data_aprovacao: date | None = None


# Diagnóstico (RF-022)


class DiagnosticoItemCreate(BaseModel):
    tipo: TipoDiagnostico
    descricao: str
    elo_relacionado: Elo | None = None
    prioridade: int | None = None


class DiagnosticoItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    planejamento_id: uuid.UUID
    tipo: TipoDiagnostico
    descricao: str
    elo_relacionado: Elo | None
    prioridade: int | None


# Objetivo (RF-023)


class ObjetivoEstrategicoCreate(BaseModel):
    descricao: str
    prazo: PrazoObjetivo
    responsavel_id: uuid.UUID | None = None
    orcamento_estimado: float | None = None


class ObjetivoEstrategicoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    planejamento_id: uuid.UUID
    descricao: str
    prazo: PrazoObjetivo
    responsavel_id: uuid.UUID | None
    orcamento_estimado: float | None
    status: StatusTarefa


class ObjetivoStatusUpdate(BaseModel):
    status: StatusTarefa


# Meta (RF-023/RN-010)


class MetaEstrategicaCreate(BaseModel):
    descricao: str
    valor_alvo: str
    metodo_afericao: str | None = None
    prazo: date | None = None
    responsavel_id: uuid.UUID | None = None


class MetaEstrategicaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    objetivo_id: uuid.UUID
    descricao: str
    valor_alvo: str
    metodo_afericao: str | None
    prazo: date | None
    responsavel_id: uuid.UUID | None
    evidencia: str | None
    status: StatusTarefa


class MetaStatusUpdate(BaseModel):
    status: StatusTarefa
    evidencia: str | None = None


# Iniciativa (RF-023)


class IniciativaEstrategicaCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    responsavel_id: uuid.UUID | None = None
    prazo: date | None = None


class IniciativaEstrategicaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    objetivo_id: uuid.UUID
    titulo: str
    descricao: str | None
    responsavel_id: uuid.UUID | None
    prazo: date | None
    status: StatusTarefa


class IniciativaStatusUpdate(BaseModel):
    status: StatusTarefa


# Indicador (RF-023)


class IndicadorEstrategicoCreate(BaseModel):
    nome: str
    formula: str | None = None
    fonte: str | None = None
    unidade: str | None = None
    meta_valor: str | None = None
    valor_atual: str | None = None
    periodicidade: str | None = None
    responsavel_id: uuid.UUID | None = None


class IndicadorEstrategicoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    objetivo_id: uuid.UUID
    nome: str
    formula: str | None
    fonte: str | None
    unidade: str | None
    meta_valor: str | None
    valor_atual: str | None
    periodicidade: str | None
    responsavel_id: uuid.UUID | None


class IndicadorValorUpdate(BaseModel):
    valor_atual: str | None = None
    data_referencia: date | None = None
    observacao: str | None = None


class IndicadorValorHistoricoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    indicador_id: uuid.UUID
    data_referencia: date
    valor: str
    observacao: str | None
    registrado_por_id: uuid.UUID
