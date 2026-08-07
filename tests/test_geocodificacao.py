"""RF-011: geocodificação e mapa da cadeia. Os testes do serviço em si
não fazem chamada de rede de verdade (`monkeypatch` no `urlopen`) — CI
não deveria depender de um serviço externo pra passar/falhar. Os testes
de rota que envolvem geocodificação também usam monkeypatch; o mapa e a
localização manual não dependem de rede nenhuma."""

import json
from unittest.mock import MagicMock

import pytest
from conftest import criar_usuario_com_papel, login_como

from app.models.enums import Papel
from app.services import geocodificacao
from app.services.geocodificacao import GeocodificacaoIndisponivel, geocodificar_endereco


def test_geocodificar_sem_nenhum_dado_levanta_value_error():
    with pytest.raises(ValueError):
        geocodificar_endereco(None, None, None)


def test_geocodificar_endereco_sucesso(monkeypatch):
    resposta_falsa = MagicMock()
    resposta_falsa.read.return_value = json.dumps(
        [{"lat": "-23.1177393", "lon": "-46.5547861", "display_name": "Atibaia, SP, Brasil"}]
    ).encode("utf-8")
    resposta_falsa.__enter__.return_value = resposta_falsa

    monkeypatch.setattr(geocodificacao.urllib.request, "urlopen", lambda *a, **k: resposta_falsa)

    resultado = geocodificar_endereco(None, "Atibaia", "SP")
    assert resultado["latitude"] == pytest.approx(-23.1177393)
    assert resultado["longitude"] == pytest.approx(-46.5547861)


def test_geocodificar_endereco_nao_encontrado(monkeypatch):
    resposta_falsa = MagicMock()
    resposta_falsa.read.return_value = b"[]"
    resposta_falsa.__enter__.return_value = resposta_falsa
    monkeypatch.setattr(geocodificacao.urllib.request, "urlopen", lambda *a, **k: resposta_falsa)

    with pytest.raises(GeocodificacaoIndisponivel):
        geocodificar_endereco(None, "Lugar Que Nao Existe De Verdade", "SP")


def test_definir_localizacao_manual(admin_client):
    entidade_id = admin_client.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": "Empresa Geolocalizada"}
    ).json()["id"]

    resposta = admin_client.patch(
        f"/api/entidades/{entidade_id}/localizacao", json={"latitude": -23.11, "longitude": -46.55}
    )
    assert resposta.status_code == 200
    assert resposta.json()["latitude"] == pytest.approx(-23.11)
    assert resposta.json()["longitude"] == pytest.approx(-46.55)


def test_mapa_da_cpl_so_lista_entidades_geocodificadas(admin_client):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": "CPL Mapa", "sigla": "CPL-MAPA-01"}
    ).json()["id"]

    com_geo = admin_client.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": "Com Geolocalizacao"}
    ).json()["id"]
    sem_geo = admin_client.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": "Sem Geolocalizacao"}
    ).json()["id"]

    admin_client.post(f"/api/cpls/{cpl_id}/entidades/{com_geo}/vinculo")
    admin_client.post(f"/api/cpls/{cpl_id}/entidades/{sem_geo}/vinculo")
    admin_client.patch(f"/api/entidades/{com_geo}/localizacao", json={"latitude": -23.1, "longitude": -46.5})

    resposta = admin_client.get(f"/api/cpls/{cpl_id}/mapa")
    assert resposta.status_code == 200
    ids_no_mapa = {e["id"] for e in resposta.json()}
    assert ids_no_mapa == {com_geo}


def test_geocodificar_via_api_usa_endereco_cadastrado(admin_client, monkeypatch):
    from app.api.routes import entidades as rota_entidades

    monkeypatch.setattr(
        rota_entidades,
        "geocodificar_endereco",
        lambda endereco, municipio, uf: {"latitude": -22.95, "longitude": -46.54, "endereco_encontrado": "x"},
    )
    entidade_id = admin_client.post(
        "/api/entidades",
        json={"tipo": "empresa", "razao_social": "Empresa a Geocodificar", "municipio": "Braganca Paulista", "uf": "SP"},
    ).json()["id"]

    resposta = admin_client.post(f"/api/entidades/{entidade_id}/geocodificar")
    assert resposta.status_code == 200
    assert resposta.json()["latitude"] == pytest.approx(-22.95)


def test_geocodificar_exige_papel_gestao(client, db_session):
    leitor = criar_usuario_com_papel(db_session, Papel.CONSELHO_COMITE)
    client_leitor = login_como(client, leitor)
    resposta = client_leitor.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": "Nao deveria criar"}
    )
    # CONSELHO_COMITE não está em PAPEIS_GESTAO — nem chega a criar a entidade
    assert resposta.status_code == 403
