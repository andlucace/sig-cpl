"""RF-057: assistente de IA (síntese, verificação de consistência,
sugestão de lacunas) — mockado, sem chamada de rede real (não dá pra
depender da API paga da Anthropic pra CI passar), mesmo raciocínio de
test_geocodificacao.py/test_integracao_publica.py."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import anthropic as anthropic_sdk
import pytest
from conftest import criar_usuario_com_papel, login_como

from app.models.enums import Papel
from app.services import ia_assistente
from app.services.ia_assistente import IAIndisponivel, gerar_assistente_ia, ia_disponivel


def _cpl_fake():
    return SimpleNamespace(
        nome="CPL Teste IA",
        sigla="CPL-IA-01",
        setor="Teste",
        municipio="Atibaia",
        uf="SP",
        nivel_maturidade=None,
    )


def _dados_fake():
    return (
        {"total_empresas": 5},
        {"total_orgaos": 2},
        {"total_objetivos": 3},
        {
            "total_projetos": 1,
            "por_estagio": {},
            "por_prioridade": {},
            "total_previsto": 0,
            "total_desembolsado": 0,
            "total_etapas": 0,
            "etapas_concluidas": 0,
            "riscos_ativos": 0,
        },
        {"nivel_maturidade_atual": None, "dias_para_vencer": None, "lacunas_avaliacao_vigente": []},
    )


def _client_falso(texto_resposta: str) -> MagicMock:
    # `type="text"` de propósito — o código real filtra os blocos de
    # `content` por tipo, pra não confundir um `ThinkingBlock` (extended
    # thinking) com o bloco de texto de verdade.
    bloco_pensamento = MagicMock(type="thinking")
    bloco_texto = MagicMock(type="text", text=texto_resposta)
    resposta_falsa = MagicMock()
    resposta_falsa.content = [bloco_pensamento, bloco_texto]
    cliente_falso = MagicMock()
    cliente_falso.messages.create.return_value = resposta_falsa
    return cliente_falso


def test_ia_disponivel_falso_sem_chave(monkeypatch):
    monkeypatch.setattr(ia_assistente, "get_settings", lambda: SimpleNamespace(anthropic_api_key=None))
    assert ia_disponivel() is False


def test_ia_disponivel_verdadeiro_com_chave(monkeypatch):
    monkeypatch.setattr(ia_assistente, "get_settings", lambda: SimpleNamespace(anthropic_api_key="fake"))
    assert ia_disponivel() is True


def test_gerar_assistente_sem_chave_levanta_indisponivel(monkeypatch):
    monkeypatch.setattr(ia_assistente, "get_settings", lambda: SimpleNamespace(anthropic_api_key=None))
    with pytest.raises(IAIndisponivel):
        gerar_assistente_ia(_cpl_fake(), *_dados_fake())


def test_gerar_assistente_sucesso(monkeypatch):
    monkeypatch.setattr(
        ia_assistente,
        "get_settings",
        lambda: SimpleNamespace(anthropic_api_key="fake-key", anthropic_model="claude-sonnet-5"),
    )
    texto = json.dumps(
        {
            "sintese": "CPL em bom desenvolvimento.",
            "verificacao_consistencia": ["Nível alto mas poucos órgãos ativos."],
            "lacunas_sugeridas": ["Registrar mais reuniões."],
        }
    )
    monkeypatch.setattr(ia_assistente.anthropic, "Anthropic", lambda **kwargs: _client_falso(texto))

    resultado = gerar_assistente_ia(_cpl_fake(), *_dados_fake())
    assert resultado["sintese"] == "CPL em bom desenvolvimento."
    assert resultado["verificacao_consistencia"] == ["Nível alto mas poucos órgãos ativos."]
    assert resultado["lacunas_sugeridas"] == ["Registrar mais reuniões."]


def test_gerar_assistente_so_com_bloco_de_pensamento_levanta_indisponivel(monkeypatch):
    """Regressão: resposta real da Anthropic com extended thinking pode
    trazer só `ThinkingBlock` (sem `TextBlock`) se o modelo não terminar
    de gerar texto — `resposta.content[0].text` quebraria com
    `AttributeError` em produção antes desta proteção."""

    monkeypatch.setattr(
        ia_assistente,
        "get_settings",
        lambda: SimpleNamespace(anthropic_api_key="fake-key", anthropic_model="claude-sonnet-5"),
    )
    resposta_falsa = MagicMock()
    resposta_falsa.content = [MagicMock(type="thinking")]
    cliente_falso = MagicMock()
    cliente_falso.messages.create.return_value = resposta_falsa
    monkeypatch.setattr(ia_assistente.anthropic, "Anthropic", lambda **kwargs: cliente_falso)

    with pytest.raises(IAIndisponivel):
        gerar_assistente_ia(_cpl_fake(), *_dados_fake())


def test_gerar_assistente_resposta_json_invalida_levanta_indisponivel(monkeypatch):
    monkeypatch.setattr(
        ia_assistente,
        "get_settings",
        lambda: SimpleNamespace(anthropic_api_key="fake-key", anthropic_model="claude-sonnet-5"),
    )
    monkeypatch.setattr(ia_assistente.anthropic, "Anthropic", lambda **kwargs: _client_falso("isso não é json"))

    with pytest.raises(IAIndisponivel):
        gerar_assistente_ia(_cpl_fake(), *_dados_fake())


def test_gerar_assistente_erro_de_api_levanta_indisponivel(monkeypatch):
    monkeypatch.setattr(
        ia_assistente,
        "get_settings",
        lambda: SimpleNamespace(anthropic_api_key="fake-key", anthropic_model="claude-sonnet-5"),
    )

    def _levanta_erro(**kwargs):
        raise anthropic_sdk.APIConnectionError(request=MagicMock())

    cliente_falso = MagicMock()
    cliente_falso.messages.create.side_effect = _levanta_erro
    monkeypatch.setattr(ia_assistente.anthropic, "Anthropic", lambda **kwargs: cliente_falso)

    with pytest.raises(IAIndisponivel):
        gerar_assistente_ia(_cpl_fake(), *_dados_fake())


def test_rota_assistente_ia_exige_papel_gestao(admin_client, client, db_session):
    cpl_id = admin_client.post("/api/cpls", json={"nome": "CPL Rota IA", "sigla": "CPL-ROTA-IA-01"}).json()["id"]

    leitor = criar_usuario_com_papel(db_session, Papel.CONSELHO_COMITE, cpl_id=cpl_id)
    client_leitor = login_como(client, leitor)

    resposta = client_leitor.post(f"/painel/indicadores/cpls/{cpl_id}/assistente-ia")
    assert resposta.status_code == 403


def test_rota_assistente_ia_sem_chave_mostra_mensagem_amigavel(admin_client):
    # Sem ANTHROPIC_API_KEY configurada no ambiente de teste (conftest.py não
    # define essa variável) — a rota deve degradar graciosamente, não 500.
    cpl_id = admin_client.post("/api/cpls", json={"nome": "CPL Rota IA 2", "sigla": "CPL-ROTA-IA-02"}).json()["id"]
    resposta = admin_client.post(f"/painel/indicadores/cpls/{cpl_id}/assistente-ia")
    assert resposta.status_code == 200
    assert "não configurado" in resposta.text
