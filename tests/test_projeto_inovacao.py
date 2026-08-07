"""RF-031/032 + RF-052: demanda → matchmaking de inovação → conversão em
projeto. Cobre o fio condutor mais longo do sistema num teste só."""


def test_demanda_matchmaking_e_conversao_em_projeto(admin_client):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": "CPL Projeto", "sigla": "CPL-PROJ-01"}
    ).json()["id"]

    universidade_id = admin_client.post(
        "/api/entidades", json={"tipo": "universidade", "razao_social": "Universidade de Teste"}
    ).json()["id"]
    admin_client.post(
        f"/api/entidades/{universidade_id}/ofertas",
        json={"tipo": "tecnologia", "nome": "Laboratorio de automacao"},
    )

    demanda = admin_client.post(
        f"/api/projetos/cpls/{cpl_id}/demandas",
        json={"titulo": "Automacao da producao", "origem_tipo": "empresa"},
    )
    assert demanda.status_code == 201
    demanda_id = demanda.json()["id"]

    # RF-052: buscar competencia e sugerir match
    competencias = admin_client.get("/api/inovacao/competencias", params={"termo": "automacao"})
    assert competencias.status_code == 200
    assert any(e["id"] == universidade_id for e in competencias.json())

    match = admin_client.post(
        f"/api/inovacao/demandas/{demanda_id}/matches", json={"entidade_id": universidade_id}
    )
    assert match.status_code == 201
    assert match.json()["status"] == "sugerido"
    match_id = match.json()["id"]

    # não pode duplicar o mesmo par demanda+entidade
    duplicado = admin_client.post(
        f"/api/inovacao/demandas/{demanda_id}/matches", json={"entidade_id": universidade_id}
    )
    assert duplicado.status_code == 400

    firmar = admin_client.patch(f"/api/inovacao/matches/{match_id}", json={"status": "firmado"})
    assert firmar.status_code == 200
    assert firmar.json()["status"] == "firmado"

    projeto = admin_client.post(
        f"/api/projetos/demandas/{demanda_id}/converter",
        json={"titulo": "Projeto de Automacao"},
    )
    assert projeto.status_code == 201
    assert projeto.json()["estagio"] == "demanda"

    demanda_apos = admin_client.get(f"/api/projetos/cpls/{cpl_id}/demandas")
    convertida = next(d for d in demanda_apos.json() if d["id"] == demanda_id)
    assert convertida["status"] == "convertida_em_projeto"


def test_converter_demanda_ja_convertida_rejeitado(admin_client):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": "CPL Reconversao", "sigla": "CPL-RECONV-01"}
    ).json()["id"]
    demanda_id = admin_client.post(
        f"/api/projetos/cpls/{cpl_id}/demandas",
        json={"titulo": "Demanda unica", "origem_tipo": "empresa"},
    ).json()["id"]

    primeira = admin_client.post(
        f"/api/projetos/demandas/{demanda_id}/converter", json={"titulo": "Primeiro projeto"}
    )
    assert primeira.status_code == 201

    segunda = admin_client.post(
        f"/api/projetos/demandas/{demanda_id}/converter", json={"titulo": "Segundo projeto"}
    )
    assert segunda.status_code == 400
