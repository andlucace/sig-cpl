import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.enums import NivelMaturidade


class CPLCreate(BaseModel):
    nome: str
    sigla: str
    setor: str | None = None
    municipio: str | None = None
    uf: str | None = None
    entidade_gestora_id: uuid.UUID | None = None


class CPLUpdate(BaseModel):
    """Não inclui `nivel_maturidade`/`data_reconhecimento`/
    `data_validade_reconhecimento` de propósito — esses campos só mudam
    via `POST /api/maturidade/avaliacoes/{id}/decidir` (RN-016: decisão
    humana dentro do fluxo de avaliação, não uma edição solta de CPL)."""

    nome: str | None = None
    sigla: str | None = None
    setor: str | None = None
    municipio: str | None = None
    uf: str | None = None
    entidade_gestora_id: uuid.UUID | None = None
    ativo: bool | None = None


class CPLRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    sigla: str
    setor: str | None
    municipio: str | None
    uf: str | None
    entidade_gestora_id: uuid.UUID | None
    nivel_maturidade: NivelMaturidade | None
    data_reconhecimento: date | None
    data_validade_reconhecimento: date | None
    ativo: bool
