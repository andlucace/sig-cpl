import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AcaoAuditoria


class RegistroAuditoria(Base):
    """RF-056/RNF-003: trilha de auditoria imutável. Não possui
    updated_at nem endpoint de alteração/exclusão — uma vez gravado, um
    registro nunca é modificado.

    A maior parte das linhas é criada automaticamente por um listener
    `before_flush` do SQLAlchemy (app/services/auditoria.py), que captura
    toda criação/atualização/exclusão de qualquer modelo mapeado sem
    exigir chamada manual em cada endpoint. Eventos que não passam pelo
    ORM como uma escrita (autenticação, download de arquivo) são
    registrados explicitamente via `registrar_evento`."""

    __tablename__ = "registros_auditoria"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    acao: Mapped[AcaoAuditoria] = mapped_column(nullable=False)
    entidade_tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    entidade_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    cpl_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=True
    )

    descricao: Mapped[str | None] = mapped_column(Text)
    dados_anteriores: Mapped[dict | None] = mapped_column(JSONB)
    dados_novos: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(64))

    usuario: Mapped["Usuario | None"] = relationship()
