import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text, func
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
    """RF-023/RF-044 (catálogo de indicadores, RN-011): indicador de
    acompanhamento de um objetivo, com fórmula, fonte de dados, meta,
    responsável e valor atual — série histórica em `IndicadorValorHistorico`."""

    __tablename__ = "indicadores_estrategicos"

    objetivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("objetivos_estrategicos.id")
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    formula: Mapped[str | None] = mapped_column(Text)
    fonte: Mapped[str | None] = mapped_column(String(255))
    unidade: Mapped[str | None] = mapped_column(String(50))
    meta_valor: Mapped[str | None] = mapped_column(String(255))
    valor_atual: Mapped[str | None] = mapped_column(String(255))
    periodicidade: Mapped[str | None] = mapped_column(String(100))
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )

    objetivo: Mapped["ObjetivoEstrategico"] = relationship(back_populates="indicadores")
    responsavel: Mapped["Pessoa | None"] = relationship()
    valores_historico: Mapped[list["IndicadorValorHistorico"]] = relationship(
        back_populates="indicador", order_by="IndicadorValorHistorico.data_referencia"
    )


class IndicadorValorHistorico(Base):
    """RF-044: série histórica do indicador — cada aferição registrada fica
    preservada aqui, em vez de só sobrescrever `valor_atual`."""

    __tablename__ = "indicador_valores_historico"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("indicadores_estrategicos.id"), nullable=False
    )
    data_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    valor: Mapped[str] = mapped_column(String(255), nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text)
    registrado_por_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    registrado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    indicador: Mapped["IndicadorEstrategico"] = relationship(back_populates="valores_historico")
