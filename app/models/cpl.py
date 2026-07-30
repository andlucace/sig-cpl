import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import NivelMaturidade


class CPL(TimestampedBase):
    """RF-001 / seção 10: Cadeia Produtiva Local — identificação, setor,
    território, entidade gestora, reconhecimento, nível e vigência.
    Cada CPL mantém isolamento lógico de dados e parâmetros (multi-tenant)."""

    __tablename__ = "cpls"

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    sigla: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    setor: Mapped[str | None] = mapped_column(String(255))
    municipio: Mapped[str | None] = mapped_column(String(255))
    uf: Mapped[str | None] = mapped_column(String(2))

    entidade_gestora_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entidades.id"), nullable=True
    )

    nivel_maturidade: Mapped[NivelMaturidade | None] = mapped_column(
        nullable=True
    )
    data_reconhecimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_validade_reconhecimento: Mapped[date | None] = mapped_column(Date, nullable=True)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    entidade_gestora: Mapped["Entidade | None"] = relationship(
        foreign_keys=[entidade_gestora_id]
    )
