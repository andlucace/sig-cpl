"""RNF-011: infraestrutura de teste — banco de teste isolado (Postgres de
verdade, não sqlite: o projeto usa tipos específicos do Postgres — UUID,
JSONB — que não existem em sqlite) e uma sessão por teste que nunca
persiste de fato, mesmo quando o código da aplicação chama `db.commit()`
internamente (todo endpoint comita). Usa o padrão de SAVEPOINT aninhado
documentado pelo próprio SQLAlchemy para isolar testes nesse cenário.

A variável de ambiente `DATABASE_URL` é sobrescrita ANTES de qualquer
import de `app.*` — `get_settings()` é `@lru_cache`d e o engine de
`app/db/session.py` é criado na hora do import, então só funciona
sobrescrevendo o ambiente antes da primeira importação, nunca depois."""

import os
import uuid

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://sigcpl:sigcpl@localhost:5433/sigcpl_test"
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-nao-usar-em-producao")
os.environ.setdefault("SMTP_HOST", "")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import Papel  # noqa: E402
from app.models.usuario import Usuario, UsuarioPapel  # noqa: E402

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def _criar_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """Uma sessão por teste, isolada por SAVEPOINT — `db.commit()` chamado
    dentro do código da aplicação não vaza pro próximo teste."""

    conexao = engine.connect()
    transacao = conexao.begin()
    sessao = TestingSessionLocal(bind=conexao)
    savepoint = conexao.begin_nested()

    @event.listens_for(sessao, "after_transaction_end")
    def _reiniciar_savepoint(sessao_, transacao_):
        nonlocal savepoint
        if not savepoint.is_active:
            savepoint = conexao.begin_nested()

    yield sessao

    sessao.close()
    transacao.rollback()
    conexao.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _criar_usuario(db_session, email: str, senha: str, papel: Papel | None, cpl_id=None) -> Usuario:
    usuario = Usuario(email=email, hashed_password=hash_password(senha))
    db_session.add(usuario)
    db_session.flush()
    if papel is not None:
        db_session.add(UsuarioPapel(usuario_id=usuario.id, papel=papel, cpl_id=cpl_id))
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


@pytest.fixture()
def admin_usuario(db_session) -> Usuario:
    return _criar_usuario(
        db_session, f"admin-{uuid.uuid4().hex[:8]}@teste.com", "SenhaAdmin123!", Papel.ADMINISTRADOR_PLATAFORMA
    )


@pytest.fixture()
def admin_client(client, admin_usuario):
    resposta = client.post(
        "/api/auth/login", data={"username": admin_usuario.email, "password": "SenhaAdmin123!"}
    )
    assert resposta.status_code == 200
    token = resposta.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture()
def usuario_sem_papel(db_session) -> Usuario:
    return _criar_usuario(db_session, f"sempapel-{uuid.uuid4().hex[:8]}@teste.com", "SenhaSemPapel123!", None)


def criar_usuario_com_papel(db_session, papel: Papel, cpl_id=None, senha: str = "SenhaTeste123!") -> Usuario:
    """Helper (não fixture) pra testes que precisam de um papel escopado
    a uma CPL específica, decidida só dentro do teste (ex.: depois de
    criar a própria CPL)."""

    return _criar_usuario(db_session, f"{papel.value}-{uuid.uuid4().hex[:8]}@teste.com", senha, papel, cpl_id)


def login_como(client, usuario: Usuario, senha: str = "SenhaTeste123!"):
    resposta = client.post("/api/auth/login", data={"username": usuario.email, "password": senha})
    assert resposta.status_code == 200
    client.headers.update({"Authorization": f"Bearer {resposta.json()['access_token']}"})
    return client


@pytest.fixture()
def client_sem_papel(client, usuario_sem_papel):
    resposta = client.post(
        "/api/auth/login", data={"username": usuario_sem_papel.email, "password": "SenhaSemPapel123!"}
    )
    assert resposta.status_code == 200
    token = resposta.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
