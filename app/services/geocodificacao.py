"""RF-011: geocodificação de endereço de entidade — consulta a API pública
do Nominatim (OpenStreetMap), gratuita e sem credencial, "tecnicamente
disponível" sem depender de contrato, mesmo raciocínio da consulta de CNPJ
público do RF-054 (`app/services/integracao_publica.py`). Usa
`urllib.request` da biblioteca padrão pelo mesmo motivo de lá: rotas que
chamam esta função são síncronas, então o FastAPI já roda em threadpool,
sem precisar adicionar `httpx`/`requests` como dependência nova.

Nominatim exige um User-Agent identificável e pede uso moderado (não é
serviço para geocodificação em massa) — aqui só é chamado sob demanda, uma
entidade por vez, quando alguém clica em "Geocodificar endereço"."""

import json
import urllib.error
import urllib.parse
import urllib.request

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


class GeocodificacaoIndisponivel(Exception):
    pass


def geocodificar_endereco(endereco: str | None, municipio: str | None, uf: str | None) -> dict:
    partes = [p for p in (endereco, municipio, uf and f"{uf}, Brasil") if p]
    if not partes:
        raise ValueError("Informe ao menos município/UF ou endereço para geocodificar.")

    consulta = ", ".join(partes)
    query = urllib.parse.urlencode({"q": consulta, "format": "json", "limit": 1})
    url = f"{NOMINATIM_URL}?{query}"
    requisicao = urllib.request.Request(url, headers={"User-Agent": "SIG-CPL/1.0 (contato via sistema)"})
    try:
        with urllib.request.urlopen(requisicao, timeout=10) as resposta:
            resultados = json.loads(resposta.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise GeocodificacaoIndisponivel(f"Geocodificação indisponível (HTTP {exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GeocodificacaoIndisponivel("Geocodificação indisponível no momento.") from exc

    if not resultados:
        raise GeocodificacaoIndisponivel(f"Endereço não encontrado: {consulta!r}.")

    primeiro = resultados[0]
    return {
        "latitude": float(primeiro["lat"]),
        "longitude": float(primeiro["lon"]),
        "endereco_encontrado": primeiro.get("display_name"),
    }
