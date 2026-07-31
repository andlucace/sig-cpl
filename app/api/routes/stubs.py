from fastapi import APIRouter, status

# Módulos previstos na seção 7 (Visão macro da solução) ainda não
# implementados neste esqueleto inicial. Cada um vira um router próprio
# para já reservar o prefixo/tag na API e no OpenAPI, facilitando a
# evolução incremental descrita no roadmap (seção 17).
_MODULOS_PENDENTES = [
    ("projetos", "Projetos e fomento", "Fase 2/3 — portfólio, plano de trabalho, orçamento e execução (RF-029 a RF-041)."),
    ("comunicacao", "Comunicação e conhecimento", "Fase 1/3 — notificações, eventos e biblioteca (RF-049 a RF-051)."),
    ("integracoes", "Integrações", "Fase 3/4 — API, importação/exportação e conectores externos (RF-052 a RF-054)."),
]
# "maturidade" (RF-024 a RF-028) e "indicadores" (RF-044 a RF-048) saíram
# desta lista — já têm router de verdade (app/api/routes/maturidade.py,
# app/api/routes/indicadores.py), não fazia sentido conviver com um stub
# 501 sob o mesmo prefixo.


def _make_stub_router(prefix: str, tag: str, roadmap: str) -> APIRouter:
    router = APIRouter(prefix=f"/{prefix}", tags=[tag])

    @router.get("", status_code=status.HTTP_501_NOT_IMPLEMENTED)
    def status_modulo() -> dict:
        return {
            "modulo": tag,
            "status": "ainda não implementado neste esqueleto",
            "roadmap": roadmap,
        }

    return router


stub_routers: list[APIRouter] = [
    _make_stub_router(prefix, tag, roadmap) for prefix, tag, roadmap in _MODULOS_PENDENTES
]
