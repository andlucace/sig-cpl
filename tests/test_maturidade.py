"""RF-024 a RF-028: edital, critério, avaliação com nota, conclusão
(RN-016: pontuação/nível só *sugeridos*) e decisão humana de nível."""


def _preparar_edital_e_cpl(admin_client):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": "CPL Maturidade", "sigla": "CPL-MAT-01"}
    ).json()["id"]
    edital = admin_client.post(
        "/api/maturidade/editais",
        json={
            "nome": "Edital de Teste",
            "ciclo": "2026",
            "limiar_cpl_em_desenvolvimento": 40.0,
            "limiar_cpl_consolidada": 65.0,
            "limiar_cpl_madura": 85.0,
        },
    ).json()
    criterio = admin_client.post(
        f"/api/maturidade/editais/{edital['id']}/criterios",
        json={"nome": "Governanca", "dimensao": "governanca", "peso": 1.0, "nota_corte": 60.0},
    ).json()
    return cpl_id, edital["id"], criterio["id"]


def test_avaliacao_concluida_calcula_pontuacao_e_nivel_sugerido(admin_client):
    cpl_id, edital_id, criterio_id = _preparar_edital_e_cpl(admin_client)

    avaliacao = admin_client.post(
        f"/api/maturidade/cpls/{cpl_id}/avaliacoes",
        json={"edital_id": edital_id, "data_avaliacao": "2026-06-01"},
    )
    assert avaliacao.status_code == 201
    avaliacao_id = avaliacao.json()["id"]

    nota = admin_client.put(
        f"/api/maturidade/avaliacoes/{avaliacao_id}/notas",
        json={"criterio_id": criterio_id, "nota": 80.0},
    )
    assert nota.status_code == 200

    concluir = admin_client.post(f"/api/maturidade/avaliacoes/{avaliacao_id}/concluir")
    assert concluir.status_code == 200
    corpo = concluir.json()
    assert corpo["pontuacao_calculada"] == 80.0
    assert corpo["nivel_sugerido"] == "cpl_consolidada"
    # RN-016: nível oficial não muda sozinho ao concluir a avaliação
    assert corpo["nivel_decidido"] is None


def test_decidir_nivel_e_o_unico_jeito_de_mudar_nivel_oficial(admin_client):
    cpl_id, edital_id, criterio_id = _preparar_edital_e_cpl(admin_client)
    avaliacao_id = admin_client.post(
        f"/api/maturidade/cpls/{cpl_id}/avaliacoes",
        json={"edital_id": edital_id, "data_avaliacao": "2026-06-01"},
    ).json()["id"]
    admin_client.put(
        f"/api/maturidade/avaliacoes/{avaliacao_id}/notas", json={"criterio_id": criterio_id, "nota": 90.0}
    )
    admin_client.post(f"/api/maturidade/avaliacoes/{avaliacao_id}/concluir")

    antes = admin_client.get(f"/api/cpls/{cpl_id}")
    assert antes.json()["nivel_maturidade"] is None

    decisao = admin_client.post(
        f"/api/maturidade/avaliacoes/{avaliacao_id}/decidir",
        json={"nivel_decidido": "cpl_madura", "parecer": "Nivel confirmado apos analise."},
    )
    assert decisao.status_code == 200

    depois = admin_client.get(f"/api/cpls/{cpl_id}")
    assert depois.json()["nivel_maturidade"] == "cpl_madura"


def test_requisitos_do_edital_instanciam_checklist_da_cpl_sem_duplicar(admin_client):
    cpl_id, edital_id, _criterio_id = _preparar_edital_e_cpl(admin_client)
    admin_client.post(
        f"/api/maturidade/editais/{edital_id}/requisitos-habilitacao",
        json={"descricao": "Estatuto social", "obrigatorio": True},
    )

    primeira = admin_client.post(
        f"/api/maturidade/cpls/{cpl_id}/habilitacao/usar-requisitos-edital",
        params={"edital_id": edital_id},
    )
    assert primeira.status_code == 201
    assert len(primeira.json()) == 1

    segunda = admin_client.post(
        f"/api/maturidade/cpls/{cpl_id}/habilitacao/usar-requisitos-edital",
        params={"edital_id": edital_id},
    )
    assert segunda.status_code == 201
    assert segunda.json() == []  # idempotente: já instanciado, não duplica
