"""RF-015 a RF-020: órgão, membro, reunião, deliberação, voto e ata —
smoke test do fluxo completo de governança.

Pedido explícito de melhorias no papel Dirigente da entidade (que usa
`PAPEIS_GESTAO`, mesmo grupo de sempre): limpar o formulário e mostrar
confirmação ao convocar reunião, excluir membro com motivo (auditado),
documento de posse do órgão também visível em Documentos, e e-mail de
convocação para todos os membros — cobertos abaixo em blocos separados."""

import uuid

from app.models.auditoria import RegistroAuditoria
from app.models.enums import AcaoAuditoria
from app.services import governanca as governanca_service


def _preparar_cpl_e_orgao(admin_client, sufixo: str = "01"):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": "CPL Governanca", "sigla": f"CPL-GOV-{sufixo}"}
    ).json()["id"]
    orgao_id = admin_client.post(
        f"/api/governanca/cpls/{cpl_id}/orgaos",
        json={"nome": "Conselho Gestor", "tipo": "conselho"},
    ).json()["id"]
    pessoa_id = admin_client.post("/api/pessoas", json={"nome": "Pessoa da Governanca"}).json()["id"]
    return cpl_id, orgao_id, pessoa_id


def _cpl_orgao_e_membro_com_email(admin_client, sufixo: str, email: str | None):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": f"CPL Gov {sufixo}", "sigla": f"CPL-GOV-{sufixo}"}
    ).json()["id"]
    orgao_id = admin_client.post(
        f"/api/governanca/cpls/{cpl_id}/orgaos",
        json={"nome": "Conselho", "tipo": "conselho"},
    ).json()["id"]
    payload_pessoa = {"nome": f"Membro {sufixo}"}
    if email:
        payload_pessoa["email"] = email
    pessoa_id = admin_client.post("/api/pessoas", json=payload_pessoa).json()["id"]
    membro_id = admin_client.post(
        f"/api/governanca/orgaos/{orgao_id}/membros",
        json={"pessoa_id": pessoa_id, "funcao": "Presidente", "data_inicio": "2026-01-01"},
    ).json()["id"]
    return cpl_id, orgao_id, pessoa_id, membro_id


def test_fluxo_completo_reuniao_com_deliberacao_e_ata(admin_client):
    cpl_id, orgao_id, pessoa_id = _preparar_cpl_e_orgao(admin_client)

    membro = admin_client.post(
        f"/api/governanca/orgaos/{orgao_id}/membros",
        json={"pessoa_id": pessoa_id, "funcao": "Presidente", "data_inicio": "2026-01-01"},
    )
    assert membro.status_code == 201

    reuniao = admin_client.post(
        f"/api/governanca/orgaos/{orgao_id}/reunioes",
        json={"titulo": "1a Reuniao", "data_hora": "2026-06-01T10:00:00"},
    )
    assert reuniao.status_code == 201
    reuniao_id = reuniao.json()["id"]

    presenca = admin_client.post(
        f"/api/governanca/reunioes/{reuniao_id}/presencas",
        json={"pessoa_id": pessoa_id, "presente": True},
    )
    assert presenca.status_code == 201

    deliberacao = admin_client.post(
        f"/api/governanca/reunioes/{reuniao_id}/deliberacoes",
        json={"descricao": "Aprovar o plano de trabalho"},
    )
    assert deliberacao.status_code == 201
    deliberacao_id = deliberacao.json()["id"]

    voto = admin_client.post(
        f"/api/governanca/deliberacoes/{deliberacao_id}/votos",
        json={"pessoa_id": pessoa_id, "voto": "a_favor"},
    )
    assert voto.status_code == 201

    concluir = admin_client.patch(
        f"/api/governanca/deliberacoes/{deliberacao_id}", json={"resultado": "aprovada"}
    )
    assert concluir.status_code == 200
    assert concluir.json()["resultado"] == "aprovada"

    ata = admin_client.patch(
        f"/api/governanca/reunioes/{reuniao_id}",
        json={"status": "realizada", "ata": "Reuniao concluida com sucesso.", "quorum_atingido": True},
    )
    assert ata.status_code == 200
    assert ata.json()["status"] == "realizada"


def test_presenca_duplicada_para_mesma_pessoa_rejeitada(admin_client):
    _cpl_id, orgao_id, pessoa_id = _preparar_cpl_e_orgao(admin_client)
    reuniao_id = admin_client.post(
        f"/api/governanca/orgaos/{orgao_id}/reunioes",
        json={"titulo": "Reuniao", "data_hora": "2026-06-01T10:00:00"},
    ).json()["id"]

    primeira = admin_client.post(
        f"/api/governanca/reunioes/{reuniao_id}/presencas", json={"pessoa_id": pessoa_id, "presente": True}
    )
    assert primeira.status_code == 201
    segunda = admin_client.post(
        f"/api/governanca/reunioes/{reuniao_id}/presencas", json={"pessoa_id": pessoa_id, "presente": False}
    )
    assert segunda.status_code == 400


