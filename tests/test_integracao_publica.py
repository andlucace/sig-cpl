"""RF-054: consulta pública de CNPJ (BrasilAPI) — mockada, sem chamada de
rede real, mesmo raciocínio de `test_geocodificacao.py`."""

import json
from unittest.mock import MagicMock

import pytest

from app.services import integracao_publica
from app.services.integracao_publica import ConsultaCNPJIndisponivel, consultar_cnpj_publico


def test_consultar_cnpj_com_menos_de_14_digitos_levanta_value_error():
    with pytest.raises(ValueError):
        consultar_cnpj_publico("123")


def test_consultar_cnpj_sucesso(monkeypatch):
    resposta_falsa = MagicMock()
    resposta_falsa.read.return_value = json.dumps(
        {
            "razao_social": "EMPRESA TESTE LTDA",
            "nome_fantasia": "EMPRESA TESTE",
            "descricao_situacao_cadastral": "ATIVA",
            "cnae_fiscal": 8550301,
            "cnae_fiscal_descricao": "Descricao do CNAE",
            "logradouro": "RUA TESTE",
            "numero": "100",
            "bairro": "CENTRO",
            "municipio": "ATIBAIA",
            "uf": "SP",
        }
    ).encode("utf-8")
    resposta_falsa.__enter__.return_value = resposta_falsa
    monkeypatch.setattr(integracao_publica.urllib.request, "urlopen", lambda *a, **k: resposta_falsa)

    resultado = consultar_cnpj_publico("11222333000181")
    assert resultado["razao_social"] == "EMPRESA TESTE LTDA"
    assert resultado["cnae"] == "8550301"
    assert "RUA TESTE" in resultado["endereco"]


def test_consultar_cnpj_nao_encontrado(monkeypatch):
    import urllib.error

    def _levanta_404(*a, **k):
        raise urllib.error.HTTPError("url", 404, "not found", {}, None)

    monkeypatch.setattr(integracao_publica.urllib.request, "urlopen", _levanta_404)

    with pytest.raises(ConsultaCNPJIndisponivel):
        consultar_cnpj_publico("11222333000181")
