import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RegistroFalha(Base):
    """RNF-012: rastreamento de falhas — uma linha por exceção não
    tratada capturada pelo handler genérico em `app/main.py` (não por
    erro de validação/RBAC/404, que são fluxo de controle esperado, só
    exceções que de fato indicam um bug ou uma dependência indisponível).
    Mesmo padrão "log que só acumula" de `RegistroAuditoria`/
    `Notificacao` — nunca é editado, só consultado pelo painel de saúde
    (`/painel/administracao/saude`)."""

    __tablename__ = "registros_falha"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    metodo: Mapped[str] = mapped_column(String(10), nullable=False)
    rota: Mapped[str] = mapped_column(String(500), nullable=False)
    tipo_excecao: Mapped[str] = mapped_column(String(255), nullable=False)
    mensagem: Mapped[str | None] = mapped_column(Text)
    traceback_resumo: Mapped[str | None] = mapped_column(Text)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    request_id: Mapped[str | None] = mapped_column(String(36))

    usuario: Mapped["Usuario | None"] = relationship()
