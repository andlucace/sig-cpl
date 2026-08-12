"""RF-012: e-mail de comunicações da entidade e envio automático do
convite de campanha de atualização cadastral — achado a partir de um
relato real ("empresa não recebeu o e-mail da campanha"): o convite
sempre só gerou um link/token pra a gestão copiar manualmente, nunca
enviou e-mail nenhum. `enviar_email` é mockado no ponto de uso
(`app.services.campanhas.enviar_email`), mesmo padrão já usado em
`test_localidades.py`/`test_geocodificacao.py` — nenhum destes testes
depende de SMTP de verdade."""

import uuid
from datetime import date, timedelta

from conftest import criar_usuario_com_papel, login_como

from app.models.enums import Papel
from app.models.pessoa import Pessoa, PessoaVinculo
from app.services import campanhas as campanhas_service


def _cpl_e_entidade(admin_client, sufixo: str, email_entidade: str | None = None):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": f"CPL Campanha {sufixo}", "sigla": f"CPL-CAMP-{sufixo}"}
    ).json()["id"]
    payload = {"tipo": "empresa", "razao_social": f"Empresa Campanha {sufixo}"}
    if email_entidade:
        payload["email"] = email_entidade
    entidade_id = admin_client.post("/api/entidades", json=payload).json()["id"]
    admin_client.post(f"/api/cpls/{cpl_id}/entidades/{entidade_id}/vinculo")
    return cpl_id, entidade_id


def _campanha(admin_client, cpl_id, sufixo: str):
    return admin_client.post(
        f"/api/cadastro/cpls/{cpl_id}/campanhas", json={"titulo": f"Campanha {sufixo}"}
    ).json()["id"]


def _vincular_pessoa(db_session, entidade_id: str, email: str, data_fim=None):
    pessoa = Pessoa(nome="Contato de Teste", email=email)
    db_session.add(pessoa)
    db_session.flush()
    db_session.add(
        PessoaVinculo(
            pessoa_id=pessoa.id,
            entidade_id=uuid.UUID(entidade_id),
            papel=Papel.EMPRESA_MEMBRO,
            cargo="Contato",
            data_inicio=date(2020, 1, 1),
            data_fim=data_fim,
        )
    )
    db_session.commit()
    return pessoa


# --- Entidade.email ---------------------------------------------------------


def test_criar_entidade_com_email(admin_client):
    resposta = admin_client.post(
        "/api/entidades",
        json={"tipo": "empresa", "razao_social": "Empresa Com Email", "email": "contato@empresa.com"},
    )
    assert resposta.status_code == 201
    assert resposta.json()["email"] == "contato@empresa.com"


def test_criar_entidade_com_email_invalido_e_rejeitada(admin_client):
    resposta = admin_client.post(
        "/api/entidades",
        json={"tipo": "empresa", "razao_social": "Empresa Email Ruim", "email": "nao-e-email"},
    )
    assert resposta.status_code == 422


def test_atualizar_email_da_entidade(admin_client):
    entidade_id = admin_client.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": "Empresa Sem Email"}
    ).json()["id"]
    resposta = admin_client.patch(
        f"/api/entidades/{entidade_id}/email", json={"email": "novo@empresa.com"}
    )
    assert resposta.status_code == 200
    assert resposta.json()["email"] == "novo@empresa.com"


# --- contatos_da_entidade() --------------------------------------------------


def test_contatos_da_entidade_sem_nenhum_email(admin_client, db_session):
    _cpl_id, entidade_id = _cpl_e_entidade(admin_client, "A")
    entidade = db_session.get(campanhas_service.Entidade, uuid.UUID(entidade_id))
    assert campanhas_service.contatos_da_entidade(db_session, entidade) == []


def test_contatos_da_entidade_usa_email_proprio(admin_client, db_session):
    _cpl_id, entidade_id = _cpl_e_entidade(admin_client, "B", email_entidade="empresa-b@teste.com")
    entidade = db_session.get(campanhas_service.Entidade, uuid.UUID(entidade_id))
    assert campanhas_service.contatos_da_entidade(db_session, entidade) == ["empresa-b@teste.com"]


def test_contatos_da_entidade_soma_pessoa_vinculada(admin_client, db_session):
    _cpl_id, entidade_id = _cpl_e_entidade(admin_client, "C", email_entidade="empresa-c@teste.com")
    _vincular_pessoa(db_session, entidade_id, "pessoa-c@teste.com")
    entidade = db_session.get(campanhas_service.Entidade, uuid.UUID(entidade_id))
    contatos = campanhas_service.contatos_da_entidade(db_session, entidade)
    assert set(contatos) == {"empresa-c@teste.com", "pessoa-c@teste.com"}


def test_contatos_da_entidade_deduplica_mesmo_email(admin_client, db_session):
    _cpl_id, entidade_id = _cpl_e_entidade(admin_client, "D", email_entidade="mesmo@teste.com")
    _vincular_pessoa(db_session, entidade_id, "mesmo@teste.com")
    entidade = db_session.get(campanhas_service.Entidade, uuid.UUID(entidade_id))
    assert campanhas_service.contatos_da_entidade(db_session, entidade) == ["mesmo@teste.com"]


