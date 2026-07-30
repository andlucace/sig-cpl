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


class CPLRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    sigla: str
    setor: str | None
    municipio: str | None
    uf: str | None
    nivel_maturidade: NivelMaturidade | None
    data_reconhecimento: date | None
    data_validade_reconhecimento: date | None
    ativo: bool