# --- Excluir membro com motivo, auditado (pedido explícito) -----------------


def test_remover_membro_exige_motivo(admin_client):
    _cpl_id, _orgao_id, _pessoa_id, membro_id = _cpl_orgao_e_membro_com_email(
        admin_client, "A", "membro-a@teste.com"
    )
    resposta = admin_client.post(f"/api/governanca/membros/{membro_id}/remover", json={})
    assert resposta.status_code == 422


def test_remover_membro_desativa_e_registra_motivo(admin_client):
    _cpl_id, _orgao_id, _pessoa_id, membro_id = _cpl_orgao_e_membro_com_email(
        admin_client, "B", "membro-b@teste.com"
    )
    resposta = admin_client.post(
        f"/api/governanca/membros/{membro_id}/remover", json={"motivo": "Renúncia ao mandato"}
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["ativo"] is False
    assert corpo["motivo_remocao"] == "Renúncia ao mandato"
    assert corpo["data_fim"] is not None


def test_remover_membro_gera_registro_de_auditoria(admin_client, db_session):
    _cpl_id, _orgao_id, _pessoa_id, membro_id = _cpl_orgao_e_membro_com_email(
        admin_client, "C", "membro-c@teste.com"
    )
    admin_client.post(f"/api/governanca/membros/{membro_id}/remover", json={"motivo": "Conduta inadequada"})

    registro = (
        db_session.query(RegistroAuditoria)
        .filter(
            RegistroAuditoria.entidade_tipo == "MembroOrgao",
            RegistroAuditoria.entidade_id == uuid.UUID(membro_id),
            RegistroAuditoria.acao == AcaoAuditoria.ATUALIZACAO,
        )
        .first()
    )
    assert registro is not None
    assert registro.dados_novos["ativo"] is False
    assert registro.dados_novos["motivo_remocao"] == "Conduta inadequada"


def test_remover_membro_exige_papel_gestao(client, admin_client, db_session):
    from conftest import criar_usuario_com_papel, login_como

    from app.models.enums import Papel

    cpl_id, _orgao_id, _pessoa_id, membro_id = _cpl_orgao_e_membro_com_email(
        admin_client, "D", "membro-d@teste.com"
    )
    leitor = criar_usuario_com_papel(db_session, Papel.CONSELHO_COMITE, cpl_id=cpl_id)
    client_leitor = login_como(client, leitor)
    resposta = client_leitor.post(
        f"/api/governanca/membros/{membro_id}/remover", json={"motivo": "Teste"}
    )
    assert resposta.status_code == 403


# --- E-mail de convocação de reunião para todos os membros (pedido explícito) --


def test_convocar_reuniao_envia_email_para_membros_ativos(admin_client, monkeypatch):
    chamadas = []
    monkeypatch.setattr(governanca_service, "enviar_email", lambda *a, **k: chamadas.append(a))

    _cpl_id, orgao_id, _pessoa_id, _membro_id = _cpl_orgao_e_membro_com_email(
        admin_client, "E", "membro-e@teste.com"
    )
    resposta = admin_client.post(
        f"/api/governanca/orgaos/{orgao_id}/reunioes",
        json={"titulo": "Reuniao com email", "data_hora": "2026-06-01T10:00:00"},
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["email_convocacao_enviado"] is True
    assert corpo["email_convocacao_destinatarios"] == ["membro-e@teste.com"]
    assert corpo["email_convocacao_enviado_em"] is not None
    assert len(chamadas) == 1
    assert chamadas[0][0] == "membro-e@teste.com"


def test_convocar_reuniao_sem_membro_com_email_nao_envia(admin_client, monkeypatch):
    monkeypatch.setattr(
        governanca_service,
        "enviar_email",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("não deveria enviar sem e-mail cadastrado")),
    )

    _cpl_id, orgao_id, _pessoa_id, _membro_id = _cpl_orgao_e_membro_com_email(admin_client, "F", None)
    resposta = admin_client.post(
        f"/api/governanca/orgaos/{orgao_id}/reunioes",
        json={"titulo": "Reuniao sem email", "data_hora": "2026-06-01T10:00:00"},
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["email_convocacao_enviado"] is False
    assert corpo["email_convocacao_erro"] is None


def test_convocar_reuniao_ignora_membro_removido(admin_client, monkeypatch):
    chamadas = []
    monkeypatch.setattr(governanca_service, "enviar_email", lambda *a, **k: chamadas.append(a))

    _cpl_id, orgao_id, _pessoa_id, membro_id = _cpl_orgao_e_membro_com_email(
        admin_client, "G", "membro-g@teste.com"
    )
    admin_client.post(f"/api/governanca/membros/{membro_id}/remover", json={"motivo": "Saída"})

    resposta = admin_client.post(
        f"/api/governanca/orgaos/{orgao_id}/reunioes",
        json={"titulo": "Reuniao pos remocao", "data_hora": "2026-06-01T10:00:00"},
    )
    assert resposta.status_code == 201
    assert resposta.json()["email_convocacao_enviado"] is False
    assert chamadas == []


def test_convocar_reuniao_smtp_falha_nao_bloqueia_criacao(admin_client, monkeypatch):
    def _levanta_erro(*a, **k):
        raise RuntimeError("SMTP não configurado (SMTP_HOST ausente)")

    monkeypatch.setattr(governanca_service, "enviar_email", _levanta_erro)

    _cpl_id, orgao_id, _pessoa_id, _membro_id = _cpl_orgao_e_membro_com_email(
        admin_client, "H", "membro-h@teste.com"
    )
    resposta = admin_client.post(
        f"/api/governanca/orgaos/{orgao_id}/reunioes",
        json={"titulo": "Reuniao com falha de smtp", "data_hora": "2026-06-01T10:00:00"},
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["email_convocacao_enviado"] is False
    assert "SMTP" in corpo["email_convocacao_erro"]


def test_web_convocar_reuniao_mostra_confirmacao_e_status_do_email(admin_client, monkeypatch):
    monkeypatch.setattr(governanca_service, "enviar_email", lambda *a, **k: None)

    _cpl_id, orgao_id, _pessoa_id, _membro_id = _cpl_orgao_e_membro_com_email(
        admin_client, "I", "membro-i@teste.com"
    )
    resposta = admin_client.post(
        f"/painel/governanca/orgaos/{orgao_id}/reunioes",
        data={"titulo": "Reuniao web", "data_hora": "2026-06-01T10:00"},
    )
    assert resposta.status_code == 200
    assert "convocada com sucesso" in resposta.text.lower()
    assert "membro-i@teste.com" in resposta.text


# --- Documento de posse do órgão, também visível em Documentos (pedido explícito) --


def test_upload_documento_do_orgao_via_api(admin_client):
    cpl_id, orgao_id, _pessoa_id = _preparar_cpl_e_orgao(admin_client)
    resposta = admin_client.post(
        f"/api/documentos/cpls/{cpl_id}",
        data={"titulo": "Ata de posse", "categoria": "declaracao", "orgao_id": orgao_id},
        files={"arquivo": ("posse.pdf", b"conteudo de teste", "application/pdf")},
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["orgao_id"] == orgao_id

    listagem_cpl = admin_client.get(f"/api/documentos/cpls/{cpl_id}").json()
    assert any(d["id"] == corpo["id"] for d in listagem_cpl)

    listagem_orgao = admin_client.get(f"/api/documentos/orgaos/{orgao_id}").json()
    assert any(d["id"] == corpo["id"] for d in listagem_orgao)


def test_upload_documento_orgao_de_outra_cpl_e_rejeitado(admin_client):
    cpl_id, _orgao_id, _pessoa_id = _preparar_cpl_e_orgao(admin_client, "X1")
    _outra_cpl_id, outro_orgao_id, _p = _preparar_cpl_e_orgao(admin_client, "X2")
    resposta = admin_client.post(
        f"/api/documentos/cpls/{cpl_id}",
        data={"titulo": "Documento errado", "categoria": "declaracao", "orgao_id": outro_orgao_id},
        files={"arquivo": ("errado.pdf", b"conteudo", "application/pdf")},
    )
    assert resposta.status_code == 400


def test_web_upload_documento_orgao_redireciona_e_aparece_na_pagina(admin_client):
    cpl_id, orgao_id, _pessoa_id = _preparar_cpl_e_orgao(admin_client)
    resposta = admin_client.post(
        f"/painel/documentos/orgaos/{orgao_id}/anexos",
        data={"titulo": "Documento de posse", "categoria": "declaracao", "confidencialidade": "interno"},
        files={"arquivo": ("posse.pdf", b"conteudo de teste", "application/pdf")},
        follow_redirects=False,
    )
    assert resposta.status_code == 303
    assert resposta.headers["location"] == f"/painel/governanca/orgaos/{orgao_id}"

    pagina_orgao = admin_client.get(f"/painel/governanca/orgaos/{orgao_id}")
    assert "Documento de posse" in pagina_orgao.text

    pagina_documentos = admin_client.get(f"/painel/documentos/cpls/{cpl_id}")
    assert "Documento de posse" in pagina_documentos.text
