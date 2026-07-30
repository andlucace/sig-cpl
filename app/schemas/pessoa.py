import uuid

from pydantic import BaseModel, ConfigDict


class PessoaCreate(BaseModel):
    nome: str
    cpf: str | None = None
    email: str | None = None
    telefone: str | None = None


class PessoaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    cpf: str | None
    email: str | None
    telefone: str | None
