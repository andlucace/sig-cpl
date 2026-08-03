from fastapi import APIRouter, status

# Módulos previstos na seção 7 (Visão macro da solução) ainda não
# implementados neste esqueleto inicial. Cada um vira um router próprio
# para já reservar o prefixo/tag na API e no OpenAPI, facilitando a
# evolução incremental descrita no roadmap (seção 17).
_MODULOS_PENDENTES = [
    ("comunicacao", "Comunicação e conhecimento", "Fase 1/3 — eventos e biblioteca (RF-050/051)."),
    ("integracoes", "Integrações", "Fase 3/4 — API, importação/exportação e conectores externos (RF-052 a RF-054)."),
]
# "maturidade" (RF-024 a RF-028), "indicadores" (RF-044 a RF-048) e
# "projetos" (RF-031/032 — só a fundação: demandas e portfólio, ainda
# falta plano de trabalho/financeiro/execução/prestação de contas)
# saíram desta lista — já têm router de verdade, não fazia sentido
# conviver com um stub 501 sob o mesmo prefixo. "notificacoes" (RF-049)
# nunca precisou entrar aqui — o router de verdade já nasceu direto.


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
