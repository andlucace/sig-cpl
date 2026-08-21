"""RF-012: dois ajustes pontuais na campanha de atualização cadastral —
(1) "ODS relacionados" virou uma listbox de seleção múltipla com os 17
Objetivos de Desenvolvimento Sustentável, em vez de texto livre; (2) os
campos de texto longo do formulário público (mercados de exportação,
interesses em comissões, entidades associativas, recursos
compartilhados, países/parceiros, práticas ambientais, matéria-prima/
produto principal, compra/venda, parcerias institucionais, investimentos
recentes, tecnologias utilizadas, necessidades/demandas da empresa)
viraram `<textarea>` (aceitam Enter), não mais `<input type="text">`."""

from app.web.routes_atualizacao_publica import ODS_OPCOES


def _cpl_entidade_e_token(admin_client, sufixo: str):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": f"CPL ODS {sufixo}", "sigla": f"CPL-ODS-{sufixo}"}
    ).json()["id"]
    entidade_id = admin_client.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": f"Empresa ODS {sufixo}"}
    ).json()["id"]
    admin_client.post(f"/api/cpls/{cpl_id}/entidades/{entidade_id}/vinculo")
    campanha_id = admin_client.post(
        f"/api/cadastro/cpls/{cpl_id}/campanhas", json={"titulo": f"Campanha ODS {sufixo}"}
    ).json()["id"]
    convite = admin_client.post(
        f"/api/cadastro/campanhas/{campanha_id}/convites", json={"entidade_id": entidade_id}
    ).json()
    return cpl_id, entidade_id, convite["token"]


# --- Listbox de ODS -------------------------------------------------------------


def test_ods_relacionados_e_listbox_com_os_17_ods(client, admin_client):
    assert len(ODS_OPCOES) == 17
    _cpl_id, _entidade_id, token = _cpl_entidade_e_token(admin_client, "A")
    resposta = client.get(f"/atualizacao/{token}")
    assert resposta.status_code == 200
    assert '<select class="form-select" name="ods_relacionados" multiple' in resposta.text
    for opcao in ODS_OPCOES:
        assert opcao in resposta.text


def test_atualizacao_publica_grava_multiplos_ods_separados_por_ponto_e_virgula(client, admin_client):
    _cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "B")
    selecionados = [
        "ODS 8 — Trabalho decente e crescimento econômico",
        "ODS 9 — Indústria, inovação e infraestrutura",
        "ODS 16 — Paz, justiça e instituições eficazes",
    ]
    resposta = client.post(
        f"/atualizacao/{token}",
        data={
            "razao_social": "Empresa ODS B",
            "ods_relacionados": selecionados,
            "consentimento_lgpd": "sim",
        },
    )
    assert resposta.status_code == 200
    diagnostico = admin_client.get(f"/api/cadastro/entidades/{entidade_id}/diagnostico").json()
    assert diagnostico["ods_relacionados"] == "; ".join(selecionados)


def test_atualizacao_publica_ignora_ods_nao_reconhecido(client, admin_client):
    _cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "C")
    resposta = client.post(
        f"/atualizacao/{token}",
        data={
            "razao_social": "Empresa ODS C",
            "ods_relacionados": ["ODS 1 — Erradicação da pobreza", "Não é um ODS de verdade"],
            "consentimento_lgpd": "sim",
        },
    )
    assert resposta.status_code == 200
    diagnostico = admin_client.get(f"/api/cadastro/entidades/{entidade_id}/diagnostico").json()
    assert diagnostico["ods_relacionados"] == "ODS 1 — Erradicação da pobreza"


def test_formulario_publico_reabre_com_ods_ja_selecionados(client, admin_client):
    _cpl_id, _entidade_id, token = _cpl_entidade_e_token(admin_client, "D")
    client.post(
        f"/atualizacao/{token}",
        data={
            "razao_social": "Empresa ODS D",
            "ods_relacionados": ["ODS 5 — Igualdade de gênero"],
            "consentimento_lgpd": "sim",
        },
    )
    resposta = client.get(f"/atualizacao/{token}")
    assert resposta.status_code == 200
    assert '<option value="ODS 5 — Igualdade de gênero" selected>' in resposta.text


# --- Campos de texto longo viram textarea (aceitam Enter) -----------------------


def test_campos_longos_sao_textarea_nao_input(client, admin_client):
    _cpl_id, _entidade_id, token = _cpl_entidade_e_token(admin_client, "E")
    resposta = client.get(f"/atualizacao/{token}")
    assert resposta.status_code == 200
    corpo = resposta.text
    campos_textarea = [
        "mercados_exportacao",
        "interesse_comissoes",
        "entidades_associativas",
        "recursos_compartilhados",
        "descricao_contatos_internacionais",
        "praticas_ambientais",
        "materia_prima_principal",
        "produto_principal",
        "compra_de",
        "vende_para",
        "parcerias_instituicoes",
        "investimentos_recentes",
        "tecnologias_utilizadas",
        "necessidades_empresa",
        "outras_demandas",
    ]
    for campo in campos_textarea:
        assert f'<textarea class="form-control" name="{campo}"' in corpo
        assert f'<input type="text" class="form-control" name="{campo}"' not in corpo


def test_atualizacao_publica_grava_texto_multilinha_com_enter(client, admin_client):
    _cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "F")
    texto_multilinha = "Argentina\nChile\nUruguai"
    resposta = client.post(
        f"/atualizacao/{token}",
        data={
            "razao_social": "Empresa ODS F",
            "mercados_exportacao": texto_multilinha,
            "necessidades_empresa": "Linha 1\nLinha 2",
            "consentimento_lgpd": "sim",
        },
    )
    assert resposta.status_code == 200
    diagnostico = admin_client.get(f"/api/cadastro/entidades/{entidade_id}/diagnostico").json()
    assert diagnostico["mercados_exportacao"] == texto_multilinha
    assert diagnostico["necessidades_empresa"] == "Linha 1\nLinha 2"


# --- ods_mais_citados não quebra com vírgula interna no título do ODS -----------


def test_resumo_cadastral_conta_ods_com_virgula_no_titulo_corretamente(admin_client):
    cpl_id, entidade_id, _token = _cpl_entidade_e_token(admin_client, "G")
    entidade_2 = admin_client.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": "Empresa ODS G2"}
    ).json()["id"]
    admin_client.post(f"/api/cpls/{cpl_id}/entidades/{entidade_2}/vinculo")

    admin_client.put(
        f"/api/cadastro/entidades/{entidade_id}/diagnostico",
        json={"ods_relacionados": "ODS 9 — Indústria, inovação e infraestrutura; ODS 16 — Paz, justiça e instituições eficazes"},
    )
    admin_client.put(
        f"/api/cadastro/entidades/{entidade_2}/diagnostico",
        json={"ods_relacionados": "ODS 9 — Indústria, inovação e infraestrutura"},
    )

    resumo = admin_client.get(f"/api/indicadores/cpls/{cpl_id}/resumo-cadastral").json()
    mais_citados = dict(resumo["ods_mais_citados"])
    assert mais_citados["ODS 9 — Indústria, inovação e infraestrutura"] == 2
    assert mais_citados["ODS 16 — Paz, justiça e instituições eficazes"] == 1
    # nenhum fragmento partido pela vírgula interna do título (ex.: "Indústria" sozinho)
    assert "Indústria" not in mais_citados
    assert " inovação e infraestrutura" not in mais_citados
