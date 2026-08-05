import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    EstagioProjeto,
    ImpactoRisco,
    OrigemDemanda,
    PrioridadeProjeto,
    ProbabilidadeRisco,
    StatusDemanda,
    StatusRecurso,
    StatusRisco,
    StatusTarefa,
    TipoMeta,
    TipoRecursoSubmissao,
)

# Demanda de projeto (RF-031)


class DemandaProjetoCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    origem_tipo: OrigemDemanda
    origem_id: uuid.UUID | None = None
    origem_detalhe: str | None = None


class DemandaProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    titulo: str
    descricao: str | None
    origem_tipo: OrigemDemanda
    origem_id: uuid.UUID | None
    origem_detalhe: str | None
    status: StatusDemanda
    registrado_por_id: uuid.UUID
    created_at: datetime


# Projeto / portfólio (RF-032)


class ProjetoCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    eixo_sp_produz: str | None = None
    prioridade: PrioridadeProjeto = PrioridadeProjeto.MEDIA
    responsavel_id: uuid.UUID | None = None
    objetivo_estrategico_id: uuid.UUID | None = None
    introducao: str | None = None
    objeto: str | None = None
    objetivos: str | None = None
    justificativa: str | None = None
    impactos: str | None = None
    impactos_socioambientais: str | None = None
    continuidade: str | None = None
    escalabilidade: str | None = None


class ProjetoUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    eixo_sp_produz: str | None = None
    estagio: EstagioProjeto | None = None
    prioridade: PrioridadeProjeto | None = None
    responsavel_id: uuid.UUID | None = None
    objetivo_estrategico_id: uuid.UUID | None = None
    introducao: str | None = None
    objeto: str | None = None
    objetivos: str | None = None
    justificativa: str | None = None
    impactos: str | None = None
    impactos_socioambientais: str | None = None
    continuidade: str | None = None
    escalabilidade: str | None = None


class ProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    demanda_origem_id: uuid.UUID | None
    titulo: str
    descricao: str | None
    eixo_sp_produz: str | None
    estagio: EstagioProjeto
    prioridade: PrioridadeProjeto
    responsavel_id: uuid.UUID | None
    objetivo_estrategico_id: uuid.UUID | None
    introducao: str | None
    objeto: str | None
    objetivos: str | None
    justificativa: str | None
    impactos: str | None
    impactos_socioambientais: str | None
    continuidade: str | None
    escalabilidade: str | None
    edital_fomento_id: uuid.UUID | None
    created_at: datetime


# Etapas do plano de trabalho (RF-034)


class EtapaProjetoCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    valor_previsto: Decimal | None = None
    marco: bool = False


class EtapaProjetoUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    ordem: int | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    status: StatusTarefa | None = None
    valor_previsto: Decimal | None = None
    valor_executado: Decimal | None = None
    marco: bool | None = None


class EtapaProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    titulo: str
    descricao: str | None
    ordem: int
    data_inicio: date | None
    data_fim: date | None
    status: StatusTarefa
    valor_previsto: Decimal | None
    valor_executado: Decimal | None
    marco: bool
    created_at: datetime


# Metas do plano de trabalho (RF-034)


class MetaProjetoCreate(BaseModel):
    descricao: str
    tipo: TipoMeta
    valor_alvo: str | None = None
    prazo: date | None = None
    responsavel_id: uuid.UUID | None = None


class MetaProjetoUpdate(BaseModel):
    descricao: str | None = None
    tipo: TipoMeta | None = None
    valor_alvo: str | None = None
    valor_alcancado: str | None = None
    prazo: date | None = None
    responsavel_id: uuid.UUID | None = None
    status: StatusTarefa | None = None


class MetaProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    descricao: str
    tipo: TipoMeta
    valor_alvo: str | None
    valor_alcancado: str | None
    prazo: date | None
    responsavel_id: uuid.UUID | None
    status: StatusTarefa
    created_at: datetime


# Indicadores do plano de trabalho (RF-034)


class IndicadorProjetoCreate(BaseModel):
    nome: str
    unidade_medida: str | None = None
    meta_valor: str | None = None
    responsavel_id: uuid.UUID | None = None


