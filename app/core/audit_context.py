import uuid
from contextvars import ContextVar

usuario_atual_id: ContextVar[uuid.UUID | None] = ContextVar("usuario_atual_id", default=None)
ip_atual: ContextVar[str | None] = ContextVar("ip_atual", default=None)
