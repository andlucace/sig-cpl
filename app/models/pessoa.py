import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedBase
from app.models.enums import Papel


class Pessoa(TimestampedBase):
    """RF-007: pessoa física — representante, contato ou membro vinculado
    a uma ou mais entidades/CPLs, com histórico de vigência via PessoaVinculo."""

    __tablename__ = "pessoas"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cpf: Mapped[str | None] = mapped_column(String(14), index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    telefone: Mapped[str | None] = mapped_column(String(30))
    whatsapp: Mapped[str | None] = mapped_column(String(30))


class PessoaVinculo(Base):
    """RF-007: vínculo de uma pessoa com uma entidade e/ou CPL, com papel,
    cargo e período de vigência (data_inicio/data_fim)."""

    __tablename__ = "pessoa_vinculo"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pessoa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pessoas.id"))
    entidade_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entidades.id"), nullable=True
    )
    cpl_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=True
    )
    papel: Mapped[Papel] = mapped_column(nullable=False)
    cargo: Mapped[str | None] = mapped_column(String(255))
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date | None] = mapped_column(Date, nullable=True)

    pessoa: Mapped["Pessoa"] = relationship()
