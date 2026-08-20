"""RF-012: diagnóstico cadastral — pedidos explícitos de (c) ter no
formulário público (link de campanha) todos os campos que estão no
modelo da planilha de importação (`CAMPOS_CONHECIDOS`), e (d) mostrar no
resumo da entidade os campos que não apareciam ali antes (o resumo só
mostrava 3 de 26 campos)."""


def _cpl_entidade_e_token(admin_client, sufixo: str):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": f"CPL Diagnostico {sufixo}", "sigla": f"CPL-DIAG-{sufixo}"}
    ).json()["id"]
    entidade_id = admin_client.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": f"Empresa Diagnostico {sufixo}"}
    ).json()["id"]
    admin_client.post(f"/api/cpls/{cpl_id}/entidades/{entidade_id}/vinculo")
    campanha_id = admin_client.post(
        f"/api/cadastro/cpls/{cpl_id}/campanhas", json={"titulo": f"Campanha {sufixo}"}
    ).json()["id"]
    convite = admin_client.post(
        f"/api/cadastro/campanhas/{campanha_id}/convites", json={"entidade_id": entidade_id}
    ).json()
    return cpl_id, entidade_id, convite["token"]


# --- (c) Campos faltantes no formulário público ------------------------------


def test_formulario_publico_mostra_os_tres_campos_que_faltavam(client, admin_client):
    _cpl_id, _entidade_id, token = _cpl_entidade_e_token(admin_client, "A")
    resposta = client.get(f"/atualizacao/{token}")
    assert resposta.status_code == 200
    assert 'name="compartilha_recursos"' in resposta.text
    assert 'name="recursos_compartilhados"' in resposta.text
    assert 'name="ods_relacionados"' in resposta.text


def test_atualizacao_publica_grava_compartilha_recursos_e_ods(client, admin_client):
    cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "B")
    resposta = client.post(
        f"/atualizacao/{token}",
        data={
            "razao_social": "Empresa Diagnostico B",
            "compartilha_recursos": "sim",
            "recursos_compartilhados": "Galpão e maquinário compartilhados",
            "ods_relacionados": "ODS 9 — Indústria, inovação e infraestrutura",
            "consentimento_lgpd": "sim",
        },
    )
    assert resposta.status_code == 200

    diagnostico = admin_client.get(f"/api/cadastro/entidades/{entidade_id}/diagnostico").json()
    assert diagnostico["compartilha_recursos"] is True
    assert diagnostico["recursos_compartilhados"] == "Galpão e maquinário compartilhados"
    assert diagnostico["ods_relacionados"] == "ODS 9 — Indústria, inovação e infraestrutura"


def test_atualizacao_publica_grava_compartilha_recursos_nao(client, admin_client):
    cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "C")
    client.post(
        f"/atualizacao/{token}",
        data={"razao_social": "Empresa Diagnostico C", "compartilha_recursos": "nao", "consentimento_lgpd": "sim"},
    )
    diagnostico = admin_client.get(f"/api/cadastro/entidades/{entidade_id}/diagnostico").json()
    assert diagnostico["compartilha_recursos"] is False


# --- (d) Resumo do diagnóstico na tela da entidade ---------------------------


def test_resumo_diagnostico_mostra_campos_antes_ausentes(admin_client):
    _cpl_id, entidade_id, _token = _cpl_entidade_e_token(admin_client, "D")
    admin_client.put(
        f"/api/cadastro/entidades/{entidade_id}/diagnostico",
        json={
            "atividades_produtos": "Fabricação de autopeças",
            "mercados_exportacao": "Argentina e Chile",
            "ods_relacionados": "ODS 8",
            "realiza_inovacao": False,
        },
    )
    resposta = admin_client.get(f"/painel/cadastro/entidades/{entidade_id}")
    assert resposta.status_code == 200
    assert "Fabricação de autopeças" in resposta.text
    assert "Argentina e Chile" in resposta.text
    assert "ODS 8" in resposta.text
    # campo booleano respondido explicitamente como falso ainda deve aparecer
    assert "Realiza inovação?" in resposta.text


def test_resumo_diagnostico_nao_mostra_pergunta_nunca_respondida(admin_client):
    _cpl_id, entidade_id, _token = _cpl_entidade_e_token(admin_client, "E")
    admin_client.put(
        f"/api/cadastro/entidades/{entidade_id}/diagnostico",
        json={"capacidade_produtiva": "500 unidades/mês"},
    )
    resposta = admin_client.get(f"/painel/cadastro/entidades/{entidade_id}")
    assert resposta.status_code == 200
    assert "500 unidades/mês" in resposta.text
    # nenhum dos campos booleanos foi respondido — não devem aparecer como "Não"
    assert "Realiza inovação?" not in resposta.text
    assert "Realiza P&D?" not in resposta.text
    assert "Possui certificações?" not in resposta.text


def test_resumo_diagnostico_sem_nenhuma_resposta(admin_client):
    admin_client.post(
        "/api/cpls", json={"nome": "CPL Diagnostico Vazio", "sigla": "CPL-DIAG-VAZIO"}
    )
    entidade_id = admin_client.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": "Empresa Sem Diagnostico"}
    ).json()["id"]
    resposta = admin_client.get(f"/painel/cadastro/entidades/{entidade_id}")
    assert resposta.status_code == 200
    assert "Nenhum diagnóstico respondido ainda." in resposta.text
