import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AcaoAuditoria


class RegistroAuditoriaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    usuario_id: uuid.UUID | None
    acao: AcaoAuditoria
    entidade_tipo: str
    entidade_id: uuid.UUID | None
    cpl_id: uuid.UUID | None
    descricao: str | None
    dados_anteriores: dict | None
    dados_novos: dict | None
    ip_address: str | None
