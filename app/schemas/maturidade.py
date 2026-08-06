import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    DimensaoMaturidade,
    NivelMaturidade,
    StatusAvaliacao,
    StatusItemHabilitacao,
    StatusRecurso,
)

# Edital (RF-024/RN-006)


class EditalCreate(BaseModel):
    nome: str
    ciclo: str
    descricao: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    limiar_cpl_em_desenvolvimento: float | None = None
    limiar_cpl_consolidada: float | None = None
    limiar_cpl_madura: float | None = None


class EditalUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    ativo: bool | None = None
    limiar_cpl_em_desenvolvimento: float | None = None
    limiar_cpl_consolidada: float | None = None
    limiar_cpl_madura: float | None = None


class EditalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    ciclo: str
    descricao: str | None
    data_inicio: date | None
    data_fim: date | None
    ativo: bool
    limiar_cpl_em_desenvolvimento: float | None
    limiar_cpl_consolidada: float | None
    limiar_cpl_madura: float | None


# Critério (RF-024)


class CriterioMaturidadeCreate(BaseModel):
    nome: str
    descricao: str | None = None
    dimensao: DimensaoMaturidade
    peso: float = 1.0
    nota_corte: float | None = None


class CriterioMaturidadeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    edital_id: uuid.UUID
    nome: str
    descricao: str | None
    dimensao: DimensaoMaturidade
    peso: float
    nota_corte: float | None


# Avaliação (RF-024/025/026)


class AvaliacaoCreate(BaseModel):
    edital_id: uuid.UUID
    data_avaliacao: date


class AvaliacaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    edital_id: uuid.UUID
    status: StatusAvaliacao
    avaliador_id: uuid.UUID
    data_avaliacao: date
    pontuacao_calculada: float | None
    nivel_sugerido: NivelMaturidade | None
    nivel_decidido: NivelMaturidade | None
    parecer: str | None
    decidido_por_id: uuid.UUID | None
    data_decisao: date | None


class AvaliacaoCriterioUpsert(BaseModel):
    criterio_id: uuid.UUID
    nota: float
    evidencia_documento_id: uuid.UUID | None = None
    observacao: str | None = None


class AvaliacaoCriterioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    avaliacao_id: uuid.UUID
    criterio_id: uuid.UUID
    nota: float
    evidencia_documento_id: uuid.UUID | None
    observacao: str | None


class DecisaoNivelCreate(BaseModel):
    nivel_decidido: NivelMaturidade
    parecer: str | None = None
    decidido_por_id: uuid.UUID | None = None


class SimulacaoAvaliacaoRead(BaseModel):
    """RF-026: "simular cenários" — pontuação/nível que resultariam de
    concluir a avaliação *agora*, com as notas já lançadas até este
    ponto, sem persistir nada. Deixa de fazer sentido depois que a
    avaliação é concluída de verdade (os campos reais de `Avaliacao` já
    respondem a mesma pergunta a partir daí)."""

    pontuacao_simulada: float | None
    nivel_sugerido_simulado: NivelMaturidade | None
    total_criterios: int
    total_notas_lancadas: int
    lacunas: list[AvaliacaoCriterioRead]


# Recurso (RF-027)


class RecursoAvaliacaoCreate(BaseModel):
    justificativa: str


class RecursoAvaliacaoDecisao(BaseModel):
    status: StatusRecurso
    parecer_decisao: str | None = None


class RecursoAvaliacaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    avaliacao_id: uuid.UUID
    justificativa: str
    solicitado_por_id: uuid.UUID
    status: StatusRecurso
    parecer_decisao: str | None
    decidido_por_id: uuid.UUID | None
    data_decisao: date | None
    created_at: datetime


# Habilitação jurídica (RF-027)


class ItemHabilitacaoCreate(BaseModel):
    edital_id: uuid.UUID
    descricao: str
    obrigatorio: bool = True
    documento_id: uuid.UUID | None = None


class ItemHabilitacaoAnalise(BaseModel):
    status: StatusItemHabilitacao
    parecer: str | None = None


class ItemHabilitacaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    edital_id: uuid.UUID
    descricao: str
    obrigatorio: bool
    documento_id: uuid.UUID | None
    status: StatusItemHabilitacao
    parecer: str | None
    analisado_por_id: uuid.UUID | None
    data_analise: date | None
