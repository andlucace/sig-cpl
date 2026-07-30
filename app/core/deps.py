import uuid

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.usuario import Usuario

COOKIE_NAME = "sigcpl_access_token"


def extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:]
    return request.cookies.get(COOKIE_NAME)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """Resolve o usuário autenticado a partir do cookie de sessão (portal
    restrito via HTMX) ou de um Bearer token (consumo via API, RF-053)."""

    token = extract_token(request)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou sessão expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.get(Usuario, uuid.UUID(user_id))
    if user is None or not user.ativo:
        raise credentials_exception
    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Usuario | None:
    """Mesma resolução de get_current_user, mas sem levantar exceção —
    útil para o portal público (RF-002), que exibe conteúdo distinto para
    visitantes autenticados sem exigir login."""

    try:
        return get_current_user(request, db)
    except HTTPException:
        return None
