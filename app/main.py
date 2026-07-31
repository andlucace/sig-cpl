import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import (
    auditoria,
    auth,
    cadastro_dinamico,
    cpl,
    documentos,
    entidades,
    governanca,
    indicadores,
    maturidade,
    pessoas,
    planejamento,
    usuario_papel,
)
from app.api.routes.stubs import stub_routers
from app.core.audit_context import ip_atual, usuario_atual_id
from app.core.config import get_settings
from app.core.deps import extract_token
from app.core.security import decode_access_token
from app.services import auditoria as auditoria_service  # noqa: F401 — registra o listener de auditoria
from app.web import (
    routes_atualizacao_publica,
    routes_auditoria,
    routes_cadastro,
    routes_cpl,
    routes_documentos,
    routes_governanca,
    routes_indicadores,
    routes_maturidade,
    routes_planejamento,
    routes_publico,
    routes_restrito,
)
from app.web.templates import templates

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Sistema Integrado de Gestão de Cadeia Produtiva Local — referência Programa SP Produz.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.exception_handler(StarletteHTTPException)
async def tratar_http_exception(request: Request, exc: StarletteHTTPException):
    """RBAC (seção "Controle de acesso"): um 403 de `verificar_papel` por
    padrão vira JSON cru mesmo em navegação direta no portal web. Aqui
    trocamos por uma página amigável — mas só para GET de página inteira,
    não para chamadas de API (`/api/...`, RF-053) nem para requisições
    HTMX (que não fazem swap em resposta não-2xx de qualquer forma, então
    devolver a página inteira quebraria o fragmento esperado)."""

    e_rota_api = request.url.path.startswith("/api/")
    e_htmx = request.headers.get("HX-Request") == "true"
    if exc.status_code == status.HTTP_403_FORBIDDEN and not e_rota_api and not e_htmx:
        return templates.TemplateResponse(
            request, "erro_403.html", {"detalhe": exc.detail}, status_code=status.HTTP_403_FORBIDDEN
        )
    return JSONResponse(
        {"detail": exc.detail}, status_code=exc.status_code, headers=getattr(exc, "headers", None)
    )


@app.middleware("http")
async def contexto_auditoria(request: Request, call_next):
    """Popula os contextvars lidos pelo listener de auditoria
    (app/services/auditoria.py) com o usuário autenticado e o IP de cada
    requisição — decodifica o token localmente, sem consultar o banco,
    para manter o middleware leve."""

    usuario_id = None
    token = extract_token(request)
    if token:
        try:
            payload = decode_access_token(token)
            usuario_id = uuid.UUID(payload["sub"])
        except (JWTError, ValueError, KeyError, TypeError):
            usuario_id = None

    token_usuario = usuario_atual_id.set(usuario_id)
    token_ip = ip_atual.set(request.client.host if request.client else None)
    try:
        return await call_next(request)
    finally:
        usuario_atual_id.reset(token_usuario)
        ip_atual.reset(token_ip)


# API (RF-053: exposta em /api para consumo programático e integrações)
app.include_router(auth.router, prefix="/api")
app.include_router(cpl.router, prefix="/api")
app.include_router(entidades.router, prefix="/api")
app.include_router(entidades.cpl_router, prefix="/api")
app.include_router(pessoas.router, prefix="/api")
app.include_router(usuario_papel.router, prefix="/api")
app.include_router(governanca.router, prefix="/api")
app.include_router(planejamento.router, prefix="/api")
app.include_router(cadastro_dinamico.router, prefix="/api")
app.include_router(documentos.router, prefix="/api")
app.include_router(auditoria.router, prefix="/api")
app.include_router(indicadores.router, prefix="/api")
app.include_router(maturidade.router, prefix="/api")
for stub_router in stub_routers:
    app.include_router(stub_router, prefix="/api")

# Portal restrito (HTMX), autopreenchimento público por token e portal público
app.include_router(routes_restrito.router)
app.include_router(routes_cpl.router)
app.include_router(routes_governanca.router)
app.include_router(routes_planejamento.router)
app.include_router(routes_cadastro.router)
app.include_router(routes_documentos.router)
app.include_router(routes_auditoria.router)
app.include_router(routes_indicadores.router)
app.include_router(routes_maturidade.router)
app.include_router(routes_atualizacao_publica.router)
app.include_router(routes_publico.router)


@app.get("/api/saude", tags=["Administração"])
def saude() -> dict:
    """Endpoint simples de verificação de disponibilidade (apoia RNF-004/RNF-012)."""
    return {"status": "ok", "app": settings.app_name, "ambiente": settings.environment}
