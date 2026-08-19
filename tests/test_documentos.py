"""RF-042: repositório de documentos — pedidos explícitos de código
sequencial, busca por nome/código, e visualização de quantas e quais
aprovações/assinaturas um documento exige (além do `aprovado`/`assinado`
booleano simples que já existia). Este módulo não tinha teste algum
antes desta fatia."""

from conftest import criar_usuario_com_papel, login_como

from app.models.enums import Papel


def _cpl_e_pessoa(admin_client, sufixo: str):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": f"CPL Documentos {sufixo}", "sigla": f"CPL-DOC-{sufixo}"}
    ).json()["id"]
    pessoa_id = admin_client.post("/api/pessoas", json={"nome": f"Pessoa {sufixo}"}).json()["id"]
    return cpl_id, pessoa_id


def _enviar_documento(admin_client, cpl_id, titulo="Documento de Teste", categoria="declaracao"):
    resposta = admin_client.post(
        f"/api/documentos/cpls/{cpl_id}",
        data={"titulo": titulo, "categoria": categoria},
        files={"arquivo": ("arquivo.pdf", b"conteudo de teste", "application/pdf")},
    )
    assert resposta.status_code == 201
    return resposta.json()


# --- Código sequencial (pedido explícito) ------------------------------------


def test_documento_criado_ganha_codigo(admin_client):
    cpl_id, _pessoa_id = _cpl_e_pessoa(admin_client, "A")
    documento = _enviar_documento(admin_client, cpl_id)
    assert documento["codigo"].startswith("DOC-")
    assert len(documento["codigo"]) == 10  # "DOC-" + 6 digitos


def test_dois_documentos_ganham_codigos_diferentes(admin_client):
    cpl_id, _pessoa_id = _cpl_e_pessoa(admin_client, "B")
    doc1 = _enviar_documento(admin_client, cpl_id, titulo="Primeiro")
    doc2 = _enviar_documento(admin_client, cpl_id, titulo="Segundo")
    assert doc1["codigo"] != doc2["codigo"]


# --- Busca por nome ou código (pedido explícito) -----------------------------


def test_busca_documento_por_nome(admin_client):
    cpl_id, _pessoa_id = _cpl_e_pessoa(admin_client, "C")
    _enviar_documento(admin_client, cpl_id, titulo="Estatuto Social")
    _enviar_documento(admin_client, cpl_id, titulo="Comprovante de Pagamento")

    resposta = admin_client.get(f"/api/documentos/cpls/{cpl_id}?q=estatuto")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["titulo"] == "Estatuto Social"


def test_busca_documento_por_codigo(admin_client):
    cpl_id, _pessoa_id = _cpl_e_pessoa(admin_client, "D")
    documento = _enviar_documento(admin_client, cpl_id, titulo="Ata de Reunião")

    resposta = admin_client.get(f"/api/documentos/cpls/{cpl_id}?q={documento['codigo']}")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["id"] == documento["id"]


def test_busca_documento_sem_resultado(admin_client):
    cpl_id, _pessoa_id = _cpl_e_pessoa(admin_client, "E")
    _enviar_documento(admin_client, cpl_id, titulo="Qualquer Documento")

    resposta = admin_client.get(f"/api/documentos/cpls/{cpl_id}?q=inexistente-xyz")
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_web_busca_documentos(admin_client):
    cpl_id, _pessoa_id = _cpl_e_pessoa(admin_client, "F")
    _enviar_documento(admin_client, cpl_id, titulo="Contrato Social")
    _enviar_documento(admin_client, cpl_id, titulo="Recibo Diverso")

    resposta = admin_client.get(f"/painel/documentos/cpls/{cpl_id}?q=contrato")
    assert resposta.status_code == 200
    assert "Contrato Social" in resposta.text
    assert "Recibo Diverso" not in resposta.text


# --- Aprovações e assinaturas exigidas (pedido explícito) --------------------


