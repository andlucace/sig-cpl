"""Estados/municípios do Brasil pro formulário de CPL (IBGE) — testes do
serviço não fazem chamada de rede de verdade (`monkeypatch` no
`urlopen`), mesmo raciocínio de `test_geocodificacao.py`. `estados()`/
`municipios_do_estado()` são `lru_cache`d — cada teste limpa o cache
antes de rodar, senão o resultado do primeiro teste da suíte "vaza" pros
demais (a função nem seria chamada de novo)."""

import gzip
import json
import urllib.error
from unittest.mock import MagicMock

import pytest
from conftest import criar_usuario_com_papel, login_como

from app.models.enums import Papel
from app.services import localidades
from app.services.localidades import _UFS_RESERVA, estados, municipios_do_estado
from app.web import routes_cpl


@pytest.fixture(autouse=True)
def _limpar_cache():
    estados.cache_clear()
    municipios_do_estado.cache_clear()
    yield
    estados.cache_clear()
    municipios_do_estado.cache_clear()


def _resposta_falsa(corpo: dict | list, gzipada: bool = False) -> MagicMock:
    bruto = json.dumps(corpo).encode("utf-8")
    resposta = MagicMock()
    if gzipada:
        resposta.read.return_value = gzip.compress(bruto)
        resposta.headers.get.return_value = "gzip"
    else:
        resposta.read.return_value = bruto
        resposta.headers.get.return_value = None
    resposta.__enter__.return_value = resposta
    return resposta


def test_estados_sucesso(monkeypatch):
    dados = [{"sigla": "SP", "nome": "São Paulo"}, {"sigla": "AC", "nome": "Acre"}]
    monkeypatch.setattr(
        localidades.urllib.request, "urlopen", lambda *a, **k: _resposta_falsa(dados)
    )
    assert estados() == [("SP", "São Paulo"), ("AC", "Acre")]


def test_estados_descomprime_gzip(monkeypatch):
    """Regressão: o IBGE sempre manda `Content-Encoding: gzip`, mesmo sem
    o cliente pedir — `urllib` não descomprime sozinho."""

    dados = [{"sigla": "RJ", "nome": "Rio de Janeiro"}]
    monkeypatch.setattr(
        localidades.urllib.request, "urlopen", lambda *a, **k: _resposta_falsa(dados, gzipada=True)
    )
    assert estados() == [("RJ", "Rio de Janeiro")]


def test_estados_cai_para_reserva_em_erro(monkeypatch):
    def _levanta_erro(*a, **k):
        raise urllib.error.URLError("sem rede")

    monkeypatch.setattr(localidades.urllib.request, "urlopen", _levanta_erro)
    assert estados() == _UFS_RESERVA
    assert len(estados()) == 27


def test_municipios_do_estado_sucesso(monkeypatch):
    dados = [{"nome": "Atibaia"}, {"nome": "Bragança Paulista"}]
    monkeypatch.setattr(
        localidades.urllib.request, "urlopen", lambda *a, **k: _resposta_falsa(dados)
    )
    assert municipios_do_estado("SP") == ["Atibaia", "Bragança Paulista"]


def test_municipios_do_estado_erro_retorna_lista_vazia(monkeypatch):
    def _levanta_erro(*a, **k):
        raise urllib.error.URLError("sem rede")

    monkeypatch.setattr(localidades.urllib.request, "urlopen", _levanta_erro)
    assert municipios_do_estado("SP") == []


def test_estados_usa_cache_na_segunda_chamada(monkeypatch):
    chamadas = {"total": 0}

    def _urlopen_contando(*a, **k):
        chamadas["total"] += 1
        return _resposta_falsa([{"sigla": "SP", "nome": "São Paulo"}])

    monkeypatch.setattr(localidades.urllib.request, "urlopen", _urlopen_contando)
    estados()
    estados()
    assert chamadas["total"] == 1


# --- Rotas web (mockando o serviço no ponto de uso, mesmo padrão de
# test_geocodificacao.py) -------------------------------------------------