class IndicadorProjetoUpdate(BaseModel):
    nome: str | None = None
    unidade_medida: str | None = None
    meta_valor: str | None = None
    valor_atual: str | None = None
    responsavel_id: uuid.UUID | None = None


class IndicadorProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    nome: str
    unidade_medida: str | None
    meta_valor: str | None
    valor_atual: str | None
    responsavel_id: uuid.UUID | None
    created_at: datetime


# Riscos do plano de trabalho (RF-034)


class RiscoProjetoCreate(BaseModel):
    descricao: str
    probabilidade: ProbabilidadeRisco
    impacto: ImpactoRisco
    resposta: str | None = None
    responsavel_id: uuid.UUID | None = None
    evidencia_documento_id: uuid.UUID | None = None


class RiscoProjetoUpdate(BaseModel):
    descricao: str | None = None
    probabilidade: ProbabilidadeRisco | None = None
    impacto: ImpactoRisco | None = None
    resposta: str | None = None
    responsavel_id: uuid.UUID | None = None
    status: StatusRisco | None = None
    evidencia_documento_id: uuid.UUID | None = None


class RiscoProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    descricao: str
    probabilidade: ProbabilidadeRisco
    impacto: ImpactoRisco
    resposta: str | None
    responsavel_id: uuid.UUID | None
    status: StatusRisco
    evidencia_documento_id: uuid.UUID | None
    created_at: datetime


# Equipe do projeto (RF-035)


class EquipeProjetoCreate(BaseModel):
    pessoa_id: uuid.UUID
    funcao: str
    data_inicio: date
    data_fim: date | None = None


class EquipeProjetoUpdate(BaseModel):
    funcao: str | None = None
    data_fim: date | None = None
    ativo: bool | None = None


class EquipeProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    pessoa_id: uuid.UUID
    funcao: str
    data_inicio: date
    data_fim: date | None
    ativo: bool
    created_at: datetime


# Origem dos recursos do projeto (RF-035)


class OrigemRecursoProjetoCreate(BaseModel):
    fonte: str
    valor: Decimal
    contrapartida: bool = False
    descricao: str | None = None


class OrigemRecursoProjetoUpdate(BaseModel):
    fonte: str | None = None
    valor: Decimal | None = None
    contrapartida: bool | None = None
    descricao: str | None = None


class OrigemRecursoProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    fonte: str
    valor: Decimal
    contrapartida: bool
    descricao: str | None
    created_at: datetime


# Edital de fomento (RF-029)


class EditalFomentoCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    requisitos: str | None = None
    documentos_exigidos: str | None = None
    data_abertura: date | None = None
    data_encerramento: date | None = None
    responsavel_id: uuid.UUID | None = None


class EditalFomentoUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    requisitos: str | None = None
    documentos_exigidos: str | None = None
    data_abertura: date | None = None
    data_encerramento: date | None = None
    responsavel_id: uuid.UUID | None = None
    ativo: bool | None = None


class EditalFomentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    titulo: str
    descricao: str | None
    requisitos: str | None
    documentos_exigidos: str | None
    data_abertura: date | None
    data_encerramento: date | None
    responsavel_id: uuid.UUID | None
    ativo: bool
    created_at: datetime


# Submissão a edital de fomento e recursos (RF-030)


class SubmissaoProjetoCreate(BaseModel):
    edital_fomento_id: uuid.UUID


class RecursoSubmissaoProjetoCreate(BaseModel):
    tipo: TipoRecursoSubmissao
    protocolo: str | None = None
    prazo: date | None = None
    descricao: str


class RecursoSubmissaoProjetoDecisao(BaseModel):
    status: StatusRecurso
    parecer_decisao: str | None = None


class RecursoSubmissaoProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    tipo: TipoRecursoSubmissao
    protocolo: str | None
    prazo: date | None
    descricao: str
    solicitado_por_id: uuid.UUID
    status: StatusRecurso
    parecer_decisao: str | None
    decidido_por_id: uuid.UUID | None
    data_decisao: date | None
    created_at: datetime


# Aquisições do projeto (RF-035)