def test_criar_requisito_de_aprovacao(admin_client):
    cpl_id, pessoa_id = _cpl_e_pessoa(admin_client, "G")
    documento = _enviar_documento(admin_client, cpl_id)

    resposta = admin_client.post(
        f"/api/documentos/{documento['id']}/requisitos", json={"pessoa_id": pessoa_id, "tipo": "aprovacao"}
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["tipo"] == "aprovacao"
    assert corpo["concluido"] is False
    assert corpo["concluido_em"] is None


def test_criar_requisito_de_assinatura(admin_client):
    cpl_id, pessoa_id = _cpl_e_pessoa(admin_client, "H")
    documento = _enviar_documento(admin_client, cpl_id)

    resposta = admin_client.post(
        f"/api/documentos/{documento['id']}/requisitos", json={"pessoa_id": pessoa_id, "tipo": "assinatura"}
    )
    assert resposta.status_code == 201
    assert resposta.json()["tipo"] == "assinatura"


def test_listar_requisitos_do_documento(admin_client):
    cpl_id, pessoa_id = _cpl_e_pessoa(admin_client, "I")
    documento = _enviar_documento(admin_client, cpl_id)
    admin_client.post(
        f"/api/documentos/{documento['id']}/requisitos", json={"pessoa_id": pessoa_id, "tipo": "aprovacao"}
    )
    admin_client.post(
        f"/api/documentos/{documento['id']}/requisitos", json={"pessoa_id": pessoa_id, "tipo": "assinatura"}
    )

    resposta = admin_client.get(f"/api/documentos/{documento['id']}/requisitos")
    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_concluir_requisito(admin_client):
    cpl_id, pessoa_id = _cpl_e_pessoa(admin_client, "J")
    documento = _enviar_documento(admin_client, cpl_id)
    requisito = admin_client.post(
        f"/api/documentos/{documento['id']}/requisitos", json={"pessoa_id": pessoa_id, "tipo": "aprovacao"}
    ).json()

    resposta = admin_client.post(f"/api/documentos/requisitos/{requisito['id']}/concluir")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["concluido"] is True
    assert corpo["concluido_em"] is not None


def test_criar_requisito_exige_papel_gestao(client, admin_client, db_session):
    cpl_id, pessoa_id = _cpl_e_pessoa(admin_client, "K")
    documento = _enviar_documento(admin_client, cpl_id)

    leitor = criar_usuario_com_papel(db_session, Papel.CONSELHO_COMITE, cpl_id=cpl_id)
    client_leitor = login_como(client, leitor)
    resposta = client_leitor.post(
        f"/api/documentos/{documento['id']}/requisitos", json={"pessoa_id": pessoa_id, "tipo": "aprovacao"}
    )
    assert resposta.status_code == 403


def test_web_documento_detail_mostra_codigo(admin_client):
    cpl_id, _pessoa_id = _cpl_e_pessoa(admin_client, "L")
    documento = _enviar_documento(admin_client, cpl_id, titulo="Regimento Interno")

    resposta = admin_client.get(f"/painel/documentos/{documento['id']}")
    assert resposta.status_code == 200
    assert documento["codigo"] in resposta.text
    assert "Regimento Interno" in resposta.text


def test_web_criar_e_concluir_requisito(admin_client):
    cpl_id, pessoa_id = _cpl_e_pessoa(admin_client, "M")
    documento = _enviar_documento(admin_client, cpl_id)

    resposta = admin_client.post(
        f"/painel/documentos/{documento['id']}/requisitos",
        data={"pessoa_id": pessoa_id, "tipo": "assinatura"},
        follow_redirects=False,
    )
    assert resposta.status_code == 303
    assert resposta.headers["location"] == f"/painel/documentos/{documento['id']}"

    pagina = admin_client.get(f"/painel/documentos/{documento['id']}")
    assert "pendente" in pagina.text.lower()

    requisito_id = admin_client.get(f"/api/documentos/{documento['id']}/requisitos").json()[0]["id"]
    resposta_concluir = admin_client.post(
        f"/painel/documentos/requisitos/{requisito_id}/concluir", follow_redirects=False
    )
    assert resposta_concluir.status_code == 303

    pagina_apos = admin_client.get(f"/painel/documentos/{documento['id']}")
    assert "concluído" in pagina_apos.text.lower()


def test_lista_de_documentos_mostra_resumo_de_requisitos(admin_client):
    cpl_id, pessoa_id = _cpl_e_pessoa(admin_client, "N")
    documento = _enviar_documento(admin_client, cpl_id)
    admin_client.post(
        f"/api/documentos/{documento['id']}/requisitos", json={"pessoa_id": pessoa_id, "tipo": "aprovacao"}
    )
    admin_client.post(
        f"/api/documentos/{documento['id']}/requisitos", json={"pessoa_id": pessoa_id, "tipo": "assinatura"}
    )

    resposta = admin_client.get(f"/painel/documentos/cpls/{cpl_id}")
    assert resposta.status_code == 200
    assert "0/2 aprovações/assinaturas" in resposta.text
