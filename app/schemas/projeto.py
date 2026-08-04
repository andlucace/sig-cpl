import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import EstagioProjeto, OrigemDemanda, PrioridadeProjeto, StatusDemanda, StatusTarefa

# Demanda de projeto (RF-031)


class DemandaProjetoCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    origem_tipo: OrigemDemanda
    origem_id: uuid.UUID | None = None
    origem_detalhe: str | None = None


class DemandaProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    titulo: str
    descricao: str | None
    origem_tipo: OrigemDemanda
    origem_id: uuid.UUID | None
    origem_detalhe: str | None
    status: StatusDemanda
    registrado_por_id: uuid.UUID
    created_at: datetime


# Projeto / portfólio (RF-032)


class ProjetoCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    eixo_sp_produz: str | None = None
    prioridade: PrioridadeProjeto = PrioridadeProjeto.MEDIA
    responsavel_id: uuid.UUID | None = None
    objetivo_estrategico_id: uuid.UUID | None = None
    introducao: str | None = None
    objeto: str | None = None
    objetivos: str | None = None
    justificativa: str | None = None
    impactos: str | None = None


class ProjetoUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    eixo_sp_produz: str | None = None
    estagio: EstagioProjeto | None = None
    prioridade: PrioridadeProjeto | None = None
    responsavel_id: uuid.UUID | None = None
    objetivo_estrategico_id: uuid.UUID | None = None
    introducao: str | None = None
    objeto: str | None = None
    objetivos: str | None = None
    justificativa: str | None = None
    impactos: str | None = None


class ProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    demanda_origem_id: uuid.UUID | None
    titulo: str
    descricao: str | None
    eixo_sp_produz: str | None
    estagio: EstagioProjeto
    prioridade: PrioridadeProjeto
    responsavel_id: uuid.UUID | None
    objetivo_estrategico_id: uuid.UUID | None
    introducao: str | None
    objeto: str | None
    objetivos: str | None
    justificativa: str | None
    impactos: str | None
    created_at: datetime


# Etapas do plano de trabalho (RF-034)


class EtapaProjetoCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None


class EtapaProjetoUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    ordem: int | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    status: StatusTarefa | None = None


class EtapaProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    titulo: str
    descricao: str | None
    ordem: int
    data_inicio: date | None
    data_fim: date | None
    status: StatusTarefa
    created_at: datetime