class AquisicaoProjetoCreate(BaseModel):
    item: str
    descricao: str | None = None
    categoria: str | None = None
    quantidade: str | None = None
    valor_estimado: Decimal | None = None
    contrapartida: bool = False
    data_prevista: date | None = None
    responsavel_id: uuid.UUID | None = None
    etapa_id: uuid.UUID | None = None
    origem_recurso_id: uuid.UUID | None = None


class AquisicaoProjetoUpdate(BaseModel):
    item: str | None = None
    descricao: str | None = None
    categoria: str | None = None
    quantidade: str | None = None
    valor_estimado: Decimal | None = None
    contrapartida: bool | None = None
    data_prevista: date | None = None
    responsavel_id: uuid.UUID | None = None
    etapa_id: uuid.UUID | None = None
    origem_recurso_id: uuid.UUID | None = None
    status: StatusTarefa | None = None
    justificativa_excecao: str | None = None


class AquisicaoProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    etapa_id: uuid.UUID | None
    origem_recurso_id: uuid.UUID | None
    item: str
    descricao: str | None
    categoria: str | None
    quantidade: str | None
    valor_estimado: Decimal | None
    contrapartida: bool
    data_prevista: date | None
    responsavel_id: uuid.UUID | None
    status: StatusTarefa
    justificativa_excecao: str | None
    created_at: datetime


# Cotações de aquisição (RF-037)


class CotacaoAquisicaoCreate(BaseModel):
    fornecedor: str
    valor: Decimal
    documento_id: uuid.UUID | None = None
    observacao: str | None = None


class CotacaoAquisicaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    aquisicao_id: uuid.UUID
    fornecedor: str
    valor: Decimal
    documento_id: uuid.UUID | None
    selecionada: bool
    observacao: str | None
    created_at: datetime


class SelecaoCotacaoCreate(BaseModel):
    justificativa_excecao: str | None = None


# Desembolsos do projeto (RF-038)


class DesembolsoProjetoCreate(BaseModel):
    aquisicao_id: uuid.UUID | None = None
    origem_recurso_id: uuid.UUID | None = None
    data: date
    valor: Decimal
    descricao: str | None = None
    bem_adquirido: str | None = None
    documento_comprovante_id: uuid.UUID | None = None


class DesembolsoProjetoUpdate(BaseModel):
    descricao: str | None = None
    bem_adquirido: str | None = None
    documento_comprovante_id: uuid.UUID | None = None
    conciliado: bool | None = None


class DesembolsoProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    aquisicao_id: uuid.UUID | None
    origem_recurso_id: uuid.UUID | None
    data: date
    valor: Decimal
    descricao: str | None
    bem_adquirido: str | None
    documento_comprovante_id: uuid.UUID | None
    conciliado: bool
    created_at: datetime


# Entregas do projeto (RF-039)


class EntregaProjetoCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    etapa_id: uuid.UUID | None = None
    data_prevista: date | None = None
    documento_id: uuid.UUID | None = None


class EntregaProjetoUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    etapa_id: uuid.UUID | None = None
    data_prevista: date | None = None
    data_entrega: date | None = None
    documento_id: uuid.UUID | None = None


class EntregaProjetoAprovacao(BaseModel):
    aprovado: bool
    aprovado_por_id: uuid.UUID


class EntregaProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    etapa_id: uuid.UUID | None
    titulo: str
    descricao: str | None
    data_prevista: date | None
    data_entrega: date | None
    documento_id: uuid.UUID | None
    aprovado: bool
    aprovado_por_id: uuid.UUID | None
    data_aprovacao: date | None
    created_at: datetime


# Alterações de plano do projeto (RF-039)


class AlteracaoPlanoProjetoCreate(BaseModel):
    tipo: str
    descricao: str
    data_solicitacao: date


class AlteracaoPlanoProjetoDecisao(BaseModel):
    status: StatusRecurso
    parecer_decisao: str | None = None


class AlteracaoPlanoProjetoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    projeto_id: uuid.UUID
    tipo: str
    descricao: str
    data_solicitacao: date
    solicitado_por_id: uuid.UUID
    status: StatusRecurso
    parecer_decisao: str | None
    decidido_por_id: uuid.UUID | None
    data_decisao: date | None
    created_at: datetime