def test_pagina_criacao_cpl_mostra_selects(admin_client, monkeypatch):
    monkeypatch.setattr(routes_cpl, "estados", lambda: [("SP", "São Paulo")])
    resposta = admin_client.get("/painel/cpls")
    assert resposta.status_code == 200
    assert 'name="uf"' in resposta.text
    assert 'name="setor"' in resposta.text
    assert 'name="municipio"' in resposta.text
    assert "São Paulo" in resposta.text


def test_fragment_municipios_retorna_lista_da_uf(admin_client, monkeypatch):
    monkeypatch.setattr(routes_cpl, "municipios_do_estado", lambda uf: [f"Cidade de {uf}"])
    resposta = admin_client.get("/painel/cpls/municipios-fragment?uf=RJ")
    assert resposta.status_code == 200
    assert "Cidade de RJ" in resposta.text


def test_fragment_municipios_exige_login(client):
    resposta = client.get(
        "/painel/cpls/municipios-fragment?uf=RJ", follow_redirects=False
    )
    assert resposta.status_code == 303


def test_criar_cpl_grava_municipio_e_uf(admin_client):
    resposta = admin_client.post(
        "/painel/cpls",
        data={
            "nome": "CPL Localidades Teste",
            "sigla": "CPL-LOCAL-01",
            "setor": "",
            "setor_outro": "",
            "municipio": "Atibaia",
            "uf": "sp",
        },
        follow_redirects=False,
    )
    assert resposta.status_code == 303
    cpl_id = resposta.headers["location"].rsplit("/", 1)[-1]
    cpl = admin_client.get(f"/api/cpls/{cpl_id}").json()
    assert cpl["municipio"] == "Atibaia"
    assert cpl["uf"] == "SP"


def test_criar_cpl_uf_invalida_e_rejeitada(admin_client):
    resposta = admin_client.post(
        "/painel/cpls",
        data={"nome": "CPL UF Invalida", "sigla": "CPL-LOCAL-02", "uf": "ZZ"},
    )
    assert resposta.status_code == 400


def test_setor_outro_tem_precedencia_sobre_setor_select(admin_client):
    resposta = admin_client.post(
        "/painel/cpls",
        data={
            "nome": "CPL Setor Outro",
            "sigla": "CPL-LOCAL-03",
            "setor": "Setor Já Existente",
            "setor_outro": "Setor Digitado Na Hora",
        },
        follow_redirects=False,
    )
    assert resposta.status_code == 303
    cpl_id = resposta.headers["location"].rsplit("/", 1)[-1]
    cpl = admin_client.get(f"/api/cpls/{cpl_id}").json()
    assert cpl["setor"] == "Setor Digitado Na Hora"


def test_setores_cadastrados_aparecem_na_listbox_apos_criados(admin_client, monkeypatch):
    monkeypatch.setattr(routes_cpl, "estados", lambda: [])
    admin_client.post(
        "/painel/cpls",
        data={"nome": "CPL Setor A", "sigla": "CPL-LOCAL-04", "setor_outro": "Setor Recem Criado"},
    )
    resposta = admin_client.get("/painel/cpls")
    assert "Setor Recem Criado" in resposta.text


def test_edicao_cpl_pre_popula_municipio_da_uf_salva(admin_client, monkeypatch):
    monkeypatch.setattr(routes_cpl, "estados", lambda: [("SP", "São Paulo")])
    monkeypatch.setattr(
        routes_cpl, "municipios_do_estado", lambda uf: ["Atibaia", "Bragança Paulista"]
    )
    resposta_criar = admin_client.post(
        "/painel/cpls",
        data={"nome": "CPL Edicao Localidades", "sigla": "CPL-LOCAL-05", "municipio": "Atibaia", "uf": "SP"},
        follow_redirects=False,
    )
    cpl_id = resposta_criar.headers["location"].rsplit("/", 1)[-1]

    resposta = admin_client.get(f"/painel/cpls/{cpl_id}")
    assert resposta.status_code == 200
    assert '<option value="Atibaia" selected' in resposta.text


def test_criar_cpl_exige_administrador(client, db_session):
    gestor = criar_usuario_com_papel(db_session, Papel.ENTIDADE_GESTORA)
    client_gestor = login_como(client, gestor)
    resposta = client_gestor.post(
        "/painel/cpls", data={"nome": "Nao deveria criar", "sigla": "CPL-LOCAL-06"}
    )
    assert resposta.status_code == 403
