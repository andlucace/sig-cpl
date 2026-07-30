import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.enums import TipoEntidade


class EntidadeCreate(BaseModel):
    tipo: TipoEntidade
    razao_social: str
    nome_fantasia: str | None = None
    cnpj: str | None = None
    cpf: str | None = None
    cnae: str | None = None
    porte: str | None = None
    municipio: str | None = None
    uf: str | None = None
    endereco: str | None = None


class EntidadeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: TipoEntidade
    razao_social: str
    nome_fantasia: str | None
    cnpj: str | None
    cpf: str | None
    municipio: str | None
    uf: str | None
    ativo: bool


class EntidadeCPLRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entidade_id: uuid.UUID
    cpl_id: uuid.UUID
    data_vinculo: date
    ativo: bool
    entidade: EntidadeRead
