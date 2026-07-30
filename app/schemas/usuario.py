import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class UsuarioCreate(BaseModel):
    email: EmailStr
    password: str


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    ativo: bool
    mfa_enabled: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
