import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import StatusEvento, TipoEvento


class Evento(TimestampedBase):
    """RF-050: capacitação, mentoria, missão técnica ou evento genérico do
    Programa SP Produz — mesmo raciocínio de `Edital` (RN-006): conteúdo
    compartilhado, gerido pela plataforma, não algo que cada CPL precisa
    recriar por conta própria. `cpl_id` nulo é um evento aberto a todas as
    CPLs (gerido por `PAPEIS_EDITAL_GESTAO`, como um `Edital`); `cpl_id`
    preenchido é um evento local de uma CPL específica (gerido por
    `PAPEIS_GESTAO` daquela CPL — ex.: uma capacitação interna)."""

    __tablename__ = "eventos"

    cpl_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoEvento] = mapped_column(nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    data_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    local: Mapped[str | None] = mapped_column(String(255))
    vagas: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[StatusEvento] = mapped_column(default=StatusEvento.AGENDADO, nullable=False)
    criado_por_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    cpl: Mapped["CPL | None"] = relationship()
    inscricoes: Mapped[list["InscricaoEvento"]] = relationship(back_populates="evento")


class InscricaoEvento(TimestampedBase):
    """RF-050: inscrição, presença e avaliação de uma pessoa num evento —
    as três fases do requisito ficam num único registro por pessoa+evento
    em vez de três tabelas separadas, porque são estados sucessivos do
    mesmo vínculo (inscrita → presente/ausente → avaliação), não
    entidades independentes. `presente` fica `None` até alguém marcar
    (diferente de `Presenca.presente` em Governança, que é sempre
    preenchido na criação — ali o registro só existe depois da reunião
    acontecer; aqui a inscrição existe antes do evento, então `created_at`
    já serve como data de inscrição). `cpl_id` registra em nome de qual
    CPL a pessoa foi inscrita, útil pra relatório mesmo quando o evento em
    si é aberto a todas (`cpl_id` nulo no `Evento`)."""

    __tablename__ = "inscricoes_evento"
    __table_args__ = (UniqueConstraint("evento_id", "pessoa_id", name="uq_inscricao_evento_pessoa"),)

    evento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("eventos.id"), nullable=False)
    pessoa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=False)
    cpl_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=True)

    presente: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    nota_avaliacao: Mapped[int | None] = mapped_column(SmallInteger)
    comentario_avaliacao: Mapped[str | None] = mapped_column(Text)

    evento: Mapped["Evento"] = relationship(back_populates="inscricoes")
    pessoa: Mapped["Pessoa"] = relationship()
    cpl: Mapped["CPL | None"] = relationship()
