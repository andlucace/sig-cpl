import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedBase
from app.models.enums import StatusLinhaImportacao, StatusLoteImportacao


class DiagnosticoCadastral(TimestampedBase):
    """RF-012: campos de diagnóstico da planilha "CPLS - FORMS.xlsx" citada
    na seção 3 do documento — um registro por Entidade, separado do cadastro
    básico (RF-006/008) para não misturar dado cadastral com dado de
    pesquisa/diagnóstico, que muda de campanha para campanha."""

    __tablename__ = "diagnosticos_cadastrais"

    entidade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entidades.id"), unique=True, nullable=False
    )
    atividades_produtos: Mapped[str | None] = mapped_column(Text)
    diferenciais_competitivos: Mapped[str | None] = mapped_column(Text)
    faturamento_faixa: Mapped[str | None] = mapped_column(String(100))
    empregos_diretos: Mapped[int | None] = mapped_column(Integer)
    empregos_indiretos: Mapped[int | None] = mapped_column(Integer)
    participacao_associativa: Mapped[bool | None] = mapped_column(Boolean)
    entidades_associativas: Mapped[str | None] = mapped_column(Text)
    compartilha_recursos: Mapped[bool | None] = mapped_column(Boolean)
    recursos_compartilhados: Mapped[str | None] = mapped_column(Text)
    realiza_inovacao: Mapped[bool | None] = mapped_column(Boolean)
    descricao_inovacao: Mapped[str | None] = mapped_column(Text)
    realiza_pd: Mapped[bool | None] = mapped_column(Boolean)
    ods_relacionados: Mapped[str | None] = mapped_column(String(255))
    exporta: Mapped[bool | None] = mapped_column(Boolean)
    mercados_exportacao: Mapped[str | None] = mapped_column(Text)
    interesse_comissoes: Mapped[str | None] = mapped_column(Text)
    # RF-046/047: qualificação, sustentabilidade, contatos internacionais,
    # certificações e digitalização — adicionados numa sessão posterior à
    # criação do modelo, por isso ficam depois dos campos originais.
    oferece_qualificacao_colaboradores: Mapped[bool | None] = mapped_column(Boolean)
    descricao_qualificacao: Mapped[str | None] = mapped_column(Text)
    adota_praticas_sustentabilidade: Mapped[bool | None] = mapped_column(Boolean)
    descricao_sustentabilidade: Mapped[str | None] = mapped_column(Text)
    possui_contatos_internacionais: Mapped[bool | None] = mapped_column(Boolean)
    descricao_contatos_internacionais: Mapped[str | None] = mapped_column(Text)
    possui_certificacoes: Mapped[bool | None] = mapped_column(Boolean)
    certificacoes: Mapped[str | None] = mapped_column(String(255))
    nivel_digitalizacao: Mapped[str | None] = mapped_column(String(100))
    # RF-010: capacidade produtiva — texto livre (volume/capacidade varia
    # demais entre tipos de negócio pra caber num campo numérico único,
    # mesmo raciocínio de `quantidade` em `AquisicaoProjeto`).
    capacidade_produtiva: Mapped[str | None] = mapped_column(Text)

    entidade: Mapped["Entidade"] = relationship()


class DiagnosticoCadastralHistorico(Base):
    """RF-046: snapshot de empregos a cada atualização do diagnóstico —
    `DiagnosticoCadastral` guarda só o valor atual (sobrescrito a cada
    resposta de campanha/importação), então sem isso "novos empregos"
    (variação no tempo) não seria calculável. Mesmo padrão de
    `IndicadorValorHistorico` (app/models/planejamento.py)."""

    __tablename__ = "diagnosticos_cadastrais_historico"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entidades.id"), nullable=False)
    empregos_diretos: Mapped[int | None] = mapped_column(Integer)
    empregos_indiretos: Mapped[int | None] = mapped_column(Integer)
    registrado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CampanhaCadastral(TimestampedBase):
    """RF-012: campanha de atualização cadastral/pesquisa diagnóstica —
    agrupa convites enviados a entidades de uma CPL para autopreencherem
    seus dados via link público (sem login)."""

    __tablename__ = "campanhas_cadastrais"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    data_inicio: Mapped[date | None] = mapped_column(Date)
    data_fim: Mapped[date | None] = mapped_column(Date)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    convites: Mapped[list["CampanhaConvite"]] = relationship(back_populates="campanha")


class CampanhaConvite(Base):
    """RF-012: convite individual de uma entidade a responder a campanha,
    identificado por token de acesso público (sem exigir login — a
    entidade convidada não necessariamente tem uma conta de usuário)."""

    __tablename__ = "campanha_convites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campanha_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campanhas_cadastrais.id")
    )
    entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entidades.id"))
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    respondido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    respondido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Envio automático do convite por e-mail (ver `app/services/
    # campanhas.py::enviar_convite_email`) — registrado no próprio convite
    # (não só logado) pra quem gere a campanha conseguir ver, revisitando a
    # tela depois, se o e-mail de fato saiu, pra quem, e por que não saiu
    # quando não saiu (sem contato cadastrado vs. falha de envio são
    # situações distintas, ambas cobertas por `email_erro`).
    email_enviado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_enviado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_destinatarios: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    email_erro: Mapped[str | None] = mapped_column(String(500), nullable=True)

    campanha: Mapped["CampanhaCadastral"] = relationship(back_populates="convites")
    entidade: Mapped["Entidade"] = relationship()


class ImportacaoLote(TimestampedBase):
    """RF-013: um lote/execução de importação de planilha — mantém a
    "trilha de origem" (arquivo, quem importou, resultado agregado)."""

    __tablename__ = "importacao_lotes"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[StatusLoteImportacao] = mapped_column(
        default=StatusLoteImportacao.CONCLUIDO, nullable=False
    )
    # RF-013: arquivo fica em staging (mesmo mecanismo de armazenamento do
    # RF-042) entre o upload e a confirmação do mapeamento de colunas;
    # mapeamento_colunas registra o que foi de fato usado (sugerido ou
    # ajustado à mão), como trilha de origem do próprio mapeamento.
    arquivo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mapeamento_colunas: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_linhas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_criadas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_atualizadas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_erros: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    linhas: Mapped[list["ImportacaoLinha"]] = relationship(back_populates="lote")


class ImportacaoLinha(Base):
    """RF-013/RF-014: resultado do processamento de uma linha da planilha —
    relatório de erros e trilha de origem por registro."""

    __tablename__ = "importacao_linhas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("importacao_lotes.id"))
    numero_linha: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StatusLinhaImportacao] = mapped_column(nullable=False)
    mensagem: Mapped[str | None] = mapped_column(Text)
    entidade_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entidades.id"), nullable=True
    )

    lote: Mapped["ImportacaoLote"] = relationship(back_populates="linhas")
    entidade: Mapped["Entidade | None"] = relationship()
