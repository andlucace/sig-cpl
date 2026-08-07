"""RF-055: portal de transparência público — sem autenticação nenhuma,
e sem exposição de dado pessoal (nome de pessoa/membro de governança)."""


def _preparar_cpl_com_governanca(admin_client):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": "CPL Portal Publico", "sigla": "CPL-PORTAL-01"}
    ).json()["id"]
    orgao_id = admin_client.post(
        f"/api/governanca/cpls/{cpl_id}/orgaos",
        json={"nome": "Conselho Gestor", "tipo": "conselho"},
    ).json()["id"]
    pessoa_id = admin_client.post("/api/pessoas", json={"nome": "Fulano da Silva Sigiloso"}).json()["id"]
    admin_client.post(
        f"/api/governanca/orgaos/{orgao_id}/membros",
        json={"pessoa_id": pessoa_id, "funcao": "Presidente", "data_inicio": "2026-01-01"},
    )
    return cpl_id, orgao_id


def test_lista_publica_nao_exige_autenticacao(client, admin_client):
    admin_client.post("/api/cpls", json={"nome": "CPL Portal Publico Lista", "sigla": "CPL-PORTAL-02"})

    resposta = client.get("/cpls")
    assert resposta.status_code == 200
    assert "CPL Portal Publico Lista" in resposta.text


def test_detalhe_publico_nao_exige_autenticacao_e_nao_expoe_nome_de_pessoa(client, admin_client):
    cpl_id, _orgao_id = _preparar_cpl_com_governanca(admin_client)

    resposta = client.get(f"/cpls/{cpl_id}")
    assert resposta.status_code == 200
    assert "CPL Portal Publico" in resposta.text
    assert "Conselho Gestor" in resposta.text
    # RF-055 exige "sem exposição de dados pessoais" — nome de pessoa nunca aparece,
    # só a contagem de membros ativos do órgão.
    assert "Fulano da Silva Sigiloso" not in resposta.text
    assert "1 membro(s)" in resposta.text


def test_cpl_inexistente_ou_inativa_retorna_404(client, admin_client):
    resposta = client.get("/cpls/00000000-0000-0000-0000-000000000000")
    assert resposta.status_code == 404


def test_apenas_projetos_autorizados_aparecem_no_portal_publico(admin_client, client):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": "CPL Projetos Publicos", "sigla": "CPL-PROJ-PUB-01"}
    ).json()["id"]

    projeto_aprovado = admin_client.post(
        f"/api/projetos/cpls/{cpl_id}/projetos", json={"titulo": "Projeto Aprovado Publicavel"}
    ).json()
    admin_client.patch(f"/api/projetos/{projeto_aprovado['id']}", json={"estagio": "aprovado"})

    admin_client.post(f"/api/projetos/cpls/{cpl_id}/projetos", json={"titulo": "Projeto Ainda Em Elaboracao"})

    resposta = client.get(f"/cpls/{cpl_id}")
    assert resposta.status_code == 200
    assert "Projeto Aprovado Publicavel" in resposta.text
    assert "Projeto Ainda Em Elaboracao" not in resposta.text
