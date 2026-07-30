import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedBase
from app.models.enums import Papel


class Usuario(TimestampedBase):
    """RF-004: conta de acesso autenticável por e-mail e senha, com suporte
    a MFA para perfis críticos (mfa_enabled) e vínculo opcional a uma Pessoa."""

    __tablename__ = "usuarios"

    pessoa_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    pessoa: Mapped["Pessoa | None"] = relationship()
    papeis: Mapped[list["UsuarioPapel"]] = relationship(back_populates="usuario")


class UsuarioPapel(Base):
    """RF-005: controle de acesso por papéis, escopado opcionalmente por CPL
    ou entidade — permite que o mesmo usuário tenha papéis diferentes em
    contextos diferentes (ex.: gestor de projeto em uma CPL, membro em outra)."""

    __tablename__ = "usuario_papel"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    papel: Mapped[Papel] = mapped_column(nullable=False)
    cpl_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=True
    )
    entidade_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entidades.id"), nullable=True
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="papeis")
