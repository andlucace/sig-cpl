import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedBase
from app.models.enums import Elo, TipoEntidade

if TYPE_CHECKING:
    from app.models.cpl import CPL


class Entidade(TimestampedBase):
    """RF-006/RF-008: empresa, órgão, associação, universidade, ICT, startup,
    fornecedor ou ambiente de inovação. Uma entidade pode se vincular a mais
    de uma CPL (RN-003), tratada via EntidadeCPL."""

    __tablename__ = "entidades"

    tipo: Mapped[TipoEntidade] = mapped_column(nullable=False)
    razao_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nome_fantasia: Mapped[str | None] = mapped_column(String(255))

    cnpj: Mapped[str | None] = mapped_column(String(20), index=True)
    cpf: Mapped[str | None] = mapped_column(String(14), index=True)
    cnae: Mapped[str | None] = mapped_column(String(20))
    porte: Mapped[str | None] = mapped_column(String(50))

    municipio: Mapped[str | None] = mapped_column(String(255))
    uf: Mapped[str | None] = mapped_column(String(2))
    endereco: Mapped[str | None] = mapped_column(String(500))

    situacao_cadastral: Mapped[str | None] = mapped_column(String(100))
    canais_digitais: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EntidadeCPL(Base):
    """Associação N:N entre Entidade e CPL (RN-003), registrando o vínculo
    e permitindo que a mesma organização participe de múltiplas CPLs com
    permissões e dados tratados por vínculo."""

    __tablename__ = "entidade_cpl"
    __table_args__ = (UniqueConstraint("entidade_id", "cpl_id", name="uq_entidade_cpl"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entidades.id"))
    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"))
    data_vinculo: Mapped[date] = mapped_column(Date, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    entidade: Mapped["Entidade"] = relationship()
    cpl: Mapped["CPL"] = relationship()


class EntidadeElo(Base):
    """RF-009: classifica cada ator nos elos da cadeia, admitindo múltiplos
    elos por entidade dentro de uma mesma CPL."""

    __tablename__ = "entidade_elo"
    __table_args__ = (
        UniqueConstraint("entidade_id", "cpl_id", "elo", name="uq_entidade_cpl_elo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entidades.id"))
    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"))
    elo: Mapped[Elo] = mapped_column(nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
