import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import TipoEntidade, TipoOferta


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
    email: EmailStr | None = None


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
    endereco: str | None = None
    email: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    ativo: bool
    canais_digitais: dict | None = None


class EntidadeEmailUpdate(BaseModel):
    email: EmailStr | None = None


class CanaisDigitaisUpdate(BaseModel):
    canais_digitais: dict[str, str]


class LocalizacaoUpdate(BaseModel):
    latitude: float
    longitude: float


class EntidadeMapaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: TipoEntidade
    razao_social: str
    municipio: str | None
    uf: str | None
    latitude: float
    longitude: float


class OfertaEntidadeCreate(BaseModel):
    tipo: TipoOferta
    nome: str
    descricao: str | None = None


class OfertaEntidadeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entidade_id: uuid.UUID
    tipo: TipoOferta
    nome: str
    descricao: str | None
    ativo: bool


class EntidadeCPLRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entidade_id: uuid.UUID
    cpl_id: uuid.UUID
    data_vinculo: date
    ativo: bool
    entidade: EntidadeRead
