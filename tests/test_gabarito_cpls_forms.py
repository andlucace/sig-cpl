"""RF-012: campos adicionados a partir do gabarito real da planilha
"CPLS - FORMS.xlsx" ("Cadastro de Empresas Participantes das CPLs"),
anexado ao projeto — "Na campanha de atualização cadastral, adicionar
informações que por acaso não estejam no documento em anexo." Cobre
endereço estruturado, responsável pela empresa, elos da cadeia, capital
humano, inovação/internacionalização granulares, demandas e o
consentimento LGPD que o formulário público não pedia antes."""

from app.models.entidade import EntidadeElo
from app.models.enums import Elo, Papel
from app.models.pessoa import Pessoa, PessoaVinculo


def _cpl_entidade_e_token(admin_client, sufixo: str):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": f"CPL Gabarito {sufixo}", "sigla": f"CPL-GAB-{sufixo}"}
    ).json()["id"]
    entidade_id = admin_client.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": f"Empresa Gabarito {sufixo}"}
    ).json()["id"]
    admin_client.post(f"/api/cpls/{cpl_id}/entidades/{entidade_id}/vinculo")
    campanha_id = admin_client.post(
        f"/api/cadastro/cpls/{cpl_id}/campanhas", json={"titulo": f"Campanha Gabarito {sufixo}"}
    ).json()["id"]
    convite = admin_client.post(
        f"/api/cadastro/campanhas/{campanha_id}/convites", json={"entidade_id": entidade_id}
    ).json()
    return cpl_id, entidade_id, convite["token"]


# --- Formulário público mostra os novos campos --------------------------------


def test_formulario_publico_mostra_novos_campos(client, admin_client):
    _cpl_id, _entidade_id, token = _cpl_entidade_e_token(admin_client, "A")
    resposta = client.get(f"/atualizacao/{token}")
    assert resposta.status_code == 200
    assert 'name="cep"' in resposta.text
    assert 'name="numero"' in resposta.text
    assert 'name="bairro"' in resposta.text
    assert 'name="possui_filiais"' in resposta.text
    assert 'name="responsavel_nome"' in resposta.text
    assert 'name="responsavel_email"' in resposta.text
    assert 'name="responsavel_whatsapp"' in resposta.text
    assert 'name="elos"' in resposta.text
    assert 'name="funcionarios_clt"' in resposta.text
    assert 'name="possui_patente"' in resposta.text
    assert 'name="interesse_exportar"' in resposta.text
    assert 'name="necessidades_empresa"' in resposta.text
    assert 'name="consentimento_lgpd"' in resposta.text


# --- Consentimento LGPD é exigido ---------------------------------------------


def test_atualizacao_sem_consentimento_lgpd_e_rejeitada(client, admin_client):
    _cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "B")
    resposta = client.post(f"/atualizacao/{token}", data={"razao_social": "Empresa Gabarito B"})
    assert resposta.status_code == 400
    assert "consentir" in resposta.text.lower()

    diagnostico_resp = admin_client.get(f"/api/cadastro/entidades/{entidade_id}/diagnostico")
    assert diagnostico_resp.status_code == 404


def test_atualizacao_com_consentimento_marca_convite(client, admin_client, db_session):
    _cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "C")
    resposta = client.post(
        f"/atualizacao/{token}",
        data={"razao_social": "Empresa Gabarito C", "consentimento_lgpd": "sim"},
    )
    assert resposta.status_code == 200

    from app.models.cadastro_dinamico import CampanhaConvite

    convite = db_session.query(CampanhaConvite).filter(CampanhaConvite.entidade_id == entidade_id).first()
    assert convite.consentimento_lgpd is True
    assert convite.consentimento_em is not None


# --- Endereço estruturado e possui_filiais ------------------------------------


def test_atualizacao_publica_grava_endereco_estruturado_e_filiais(client, admin_client):
    _cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "D")
    resposta = client.post(
        f"/atualizacao/{token}",
        data={
            "razao_social": "Empresa Gabarito D",
            "cep": "12345-678",
            "numero": "100",
            "complemento": "Galpão 2",
            "bairro": "Distrito Industrial",
            "possui_filiais": "sim",
            "consentimento_lgpd": "sim",
        },
    )
    assert resposta.status_code == 200
    entidade = admin_client.get(f"/api/entidades/{entidade_id}").json()
    assert entidade["cep"] == "12345-678"
    assert entidade["numero"] == "100"
    assert entidade["complemento"] == "Galpão 2"
    assert entidade["bairro"] == "Distrito Industrial"
    assert entidade["possui_filiais"] is True


# --- Capital humano, inovação e internacionalização granulares ----------------


