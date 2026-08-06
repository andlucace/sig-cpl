import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusEvento, TipoEvento

# Evento (RF-050)


class EventoCreate(BaseModel):
    cpl_id: uuid.UUID | None = None
    titulo: str
    tipo: TipoEvento
    descricao: str | None = None
    data_inicio: datetime
    data_fim: datetime | None = None
    local: str | None = None
    vagas: int | None = None


class EventoUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    local: str | None = None
    vagas: int | None = None
    status: StatusEvento | None = None


class EventoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID | None
    titulo: str
    tipo: TipoEvento
    descricao: str | None
    data_inicio: datetime
    data_fim: datetime | None
    local: str | None
    vagas: int | None
    status: StatusEvento
    criado_por_id: uuid.UUID


# Inscrição, presença e avaliação (RF-050)


class InscricaoEventoCreate(BaseModel):
    pessoa_id: uuid.UUID
    cpl_id: uuid.UUID | None = None


class InscricaoEventoAtualizar(BaseModel):
    presente: bool | None = None
    nota_avaliacao: int | None = Field(default=None, ge=1, le=5)
    comentario_avaliacao: str | None = None


class InscricaoEventoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evento_id: uuid.UUID
    pessoa_id: uuid.UUID
    cpl_id: uuid.UUID | None
    presente: bool | None
    nota_avaliacao: int | None
    comentario_avaliacao: str | None
    created_at: datetime
