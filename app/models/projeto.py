import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import EstagioProjeto, OrigemDemanda, PrioridadeProjeto, StatusDemanda


class DemandaProjeto(TimestampedBase):
    """RF-031: demanda coletiva ou oportunidade de projeto, registrada
    antes de virar um `Projeto` formal — guarda de onde veio (empresa,
    comissão, instituição ou edital de fomento). `origem_id` é uma
    referência solta (sem FK de banco), mesmo padrão de
    `RegistroAuditoria.entidade_id` — a origem pode apontar pra tabelas
    diferentes conforme `origem_tipo`, então não dá pra usar uma única
    FK rígida."""

    __tablename__ = "demandas_projeto"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    origem_tipo: Mapped[OrigemDemanda] = mapped_column(nullable=False)
    origem_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    origem_detalhe: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[StatusDemanda] = mapped_column(default=StatusDemanda.REGISTRADA, nullable=False)
    registrado_por_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    projeto: Mapped["Projeto | None"] = relationship(back_populates="demanda_origem", uselist=False)


class Projeto(TimestampedBase):
    """RF-032: projeto no portfólio de uma CPL — prioridade, estágio,
    eixo do Programa SP Produz e vínculo ao planejamento estratégico.
    RF-033 (informações básicas do plano de trabalho — introdução,
    objeto, objetivos, justificativa, impactos) mora nos mesmos campos
    da tabela, sem uma entidade `PlanoDeTrabalho` separada — é 1:1 com
    o projeto, não haveria ganho em separar. Etapas/cronograma/
    resultados/indicadores (RF-034), equipe/aquisições/recursos
    (RF-035), financeiro (RF-036 a RF-038) e execução (RF-039/040)
    ficam para as próximas fatias deste módulo.

    `eixo_sp_produz` é texto livre, não um enum fechado — o documento de
    requisitos não define a lista de eixos do programa."""

    __tablename__ = "projetos"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    demanda_origem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("demandas_projeto.id"), unique=True, nullable=True
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    eixo_sp_produz: Mapped[str | None] = mapped_column(String(150))
    estagio: Mapped[EstagioProjeto] = mapped_column(default=EstagioProjeto.DEMANDA, nullable=False)
    prioridade: Mapped[PrioridadeProjeto] = mapped_column(default=PrioridadeProjeto.MEDIA, nullable=False)
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    objetivo_estrategico_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("objetivos_estrategicos.id"), nullable=True
    )
    # RF-033: informações básicas do plano de trabalho.
    introducao: Mapped[str | None] = mapped_column(Text)
    objeto: Mapped[str | None] = mapped_column(Text)
    objetivos: Mapped[str | None] = mapped_column(Text)
    justificativa: Mapped[str | None] = mapped_column(Text)
    impactos: Mapped[str | None] = mapped_column(Text)

    demanda_origem: Mapped["DemandaProjeto | None"] = relationship(back_populates="projeto")
    responsavel: Mapped["Pessoa | None"] = relationship()
    objetivo_estrategico: Mapped["ObjetivoEstrategico | None"] = relationship()
