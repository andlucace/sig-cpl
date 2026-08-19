import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ResultadoDeliberacao, StatusReuniao, StatusTarefa, TipoOrgao, TipoVoto

# Órgão de governança (RF-015/RF-016)


class OrgaoGovernancaCreate(BaseModel):
    nome: str
    tipo: TipoOrgao
    competencias: str | None = None
    quorum_minimo_percentual: float | None = None
    periodicidade: str | None = None
    estatuto_regimento_referencia: str | None = None


class OrgaoGovernancaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    nome: str
    tipo: TipoOrgao
    competencias: str | None
    quorum_minimo_percentual: float | None
    periodicidade: str | None
    estatuto_regimento_referencia: str | None
    ativo: bool


# Membro do órgão / mandato (RF-016)


class MembroOrgaoCreate(BaseModel):
    pessoa_id: uuid.UUID
    funcao: str
    data_inicio: date
    data_fim: date | None = None


class MembroOrgaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    orgao_id: uuid.UUID
    pessoa_id: uuid.UUID
    funcao: str
    data_inicio: date
    data_fim: date | None
    ativo: bool
    motivo_remocao: str | None


class MembroOrgaoRemocaoCreate(BaseModel):
    motivo: str


# Reunião (RF-017)


class ReuniaoCreate(BaseModel):
    titulo: str
    data_hora: datetime
    local: str | None = None
    pauta: str | None = None
    convocada_em: datetime | None = None


class ReuniaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    orgao_id: uuid.UUID
    titulo: str
    data_hora: datetime
    local: str | None
    pauta: str | None
    status: StatusReuniao
    convocada_em: datetime | None
    ata: str | None
    quorum_atingido: bool | None
    email_convocacao_enviado: bool
    email_convocacao_enviado_em: datetime | None
    email_convocacao_destinatarios: list[str] | None
    email_convocacao_erro: str | None


class ReuniaoAtaUpdate(BaseModel):
    status: StatusReuniao
    ata: str | None = None
    quorum_atingido: bool | None = None


# Presença (RF-017)


class PresencaCreate(BaseModel):
    pessoa_id: uuid.UUID
    presente: bool
    justificativa_ausencia: str | None = None


class PresencaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reuniao_id: uuid.UUID
    pessoa_id: uuid.UUID
    presente: bool
    justificativa_ausencia: str | None


# Deliberação (RF-018)


class DeliberacaoCreate(BaseModel):
    descricao: str
    quorum_necessario_percentual: float | None = None
    responsavel_id: uuid.UUID | None = None
    prazo_execucao: date | None = None


class DeliberacaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reuniao_id: uuid.UUID
    descricao: str
    resultado: ResultadoDeliberacao
    quorum_necessario_percentual: float | None
    responsavel_id: uuid.UUID | None
    prazo_execucao: date | None
    evidencia_execucao: str | None


class DeliberacaoResultadoUpdate(BaseModel):
    resultado: ResultadoDeliberacao
    evidencia_execucao: str | None = None


# Voto (RF-018/RF-020)


class VotoCreate(BaseModel):
    pessoa_id: uuid.UUID
    voto: TipoVoto
    motivo_impedimento: str | None = None


class VotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    deliberacao_id: uuid.UUID
    pessoa_id: uuid.UUID
    voto: TipoVoto
    motivo_impedimento: str | None


# Tarefa decorrente de deliberação (RF-019)


class TarefaGovernancaCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    responsavel_id: uuid.UUID | None = None
    prazo: date | None = None


class TarefaGovernancaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    deliberacao_id: uuid.UUID | None
    titulo: str
    descricao: str | None
    responsavel_id: uuid.UUID | None
    prazo: date | None
    status: StatusTarefa


class TarefaStatusUpdate(BaseModel):
    status: StatusTarefa


# Declaração de impedimento (RF-020)


class DeclaracaoImpedimentoCreate(BaseModel):
    pessoa_id: uuid.UUID
    orgao_id: uuid.UUID | None = None
    reuniao_id: uuid.UUID | None = None
    motivo: str
    data_declaracao: date


class DeclaracaoImpedimentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pessoa_id: uuid.UUID
    cpl_id: uuid.UUID
    orgao_id: uuid.UUID | None
    reuniao_id: uuid.UUID | None
    motivo: str
    data_declaracao: date
