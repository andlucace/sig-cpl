"""RF-001/RF-006/RF-008: CPL, Entidade e o vínculo entre elas — e o RBAC
que decide quem pode ver/criar o quê (RF-005)."""

from conftest import criar_usuario_com_papel, login_como

from app.models.enums import Papel


def _criar_cpl(admin_client, sigla="CPL-TESTE-01") -> str:
    resposta = admin_client.post(
        "/api/cpls", json={"nome": "CPL de Teste", "sigla": sigla, "municipio": "Teste", "uf": "SP"}
    )
    assert resposta.status_code == 201
    return resposta.json()["id"]


def test_criar_cpl_exige_administrador(client_sem_papel):
    resposta = client_sem_papel.post(
        "/api/cpls", json={"nome": "CPL sem permissao", "sigla": "CPL-SEM-PERM"}
    )
    assert resposta.status_code == 403


def test_criar_cpl_como_admin(admin_client):
    cpl_id = _criar_cpl(admin_client)
    resposta = admin_client.get(f"/api/cpls/{cpl_id}")
    assert resposta.status_code == 200
    assert resposta.json()["sigla"] == "CPL-TESTE-01"


def test_criar_cpl_rejeita_sigla_duplicada(admin_client):
    _criar_cpl(admin_client, sigla="CPL-DUPLICADA")
    resposta = admin_client.post(
        "/api/cpls", json={"nome": "Outra CPL", "sigla": "CPL-DUPLICADA"}
    )
    assert resposta.status_code == 400


def test_criar_entidade_e_vincular_a_cpl(admin_client):
    cpl_id = _criar_cpl(admin_client, sigla="CPL-VINCULO")
    resposta_entidade = admin_client.post(
        "/api/entidades",
        json={"tipo": "empresa", "razao_social": "Empresa de Teste Ltda", "municipio": "Atibaia", "uf": "SP"},
    )
    assert resposta_entidade.status_code == 201
    entidade_id = resposta_entidade.json()["id"]

    resposta_vinculo = admin_client.post(f"/api/cpls/{cpl_id}/entidades/{entidade_id}/vinculo")
    assert resposta_vinculo.status_code == 201

    resposta_lista = admin_client.get(f"/api/cpls/{cpl_id}/entidades")
    assert resposta_lista.status_code == 200
    assert len(resposta_lista.json()) == 1
    assert resposta_lista.json()[0]["entidade_id"] == entidade_id


def test_vincular_entidade_duas_vezes_rejeitado(admin_client):
    cpl_id = _criar_cpl(admin_client, sigla="CPL-VINCULO-DUP")
    entidade_id = admin_client.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": "Empresa Duplicada"}
    ).json()["id"]
    admin_client.post(f"/api/cpls/{cpl_id}/entidades/{entidade_id}/vinculo")
    resposta = admin_client.post(f"/api/cpls/{cpl_id}/entidades/{entidade_id}/vinculo")
    assert resposta.status_code == 400


def test_gestao_de_uma_cpl_nao_gerencia_outra(client, db_session):
    """RF-005: `verificar_papel` com `cpl_id` só passa se o vínculo do
    usuário for pra essa CPL específica (ou for global, caso admin)."""

    admin = criar_usuario_com_papel(db_session, Papel.ADMINISTRADOR_PLATAFORMA)
    admin_client = login_como(client, admin)
    cpl_a = _criar_cpl(admin_client, sigla="CPL-A-ISOLADA")
    cpl_b = _criar_cpl(admin_client, sigla="CPL-B-ISOLADA")

    gestor_a = criar_usuario_com_papel(db_session, Papel.ENTIDADE_GESTORA, cpl_id=cpl_a)
    client_gestor_a = login_como(client, gestor_a)

    orgao_em_a = client_gestor_a.post(
        f"/api/governanca/cpls/{cpl_a}/orgaos", json={"nome": "Conselho A", "tipo": "conselho"}
    )
    assert orgao_em_a.status_code == 201

    orgao_em_b = client_gestor_a.post(
        f"/api/governanca/cpls/{cpl_b}/orgaos", json={"nome": "Conselho B", "tipo": "conselho"}
    )
    assert orgao_em_b.status_code == 403
