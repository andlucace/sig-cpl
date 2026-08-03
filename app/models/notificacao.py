import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TipoNotificacao


class Notificacao(Base):
    """RF-049: notificação automática de prazo/pendência para um usuário
    específico — gerada por `app/services/notificacoes.py` a partir de
    dados que outros módulos já mantêm (reuniões, tarefas, documentos,
    metas, validade de reconhecimento), nunca por coleta própria. Mesmo
    padrão "log que só acumula" de `RegistroAuditoria`/
    `IndicadorValorHistorico` — `lida`/`lida_em` capturam o único estado
    mutável."""

    __tablename__ = "notificacoes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    cpl_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=True)
    tipo: Mapped[TipoNotificacao] = mapped_column(nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    mensagem: Mapped[str | None] = mapped_column(Text)
    entidade_tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    lida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuario: Mapped["Usuario"] = relationship()
    cpl: Mapped["CPL | None"] = relationship()