def test_atualizacao_publica_grava_capital_humano_e_inovacao_granular(client, admin_client):
    _cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "E")
    resposta = client.post(
        f"/atualizacao/{token}",
        data={
            "razao_social": "Empresa Gabarito E",
            "funcionarios_clt": "12",
            "terceirizados": "3",
            "aprendizes": "1",
            "colaboradores_pcd": "2",
            "possui_patente": "sim",
            "possui_registro_software": "nao",
            "importa": "sim",
            "interesse_exportar": "sim",
            "necessidades_empresa": "Acesso a linhas de crédito",
            "consentimento_lgpd": "sim",
        },
    )
    assert resposta.status_code == 200
    diagnostico = admin_client.get(f"/api/cadastro/entidades/{entidade_id}/diagnostico").json()
    assert diagnostico["funcionarios_clt"] == 12
    assert diagnostico["terceirizados"] == 3
    assert diagnostico["aprendizes"] == 1
    assert diagnostico["colaboradores_pcd"] == 2
    assert diagnostico["possui_patente"] is True
    assert diagnostico["possui_registro_software"] is False
    assert diagnostico["importa"] is True
    assert diagnostico["interesse_exportar"] is True
    assert diagnostico["necessidades_empresa"] == "Acesso a linhas de crédito"


# --- Elos da cadeia (checkboxes -> EntidadeElo) --------------------------------


def test_atualizacao_publica_sincroniza_elos_selecionados(client, admin_client, db_session):
    cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "F")
    resposta = client.post(
        f"/atualizacao/{token}",
        data={
            "razao_social": "Empresa Gabarito F",
            "elos": ["insumos", "producao"],
            "consentimento_lgpd": "sim",
        },
    )
    assert resposta.status_code == 200
    ativos = {
        e.elo
        for e in db_session.query(EntidadeElo)
        .filter(EntidadeElo.entidade_id == entidade_id, EntidadeElo.ativo.is_(True))
        .all()
    }
    assert ativos == {Elo.INSUMOS, Elo.PRODUCAO}


def test_atualizacao_publica_reenvio_desativa_elo_desmarcado(client, admin_client, db_session):
    _cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "G")
    client.post(
        f"/atualizacao/{token}",
        data={"razao_social": "Empresa Gabarito G", "elos": ["insumos", "producao"], "consentimento_lgpd": "sim"},
    )
    client.post(
        f"/atualizacao/{token}",
        data={"razao_social": "Empresa Gabarito G", "elos": ["producao"], "consentimento_lgpd": "sim"},
    )
    elos_db = {
        e.elo: e.ativo
        for e in db_session.query(EntidadeElo).filter(EntidadeElo.entidade_id == entidade_id).all()
    }
    assert elos_db[Elo.INSUMOS] is False
    assert elos_db[Elo.PRODUCAO] is True


# --- Responsável pela empresa -> Pessoa/PessoaVinculo --------------------------


def test_atualizacao_publica_vincula_responsavel(client, admin_client, db_session):
    cpl_id, entidade_id, token = _cpl_entidade_e_token(admin_client, "H")
    resposta = client.post(
        f"/atualizacao/{token}",
        data={
            "razao_social": "Empresa Gabarito H",
            "responsavel_nome": "Maria Responsável",
            "responsavel_cargo": "Sócia-administradora",
            "responsavel_telefone": "(11) 99999-0000",
            "responsavel_whatsapp": "(11) 98888-0000",
            "responsavel_email": "maria@empresah.com.br",
            "consentimento_lgpd": "sim",
        },
    )
    assert resposta.status_code == 200

    pessoa = db_session.query(Pessoa).filter(Pessoa.email == "maria@empresah.com.br").first()
    assert pessoa is not None
    assert pessoa.nome == "Maria Responsável"
    assert pessoa.whatsapp == "(11) 98888-0000"

    vinculo = db_session.query(PessoaVinculo).filter(PessoaVinculo.pessoa_id == pessoa.id).first()
    assert str(vinculo.entidade_id) == entidade_id
    assert str(vinculo.cpl_id) == cpl_id
    assert vinculo.papel == Papel.EMPRESA_MEMBRO
    assert vinculo.cargo == "Sócia-administradora"


def test_atualizacao_publica_sem_responsavel_nao_cria_pessoa(client, admin_client, db_session):
    _cpl_id, _entidade_id, token = _cpl_entidade_e_token(admin_client, "I")
    total_antes = db_session.query(Pessoa).count()
    resposta = client.post(
        f"/atualizacao/{token}",
        data={"razao_social": "Empresa Gabarito I", "consentimento_lgpd": "sim"},
    )
    assert resposta.status_code == 200
    assert db_session.query(Pessoa).count() == total_antes


# --- Resumo na tela da entidade -------------------------------------------------


def test_resumo_entidade_mostra_novos_campos_diagnostico(admin_client):
    _cpl_id, entidade_id, _token = _cpl_entidade_e_token(admin_client, "J")
    admin_client.put(
        f"/api/cadastro/entidades/{entidade_id}/diagnostico",
        json={
            "materia_prima_principal": "Aço inoxidável",
            "possui_patente": True,
            "necessidades_empresa": "Capacitação em exportação",
        },
    )
    resposta = admin_client.get(f"/painel/cadastro/entidades/{entidade_id}")
    assert resposta.status_code == 200
    assert "Aço inoxidável" in resposta.text
    assert "Possui patente?" in resposta.text
    assert "Capacitação em exportação" in resposta.text
