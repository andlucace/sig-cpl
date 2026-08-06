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


class MensagemRead(BaseModel):
    mensagem: str


class EsqueciSenhaCreate(BaseModel):
    email: EmailStr


class RedefinirSenhaCreate(BaseModel):
    token: str
    nova_senha: str


class MFAIniciarRead(BaseModel):
    segredo: str
    qr_code_base64: str


class MFAConfirmarCreate(BaseModel):
    codigo: str


class MFAConfirmarRead(BaseModel):
    codigos_backup: list[str]


class MFADesativarCreate(BaseModel):
    password: str
