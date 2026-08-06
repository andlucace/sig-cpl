import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RegistroFalhaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    metodo: str
    rota: str
    tipo_excecao: str
    mensagem: str | None
    status_code: int
    usuario_id: uuid.UUID | None
    request_id: str | None


class SaudeSistemaRead(BaseModel):
    banco_ok: bool
    uptime_segundos: int
    total_requisicoes: int
    por_status: dict[str, int]
    latencia_media_ms: float
    total_falhas_recentes: int
    janela_minutos: int
    alerta_ativo: bool
    falhas_recentes: list[RegistroFalhaRead]
