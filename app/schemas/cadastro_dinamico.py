import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import StatusLinhaImportacao, StatusLoteImportacao

# Diagnóstico cadastral (RF-012)


class DiagnosticoCadastralUpdate(BaseModel):
    atividades_produtos: str | None = None
    diferenciais_competitivos: str | None = None
    faturamento_faixa: str | None = None
    empregos_diretos: int | None = None
    empregos_indiretos: int | None = None
    participacao_associativa: bool | None = None
    entidades_associativas: str | None = None
    compartilha_recursos: bool | None = None
    recursos_compartilhados: str | None = None
    realiza_inovacao: bool | None = None
    descricao_inovacao: str | None = None
    realiza_pd: bool | None = None
    ods_relacionados: str | None = None
    exporta: bool | None = None
    mercados_exportacao: str | None = None
    interesse_comissoes: str | None = None
    oferece_qualificacao_colaboradores: bool | None = None
    descricao_qualificacao: str | None = None
    adota_praticas_sustentabilidade: bool | None = None
    descricao_sustentabilidade: str | None = None
    possui_contatos_internacionais: bool | None = None
    descricao_contatos_internacionais: str | None = None
    possui_certificacoes: bool | None = None
    certificacoes: str | None = None
    nivel_digitalizacao: str | None = None
    capacidade_produtiva: str | None = None


class DiagnosticoCadastralRead(DiagnosticoCadastralUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entidade_id: uuid.UUID


# Campanha de atualização cadastral (RF-012)


class CampanhaCadastralCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None


class CampanhaCadastralRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    titulo: str
    descricao: str | None
    data_inicio: date | None
    data_fim: date | None
    ativa: bool


class CampanhaConviteCreate(BaseModel):
    entidade_id: uuid.UUID


class CampanhaConviteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campanha_id: uuid.UUID
    entidade_id: uuid.UUID
    token: str
    respondido: bool
    respondido_em: datetime | None
    created_at: datetime
    email_enviado: bool
    email_enviado_em: datetime | None
    email_destinatarios: list[str] | None
    email_erro: str | None


# Importação de planilha (RF-013/RF-014)


class ImportacaoLinhaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    numero_linha: int
    status: StatusLinhaImportacao
    mensagem: str | None
    entidade_id: uuid.UUID | None


class ImportacaoLoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cpl_id: uuid.UUID
    usuario_id: uuid.UUID
    nome_arquivo: str
    status: StatusLoteImportacao
    mapeamento_colunas: dict[str, int] | None
    total_linhas: int
    total_criadas: int
    total_atualizadas: int
    total_erros: int
    linhas: list[ImportacaoLinhaRead] = []


class PrepararImportacaoRead(BaseModel):
    """RF-013 (remapeamento manual), resposta do passo 1: cabeçalhos
    lidos + mapeamento sugerido, pra o cliente montar a tela/payload de
    confirmação — `campos_conhecidos` lista todos os campos que podem ser
    mapeados, mesmo os que a sugestão não bateu com nenhuma coluna."""

    lote: ImportacaoLoteRead
    cabecalhos: list[str]
    mapeamento_sugerido: dict[str, int]
    campos_conhecidos: list[str]


class ConfirmarMapeamentoCreate(BaseModel):
    mapeamento: dict[str, int]
