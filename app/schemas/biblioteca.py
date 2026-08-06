import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import TipoRecursoBiblioteca


class RecursoBibliotecaUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    url_externa: str | None = None
    publicado: bool | None = None


class RecursoBibliotecaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    titulo: str
    tipo: TipoRecursoBiblioteca
    descricao: str | None
    nome_arquivo_original: str | None
    tipo_mime: str | None
    tamanho_bytes: int | None
    url_externa: str | None
    publicado: bool
    criado_por_id: uuid.UUID
    created_at: datetime