def test_contatos_da_entidade_ignora_vinculo_encerrado(admin_client, db_session):
    _cpl_id, entidade_id = _cpl_e_entidade(admin_client, "E")
    ontem = date.today() - timedelta(days=1)
    _vincular_pessoa(db_session, entidade_id, "ex-contato@teste.com", data_fim=ontem)
    entidade = db_session.get(campanhas_service.Entidade, uuid.UUID(entidade_id))
    assert campanhas_service.contatos_da_entidade(db_session, entidade) == []


# --- Envio automático no convite ---------------------------------------------


def test_convidar_sem_contato_nao_envia_email(admin_client, monkeypatch):
    chamadas = []
    monkeypatch.setattr(campanhas_service, "enviar_email", lambda *a, **k: chamadas.append(a))

    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "F")
    campanha_id = _campanha(admin_client, cpl_id, "F")
    resposta = admin_client.post(
        f"/api/cadastro/campanhas/{campanha_id}/convites", json={"entidade_id": entidade_id}
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["email_enviado"] is False
    assert corpo["email_erro"] is None
    assert corpo["email_destinatarios"] is None
    assert chamadas == []


def test_convidar_com_email_da_entidade_envia(admin_client, monkeypatch):
    chamadas = []
    monkeypatch.setattr(campanhas_service, "enviar_email", lambda *a, **k: chamadas.append(a))

    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "G", email_entidade="empresa-g@teste.com")
    campanha_id = _campanha(admin_client, cpl_id, "G")
    resposta = admin_client.post(
        f"/api/cadastro/campanhas/{campanha_id}/convites", json={"entidade_id": entidade_id}
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["email_enviado"] is True
    assert corpo["email_destinatarios"] == ["empresa-g@teste.com"]
    assert corpo["email_enviado_em"] is not None
    assert len(chamadas) == 1
    assert chamadas[0][0] == "empresa-g@teste.com"
    assert "atualizacao/" in chamadas[0][2]


def test_convidar_envia_tambem_para_contatos_vinculados(admin_client, db_session, monkeypatch):
    chamadas = []
    monkeypatch.setattr(campanhas_service, "enviar_email", lambda *a, **k: chamadas.append(a))

    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "H", email_entidade="empresa-h@teste.com")
    _vincular_pessoa(db_session, entidade_id, "contato-h@teste.com")
    campanha_id = _campanha(admin_client, cpl_id, "H")
    resposta = admin_client.post(
        f"/api/cadastro/campanhas/{campanha_id}/convites", json={"entidade_id": entidade_id}
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert set(corpo["email_destinatarios"]) == {"empresa-h@teste.com", "contato-h@teste.com"}
    assert len(chamadas) == 2


def test_convidar_smtp_falha_nao_bloqueia_criacao_do_convite(admin_client, monkeypatch):
    def _levanta_erro(*a, **k):
        raise RuntimeError("SMTP não configurado (SMTP_HOST ausente)")

    monkeypatch.setattr(campanhas_service, "enviar_email", _levanta_erro)

    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "I", email_entidade="empresa-i@teste.com")
    campanha_id = _campanha(admin_client, cpl_id, "I")
    resposta = admin_client.post(
        f"/api/cadastro/campanhas/{campanha_id}/convites", json={"entidade_id": entidade_id}
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["email_enviado"] is False
    assert "SMTP" in corpo["email_erro"]

    # o link continua existindo — a criação do convite não foi bloqueada
    listagem = admin_client.get(f"/api/cadastro/campanhas/{campanha_id}/convites").json()
    assert len(listagem) == 1
    assert listagem[0]["token"]


def test_convidar_entidade_via_web_tambem_envia_email(admin_client, monkeypatch):
    chamadas = []
    monkeypatch.setattr(campanhas_service, "enviar_email", lambda *a, **k: chamadas.append(a))

    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "J", email_entidade="empresa-j@teste.com")
    campanha_id = _campanha(admin_client, cpl_id, "J")
    resposta = admin_client.post(
        f"/painel/cadastro/campanhas/{campanha_id}/convites", data={"entidade_id": entidade_id}
    )
    assert resposta.status_code == 200
    assert "E-mail enviado para empresa-j@teste.com" in resposta.text
    assert len(chamadas) == 1


def test_convidar_entidade_web_sem_contato_mostra_aviso(admin_client, monkeypatch):
    monkeypatch.setattr(
        campanhas_service,
        "enviar_email",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("não deveria enviar sem contato")),
    )

    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "K")
    campanha_id = _campanha(admin_client, cpl_id, "K")
    resposta = admin_client.post(
        f"/painel/cadastro/campanhas/{campanha_id}/convites", data={"entidade_id": entidade_id}
    )
    assert resposta.status_code == 200
    assert "Nenhum e-mail cadastrado" in resposta.text


def test_convidar_entidade_exige_papel_gestao(client, admin_client, db_session):
    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "L", email_entidade="empresa-l@teste.com")
    campanha_id = _campanha(admin_client, cpl_id, "L")

    leitor = criar_usuario_com_papel(db_session, Papel.CONSELHO_COMITE, cpl_id=cpl_id)
    client_leitor = login_como(client, leitor)
    resposta = client_leitor.post(
        f"/api/cadastro/campanhas/{campanha_id}/convites", json={"entidade_id": entidade_id}
    )
    assert resposta.status_code == 403
