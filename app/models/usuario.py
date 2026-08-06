import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedBase
from app.models.enums import Papel


class Usuario(TimestampedBase):
    """RF-004: conta de acesso autenticável por e-mail e senha, com suporte
    a MFA para perfis críticos (mfa_enabled) e vínculo opcional a uma Pessoa.

    `mfa_secret` (segredo TOTP em base32) fica setado assim que o usuário
    inicia a configuração, mas só passa a valer (`mfa_enabled=True`) depois
    de confirmar um código válido — evita travar o próprio login com um
    segredo que o usuário nunca chegou a cadastrar no autenticador.
    `mfa_backup_codes` guarda só o hash (bcrypt) de cada código de
    recuperação de uso único, nunca o texto puro — mesmo padrão de
    `hashed_password`. Ambos os campos são redigidos na trilha de
    auditoria (`_CAMPOS_REDIGIDOS` em `app/services/auditoria.py`)."""

    __tablename__ = "usuarios"

    pessoa_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mfa_backup_codes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
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


class TokenRecuperacaoSenha(TimestampedBase):
    """RF-004: token de uso único para redefinição de senha via e-mail.
    Curta validade (`expira_em`, configurável em
    `settings.password_reset_token_expire_minutes`) e `usado_em` marca
    consumo — nunca reutilizável, mesmo dentro da janela de validade."""

    __tablename__ = "tokens_recuperacao_senha"

    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    usuario: Mapped["Usuario"] = relationship()
