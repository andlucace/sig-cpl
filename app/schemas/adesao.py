import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import Elo, StatusSolicitacaoAdesao, TipoEntidade


class SolicitacaoAdesaoCreate(BaseModel):
    tipo: TipoEntidade
    razao_social: str
    cnpj: str | None = None
    cpf: str | None = None
    municipio: str | None = None
    uf: str | None = None
    elo_pretendido: Elo
    mensagem: str | None = None
    contato_nome: str
    contato_email: EmailStr
    contato_telefone: str | None = None
    consentimento_lgpd: bool = False


class SolicitacaoAdesaoAnalise(BaseModel):
    parecer: str | None = None


class SolicitacaoAdesaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    tipo: TipoEntidade
    razao_social: str
    cnpj: str | None
    cpf: str | None
    municipio: str | None
    uf: str | None
    elo_pretendido: Elo
    mensagem: str | None
    contato_nome: str
    contato_email: str
    contato_telefone: str | None
    consentimento_lgpd: bool
    consentimento_em: datetime
    status: StatusSolicitacaoAdesao
    parecer: str | None
    analisado_por_id: uuid.UUID | None
    data_analise: date | None
    entidade_id: uuid.UUID | None
