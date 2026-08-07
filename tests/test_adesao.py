"""F01: fluxo de autoatendimento de adesão de membro — convite/solicitação
→ cadastro → consentimento → validação → vínculo à CPL → classificação de
elo → ativação. A rota de solicitação é pública de propósito (é a porta
de entrada de quem ainda não tem vínculo nenhum com o sistema); aprovar/
rejeitar exige papel de gestão, escopado à CPL da solicitação."""

from conftest import criar_usuario_com_papel, login_como

from app.models.enums import Papel


def _payload(**overrides):
    dados = {
        "tipo": "empresa",
        "razao_social": "Empresa Solicitante Ltda",
        "cnpj": "11222333000181",
        "elo_pretendido": "producao",
        "contato_nome": "Fulano de Tal",
        "contato_email": "fulano@example.com",
        "consentimento_lgpd": True,
    }
    dados.update(overrides)
    return dados


def _criar_cpl(admin_client, sigla="CPL-ADESAO-01"):
    return admin_client.post("/api/cpls", json={"nome": "CPL Adesão", "sigla": sigla}).json()["id"]


def test_solicitar_adesao_nao_exige_autenticacao(client, admin_client):
    cpl_id = _criar_cpl(admin_client)
    resposta = client.post(f"/api/cpls/{cpl_id}/solicitacoes-adesao", json=_payload())
    assert resposta.status_code == 201
    assert resposta.json()["status"] == "pendente"
    assert resposta.json()["entidade_id"] is None


def test_solicitar_adesao_sem_consentimento_e_rejeitada(client, admin_client):
    cpl_id = _criar_cpl(admin_client)
    resposta = client.post(
        f"/api/cpls/{cpl_id}/solicitacoes-adesao", json=_payload(consentimento_lgpd=False)
    )
    assert resposta.status_code == 400


def test_solicitar_adesao_cnpj_invalido_e_rejeitada(client, admin_client):
    cpl_id = _criar_cpl(admin_client)
    resposta = client.post(
        f"/api/cpls/{cpl_id}/solicitacoes-adesao", json=_payload(cnpj="11111111111111")
    )
    assert resposta.status_code == 400


def test_solicitar_adesao_cpl_inexistente_404(client):
    resposta = client.post(
        "/api/cpls/00000000-0000-0000-0000-000000000000/solicitacoes-adesao", json=_payload()
    )
    assert resposta.status_code == 404


def test_aprovar_cria_entidade_vinculo_e_elo(client, admin_client):
    cpl_id = _criar_cpl(admin_client, sigla="CPL-ADESAO-02")
    solicitacao_id = client.post(
        f"/api/cpls/{cpl_id}/solicitacoes-adesao", json=_payload(cnpj="11444777000161")
    ).json()["id"]

    resposta = admin_client.post(f"/api/solicitacoes-adesao/{solicitacao_id}/aprovar", json={})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "aprovada"
    entidade_id = corpo["entidade_id"]
    assert entidade_id is not None

    vinculo = admin_client.get(f"/api/cpls/{cpl_id}/entidades").json()
    assert any(v["entidade_id"] == entidade_id and v["ativo"] for v in vinculo)


def test_aprovar_reaproveita_entidade_existente_por_cnpj(client, admin_client):
    cpl_id_1 = _criar_cpl(admin_client, sigla="CPL-ADESAO-03A")
    cpl_id_2 = _criar_cpl(admin_client, sigla="CPL-ADESAO-03B")
    cnpj = "11444777000161"

    sol1 = client.post(f"/api/cpls/{cpl_id_1}/solicitacoes-adesao", json=_payload(cnpj=cnpj)).json()["id"]
    sol2 = client.post(f"/api/cpls/{cpl_id_2}/solicitacoes-adesao", json=_payload(cnpj=cnpj)).json()["id"]

    entidade_1 = admin_client.post(f"/api/solicitacoes-adesao/{sol1}/aprovar", json={}).json()["entidade_id"]
    entidade_2 = admin_client.post(f"/api/solicitacoes-adesao/{sol2}/aprovar", json={}).json()["entidade_id"]

    # RN-003: mesma entidade, vinculada a duas CPLs — não duplica o cadastro.
    assert entidade_1 == entidade_2


def test_rejeitar_nao_cria_entidade(client, admin_client):
    cpl_id = _criar_cpl(admin_client, sigla="CPL-ADESAO-04")
    solicitacao_id = client.post(f"/api/cpls/{cpl_id}/solicitacoes-adesao", json=_payload()).json()["id"]

    resposta = admin_client.post(
        f"/api/solicitacoes-adesao/{solicitacao_id}/rejeitar", json={"parecer": "Fora do escopo"}
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "rejeitada"
    assert corpo["entidade_id"] is None
    assert corpo["parecer"] == "Fora do escopo"


def test_reanalisar_solicitacao_ja_decidida_e_rejeitada(client, admin_client):
    cpl_id = _criar_cpl(admin_client, sigla="CPL-ADESAO-05")
    solicitacao_id = client.post(f"/api/cpls/{cpl_id}/solicitacoes-adesao", json=_payload()).json()["id"]

    admin_client.post(f"/api/solicitacoes-adesao/{solicitacao_id}/aprovar", json={})
    resposta = admin_client.post(f"/api/solicitacoes-adesao/{solicitacao_id}/rejeitar", json={})
    assert resposta.status_code == 400


def test_listar_e_analisar_exigem_papel_gestao(client, admin_client, db_session):
    cpl_id = _criar_cpl(admin_client, sigla="CPL-ADESAO-06")
    solicitacao_id = client.post(f"/api/cpls/{cpl_id}/solicitacoes-adesao", json=_payload()).json()["id"]

    leitor = criar_usuario_com_papel(db_session, Papel.CONSELHO_COMITE, cpl_id=cpl_id)
    client_leitor = login_como(client, leitor)

    assert client_leitor.get(f"/api/cpls/{cpl_id}/solicitacoes-adesao").status_code == 403
    assert client_leitor.post(f"/api/solicitacoes-adesao/{solicitacao_id}/aprovar", json={}).status_code == 403


def test_rota_web_publica_formulario_carrega_sem_autenticacao(client, admin_client):
    cpl_id = _criar_cpl(admin_client, sigla="CPL-ADESAO-07")
    resposta = client.get(f"/cpls/{cpl_id}/solicitar-adesao")
    assert resposta.status_code == 200
    assert "Solicitar adesão" in resposta.text


def test_rota_web_gestao_exige_login(client):
    # `client`/`admin_client` compartilham a mesma instância de TestClient
    # (`admin_client` só anexa o header de autenticação nela) — usar uma
    # CPL de verdade exigiria `admin_client` aqui, o que autenticaria
    # `client` também. Um UUID qualquer basta: o redirecionamento pro
    # login acontece antes de qualquer busca no banco.
    resposta = client.get(
        "/painel/cadastro/cpls/00000000-0000-0000-0000-000000000000/solicitacoes-adesao",
        follow_redirects=False,
    )
    assert resposta.status_code == 303
    assert resposta.headers["location"] == "/login"
