import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import StatusMatchInovacao


class MatchInovacaoCreate(BaseModel):
    entidade_id: uuid.UUID
    oferta_id: uuid.UUID | None = None
    observacao: str | None = None


class MatchInovacaoAtualizar(BaseModel):
    status: StatusMatchInovacao | None = None
    observacao: str | None = None


class MatchInovacaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    demanda_id: uuid.UUID
    entidade_id: uuid.UUID
    oferta_id: uuid.UUID | None
    status: StatusMatchInovacao
    observacao: str | None
    sugerido_por_id: uuid.UUID
    created_at: datetime
