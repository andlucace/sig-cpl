import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import Papel


class UsuarioPapelCreate(BaseModel):
    papel: Papel
    cpl_id: uuid.UUID | None = None
    entidade_id: uuid.UUID | None = None


class UsuarioPapelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    usuario_id: uuid.UUID
    papel: Papel
    cpl_id: uuid.UUID | None
    entidade_id: uuid.UUID | None
