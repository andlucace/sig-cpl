"""RF-004: registro, login e a válvula de bootstrap do primeiro
administrador (RF-005) — cobre a espinha dorsal de autenticação que
todo o resto do sistema depende."""

from app.models.enums import Papel
from app.models.usuario import UsuarioPapel


def test_registrar_usuario_cria_conta(client):
    resposta = client.post(
        "/api/auth/registrar", json={"email": "novo@teste.com", "password": "SenhaForte123!"}
    )
    assert resposta.status_code == 201
    assert resposta.json()["email"] == "novo@teste.com"


def test_registrar_usuario_rejeita_email_duplicado(client):
    client.post("/api/auth/registrar", json={"email": "dup@teste.com", "password": "SenhaForte123!"})
    resposta = client.post(
        "/api/auth/registrar", json={"email": "dup@teste.com", "password": "OutraSenha456!"}
    )
    assert resposta.status_code == 400


def test_login_com_senha_correta_devolve_token(client):
    client.post("/api/auth/registrar", json={"email": "login@teste.com", "password": "SenhaForte123!"})
    resposta = client.post(
        "/api/auth/login", data={"username": "login@teste.com", "password": "SenhaForte123!"}
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["access_token"]


def test_login_com_senha_errada_rejeitado(client):
    client.post("/api/auth/registrar", json={"email": "senhaerrada@teste.com", "password": "SenhaForte123!"})
    resposta = client.post(
        "/api/auth/login", data={"username": "senhaerrada@teste.com", "password": "SenhaTotalmenteErrada"}
    )
    assert resposta.status_code == 401


def test_me_sem_token_retorna_401(client):
    resposta = client.get("/api/auth/me")
    assert resposta.status_code == 401


def test_me_com_token_retorna_usuario_correto(admin_client, admin_usuario):
    resposta = admin_client.get("/api/auth/me")
    assert resposta.status_code == 200
    assert resposta.json()["email"] == admin_usuario.email


def test_valvula_bootstrap_fecha_apos_primeiro_admin(client, db_session, admin_usuario):
    """RF-005: enquanto não existe nenhum administrador, qualquer usuário
    autenticado pode se autoconceder o papel — mas essa exceção deixa de
    valer assim que o primeiro admin existe."""

    resposta_login = client.post(
        "/api/auth/registrar", json={"email": "tentativa@teste.com", "password": "SenhaForte123!"}
    )
    usuario_id = resposta_login.json()["id"]
    login = client.post(
        "/api/auth/login", data={"username": "tentativa@teste.com", "password": "SenhaForte123!"}
    )
    client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})

    resposta = client.post(
        f"/api/usuarios/{usuario_id}/papeis", json={"papel": Papel.ADMINISTRADOR_PLATAFORMA.value}
    )
    assert resposta.status_code == 403

    ainda_sem_papel = (
        db_session.query(UsuarioPapel).filter(UsuarioPapel.usuario_id == usuario_id).count()
    )
    assert ainda_sem_papel == 0
