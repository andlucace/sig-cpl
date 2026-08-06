import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedBase
from app.models.enums import (
    DimensaoMaturidade,
    NivelMaturidade,
    StatusAvaliacao,
    StatusItemHabilitacao,
    StatusRecurso,
)


class Edital(TimestampedBase):
    """RF-024/RN-006: edição do Programa SP Produz — critérios, pesos e
    notas de corte são versionados por edital, não por CPL (é um conceito
    compartilhado entre todas as CPLs, gerido pela plataforma, não algo
    que cada CPL configura pra si)."""

    __tablename__ = "editais"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    ciclo: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    data_inicio: Mapped[date | None] = mapped_column(Date)
    data_fim: Mapped[date | None] = mapped_column(Date)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # RF-026: limiares de pontuação (0-100, mesma escala da média ponderada
    # das notas) que separam os 4 níveis de RN-004 — usados só para
    # calcular um "nível sugerido"; a decisão final é sempre humana
    # (RN-016), ver `Avaliacao.nivel_decidido`.
    limiar_cpl_em_desenvolvimento: Mapped[float | None] = mapped_column(Float)
    limiar_cpl_consolidada: Mapped[float | None] = mapped_column(Float)
    limiar_cpl_madura: Mapped[float | None] = mapped_column(Float)

    criterios: Mapped[list["CriterioMaturidade"]] = relationship(back_populates="edital")


class CriterioMaturidade(TimestampedBase):
    """RF-024/RN-006: critério de avaliação dentro de um edital, com peso
    e nota de corte próprios — a "matriz de critérios" do requisito."""

    __tablename__ = "criterios_maturidade"

    edital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("editais.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    dimensao: Mapped[DimensaoMaturidade] = mapped_column(nullable=False)
    peso: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    nota_corte: Mapped[float | None] = mapped_column(Float)

    edital: Mapped["Edital"] = relationship(back_populates="criterios")


class Avaliacao(TimestampedBase):
    """RF-024/025/026/RN-016: avaliação de maturidade de uma CPL contra um
    edital — nota por critério (`AvaliacaoCriterio`), pontuação e nível
    *sugeridos* automaticamente ao concluir, mas o nível que de fato
    atualiza `CPL.nivel_maturidade` só muda com uma decisão humana
    explícita (`nivel_decidido`), nunca pela conclusão em si."""

    __tablename__ = "avaliacoes_maturidade"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    edital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("editais.id"), nullable=False)
    status: Mapped[StatusAvaliacao] = mapped_column(default=StatusAvaliacao.EM_ANDAMENTO, nullable=False)
    avaliador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    data_avaliacao: Mapped[date] = mapped_column(Date, nullable=False)

    pontuacao_calculada: Mapped[float | None] = mapped_column(Float)
    nivel_sugerido: Mapped[NivelMaturidade | None] = mapped_column(nullable=True)

    nivel_decidido: Mapped[NivelMaturidade | None] = mapped_column(nullable=True)
    parecer: Mapped[str | None] = mapped_column(Text)
    decidido_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    data_decisao: Mapped[date | None] = mapped_column(Date)

    edital: Mapped["Edital"] = relationship()
    decidido_por: Mapped["Pessoa | None"] = relationship()
    notas: Mapped[list["AvaliacaoCriterio"]] = relationship(back_populates="avaliacao")
    recurso: Mapped["RecursoAvaliacao | None"] = relationship(back_populates="avaliacao", uselist=False)


class AvaliacaoCriterio(Base):
    """RF-025: nota e evidência de um critério específico dentro de uma
    avaliação — evidência reaproveita o repositório de Documentos (RF-042)
    já existente em vez de criar um mecanismo de anexo próprio."""

    __tablename__ = "avaliacao_criterios"
    __table_args__ = (
        UniqueConstraint("avaliacao_id", "criterio_id", name="uq_avaliacao_criterio"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    avaliacao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("avaliacoes_maturidade.id"), nullable=False
    )
    criterio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("criterios_maturidade.id"), nullable=False
    )
    nota: Mapped[float] = mapped_column(Float, nullable=False)
    evidencia_documento_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id"), nullable=True
    )
    observacao: Mapped[str | None] = mapped_column(Text)

    avaliacao: Mapped["Avaliacao"] = relationship(back_populates="notas")
    criterio: Mapped["CriterioMaturidade"] = relationship()
    evidencia_documento: Mapped["Documento | None"] = relationship()


class RecursoAvaliacao(TimestampedBase):
    """RF-027: recurso (contestação) contra o resultado de uma avaliação —
    um por avaliação. Decisão sempre de quem gere os editais
    (`ADMINISTRADOR_PLATAFORMA`), não de quem avaliou originalmente."""

    __tablename__ = "recursos_avaliacao"

    avaliacao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("avaliacoes_maturidade.id"), unique=True, nullable=False
    )
    justificativa: Mapped[str] = mapped_column(Text, nullable=False)
    solicitado_por_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    status: Mapped[StatusRecurso] = mapped_column(default=StatusRecurso.PENDENTE, nullable=False)
    parecer_decisao: Mapped[str | None] = mapped_column(Text)
    decidido_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    data_decisao: Mapped[date | None] = mapped_column(Date)

    avaliacao: Mapped["Avaliacao"] = relationship(back_populates="recurso")


class ItemHabilitacaoJuridica(TimestampedBase):
    """RF-027: item do checklist de habilitação jurídica de uma CPL
    perante um edital — etapa do fluxo de reconhecimento que precede a
    avaliação de maturidade (F05 do modelo conceitual: edital →
    habilitação → PEN → evidências de maturidade → avaliação →
    submissão → resultado → recurso), sem modelo próprio até esta
    fatia — só citada na docstring de `Avaliacao`/RF-027 como algo que
    poderia reaproveitar o repositório de Documentos.

    `descricao` é texto livre (tipo de documento exigido — CNPJ,
    estatuto social, certidão de regularidade fiscal etc.) — o
    documento de requisitos não define um checklist fechado, mesmo
    raciocínio de `eixo_sp_produz` (Projetos). `documento_id`
    reaproveita o repositório de Documentos (RF-042), mesmo padrão de
    `AvaliacaoCriterio.evidencia_documento_id`. Análise (aprovar/
    rejeitar) é sempre de quem gere os editais (`PAPEIS_EDITAL_GESTAO`),
    mesma autoridade de `RecursoAvaliacao` — é o órgão externo do
    edital validando a regularidade jurídica da CPL, não uma decisão
    interna dela."""

    __tablename__ = "itens_habilitacao_juridica"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    edital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("editais.id"), nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    obrigatorio: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    documento_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id"), nullable=True
    )
    status: Mapped[StatusItemHabilitacao] = mapped_column(default=StatusItemHabilitacao.PENDENTE, nullable=False)
    parecer: Mapped[str | None] = mapped_column(Text)
    analisado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    data_analise: Mapped[date | None] = mapped_column(Date)

    cpl: Mapped["CPL"] = relationship()
    edital: Mapped["Edital"] = relationship()
    documento: Mapped["Documento | None"] = relationship()
    analisado_por: Mapped["Usuario | None"] = relationship()
