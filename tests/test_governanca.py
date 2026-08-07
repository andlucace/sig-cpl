"""RF-015 a RF-020: órgão, membro, reunião, deliberação, voto e ata —
smoke test do fluxo completo de governança."""


def _preparar_cpl_e_orgao(admin_client):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": "CPL Governanca", "sigla": "CPL-GOV-01"}
    ).json()["id"]
    orgao_id = admin_client.post(
        f"/api/governanca/cpls/{cpl_id}/orgaos",
        json={"nome": "Conselho Gestor", "tipo": "conselho"},
    ).json()["id"]
    pessoa_id = admin_client.post("/api/pessoas", json={"nome": "Pessoa da Governanca"}).json()["id"]
    return cpl_id, orgao_id, pessoa_id


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
