import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedBase
from app.models.enums import Elo, PrazoObjetivo, StatusPlanejamento, StatusTarefa, TipoDiagnostico


class PlanejamentoEstrategico(TimestampedBase):
    """RF-021: Planejamento Estratégico de Negócios (PEN) de uma CPL — um
    registro por ciclo de planejamento. As seções "cadeia" e "governança"
    citadas no requisito não são duplicadas aqui como texto livre: já são
    cobertas pelos módulos de Cadastro/Cadeia (Entidade/Elo) e Governança."""

    __tablename__ = "planejamentos_estrategicos"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    ciclo: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[StatusPlanejamento] = mapped_column(default=StatusPlanejamento.RASCUNHO, nullable=False)
    caracterizacao: Mapped[str | None] = mapped_column(Text)
    historico: Mapped[str | None] = mapped_column(Text)
    mercado: Mapped[str | None] = mapped_column(Text)
    inovacao: Mapped[str | None] = mapped_column(Text)
    impactos: Mapped[str | None] = mapped_column(Text)
    internacionalizacao: Mapped[str | None] = mapped_column(Text)
    data_aprovacao: Mapped[date | None] = mapped_column(Date)

    diagnosticos: Mapped[list["DiagnosticoItem"]] = relationship(back_populates="planejamento")
    objetivos: Mapped[list["ObjetivoEstrategico"]] = relationship(back_populates="planejamento")


class DiagnosticoItem(Base):
    """RF-022: item de diagnóstico — SWOT, problema prioritário, demanda ou
    lacuna de elo identificada na análise da cadeia."""

    __tablename__ = "diagnostico_itens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    planejamento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("planejamentos_estrategicos.id")
    )
    tipo: Mapped[TipoDiagnostico] = mapped_column(nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    elo_relacionado: Mapped[Elo | None] = mapped_column(nullable=True)
    prioridade: Mapped[int | None] = mapped_column()

    planejamento: Mapped["PlanejamentoEstrategico"] = relationship(back_populates="diagnosticos")


class ObjetivoEstrategico(TimestampedBase):
    """RF-023: objetivo estratégico — hub que agrega metas, iniciativas e
    indicadores associados a um horizonte de prazo e orçamento estimado."""

    __tablename__ = "objetivos_estrategicos"

    planejamento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("planejamentos_estrategicos.id")
    )
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    prazo: Mapped[PrazoObjetivo] = mapped_column(nullable=False)
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    orcamento_estimado: Mapped[float | None] = mapped_column(Float)
    status: Mapped[StatusTarefa] = mapped_column(default=StatusTarefa.PENDENTE, nullable=False)

    planejamento: Mapped["PlanejamentoEstrategico"] = relationship(back_populates="objetivos")
    responsavel: Mapped["Pessoa | None"] = relationship()
    metas: Mapped[list["MetaEstrategica"]] = relationship(back_populates="objetivo")
    iniciativas: Mapped[list["IniciativaEstrategica"]] = relationship(back_populates="objetivo")
    indicadores: Mapped[list["IndicadorEstrategico"]] = relationship(back_populates="objetivo")


class MetaEstrategica(TimestampedBase):
    """RF-023/RN-010: meta com tipo, valor-alvo, prazo, responsável, método
    de aferição e evidência — todos os campos exigidos pela regra de negócio."""

    __tablename__ = "metas_estrategicas"

    objetivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("objetivos_estrategicos.id")
    )
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    valor_alvo: Mapped[str] = mapped_column(String(255), nullable=False)
    metodo_afericao: Mapped[str | None] = mapped_column(Text)
    prazo: Mapped[date | None] = mapped_column(Date)
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    evidencia: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusTarefa] = mapped_column(default=StatusTarefa.PENDENTE, nullable=False)

    objetivo: Mapped["ObjetivoEstrategico"] = relationship(back_populates="metas")
    responsavel: Mapped["Pessoa | None"] = relationship()


class IniciativaEstrategica(TimestampedBase):
    """RF-023: ação/iniciativa concreta para viabilizar o objetivo."""

    __tablename__ = "iniciativas_estrategicas"

    objetivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("objetivos_estrategicos.id")
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    prazo: Mapped[date | None] = mapped_column(Date)
    status: Mapped[StatusTarefa] = mapped_column(default=StatusTarefa.PENDENTE, nullable=False)

    objetivo: Mapped["ObjetivoEstrategico"] = relationship(back_populates="iniciativas")
    responsavel: Mapped["Pessoa | None"] = relationship()


class IndicadorEstrategico(TimestampedBase):
    """RF-023 (e base para o catálogo mais amplo do RF-044): indicador de
    acompanhamento de um objetivo, com fórmula, meta e valor atual."""

    __tablename__ = "indicadores_estrategicos"

    objetivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("objetivos_estrategicos.id")
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    formula: Mapped[str | None] = mapped_column(Text)
    unidade: Mapped[str | None] = mapped_column(String(50))
    meta_valor: Mapped[str | None] = mapped_column(String(255))
    valor_atual: Mapped[str | None] = mapped_column(String(255))
    periodicidade: Mapped[str | None] = mapped_column(String(100))

    objetivo: Mapped["ObjetivoEstrategico"] = relationship(back_populates="indicadores")
