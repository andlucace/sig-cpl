import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CategoriaDocumento, ConfidencialidadeDocumento


class DocumentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    titulo: str
    categoria: CategoriaDocumento
    descricao: str | None
    confidencialidade: ConfidencialidadeDocumento
    nome_arquivo_original: str
    tipo_mime: str | None
    tamanho_bytes: int | None
    versao: int
    documento_anterior_id: uuid.UUID | None
    data_validade: date | None
    assinado: bool
    aprovado: bool
    aprovado_por_id: uuid.UUID | None
    data_aprovacao: date | None
    data_retencao_ate: date | None
    criado_por_id: uuid.UUID
    reuniao_id: uuid.UUID | None
    orgao_id: uuid.UUID | None
    created_at: datetime


class DocumentoAprovacaoUpdate(BaseModel):
    aprovado: bool | None = None
    assinado: bool | None = None
    aprovado_por_id: uuid.UUID | None = None
    data_retencao_ate: date | None = None
