from fastapi import APIRouter, Request

from app.web.templates import templates

router = APIRouter(tags=["Portal público"])


@router.get("/")
def home(request: Request):
    """RF-002/RF-055: portal público de transparência — nesta versão inicial
    exibe apenas uma página institucional estática, sem dados agregados
    (indicadores públicos ficam para a Fase 3, conforme roadmap)."""

    return templates.TemplateResponse(request, "publico/home.html", {})
