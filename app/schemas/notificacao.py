import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import TipoNotificacao


class NotificacaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID | None
    tipo: TipoNotificacao
    titulo: str
    mensagem: str | None
    entidade_tipo: str
    entidade_id: uuid.UUID
    lida: bool
    lida_em: datetime | None
    created_at: datetime
