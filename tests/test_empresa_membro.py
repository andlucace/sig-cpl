"""RBAC: o que um EMPRESA_MEMBRO pode ver/fazer — descoberto que esse
papel não estava incluído em nenhum grupo PAPEIS_* usado pelas rotas
(existia só no enum), então quem tinha só esse papel não acessava
nenhuma funcionalidade. Escopo desenhado com o usuário: dashboard de
indicadores da própria CPL (PAPEIS_LEITURA_MEMBRO), a própria entidade
(entidade_e_da_pessoa, via PessoaVinculo) e eventos da própria CPL com
autoinscrição — governança, documentos, maturidade, projetos e
planejamento continuam fechados de propósito."""

import uuid
from datetime import UTC, datetime, timedelta

from conftest import criar_usuario_com_papel, login_como

from app.core.rbac import cpl_ids_membro, entidade_e_da_pessoa
from app.models.enums import Papel
from app.models.evento import InscricaoEvento
from app.models.pessoa import Pessoa, PessoaVinculo


def _cpl_e_entidade(admin_client, sufixo: str):
    cpl_id = admin_client.post(
        "/api/cpls", json={"nome": f"CPL Membro {sufixo}", "sigla": f"CPL-MEMBRO-{sufixo}"}
    ).json()["id"]
    entidade_id = admin_client.post(
        "/api/entidades", json={"tipo": "empresa", "razao_social": f"Empresa {sufixo}"}
    ).json()["id"]
    admin_client.post(f"/api/cpls/{cpl_id}/entidades/{entidade_id}/vinculo")
    return cpl_id, entidade_id


def _membro_com_pessoa_vinculada(db_session, cpl_id, entidade_id, sufixo: str):
    """Cria o cenário completo: Usuario com papel EMPRESA_MEMBRO escopado
    à CPL, Pessoa e o PessoaVinculo que liga as duas — exatamente o que
    faltava pra juliana.prado no caso real que motivou este desenho."""

    usuario = criar_usuario_com_papel(db_session, Papel.EMPRESA_MEMBRO, cpl_id=uuid.UUID(cpl_id))
    pessoa = Pessoa(nome=f"Pessoa {sufixo}", email=f"pessoa-{sufixo}@teste.com")
    db_session.add(pessoa)
    db_session.flush()
    db_session.add(
        PessoaVinculo(
            pessoa_id=pessoa.id,
            entidade_id=uuid.UUID(entidade_id),
            cpl_id=uuid.UUID(cpl_id),
            papel=Papel.EMPRESA_MEMBRO,
            cargo="Representante",
            data_inicio=datetime.now(UTC).date(),
        )
    )
    usuario.pessoa_id = pessoa.id
    db_session.commit()
    db_session.refresh(usuario)
    return usuario, pessoa


def test_cpl_ids_membro_retorna_so_cpls_do_papel_empresa_membro(admin_client, db_session):
    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "A")
    usuario, _pessoa = _membro_com_pessoa_vinculada(db_session, cpl_id, entidade_id, "A")
    assert cpl_ids_membro(db_session, usuario) == {uuid.UUID(cpl_id)}


def test_entidade_e_da_pessoa_verdadeiro_pra_propria_e_falso_pra_outra(admin_client, db_session):
    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "B")
    _cpl_id_outra, entidade_outra_id = _cpl_e_entidade(admin_client, "B-outra")
    usuario, _pessoa = _membro_com_pessoa_vinculada(db_session, cpl_id, entidade_id, "B")

    assert entidade_e_da_pessoa(db_session, usuario, uuid.UUID(entidade_id)) is True
    assert entidade_e_da_pessoa(db_session, usuario, uuid.UUID(entidade_outra_id)) is False


def test_empresa_membro_ve_dashboard_indicadores_da_propria_cpl(admin_client, client, db_session):
    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "C")
    usuario, _pessoa = _membro_com_pessoa_vinculada(db_session, cpl_id, entidade_id, "C")
    client_membro = login_como(client, usuario)

    resposta = client_membro.get(f"/painel/indicadores/cpls/{cpl_id}")
    assert resposta.status_code == 200


def test_empresa_membro_nao_ve_dashboard_de_outra_cpl(admin_client, client, db_session):
    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "D")
    cpl_outra_id, _entidade_outra_id = _cpl_e_entidade(admin_client, "D-outra")
    usuario, _pessoa = _membro_com_pessoa_vinculada(db_session, cpl_id, entidade_id, "D")
    client_membro = login_como(client, usuario)

    resposta = client_membro.get(f"/painel/indicadores/cpls/{cpl_outra_id}")
    assert resposta.status_code == 403


def test_empresa_membro_ve_a_propria_entidade(admin_client, client, db_session):
    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "E")
    usuario, _pessoa = _membro_com_pessoa_vinculada(db_session, cpl_id, entidade_id, "E")
    client_membro = login_como(client, usuario)

    resposta = client_membro.get(f"/painel/cadastro/entidades/{entidade_id}")
    assert resposta.status_code == 200


def test_empresa_membro_nao_ve_entidade_de_outra_empresa(admin_client, client, db_session):
    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "F")
    _cpl_outra_id, entidade_outra_id = _cpl_e_entidade(admin_client, "F-outra")
    usuario, _pessoa = _membro_com_pessoa_vinculada(db_session, cpl_id, entidade_id, "F")
    client_membro = login_como(client, usuario)

    resposta = client_membro.get(
        f"/painel/cadastro/entidades/{entidade_outra_id}", follow_redirects=False
    )
    assert resposta.status_code == 303


def test_empresa_membro_ve_e_se_autoinscreve_em_evento_da_propria_cpl(admin_client, client, db_session):
    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "G")
    usuario, pessoa = _membro_com_pessoa_vinculada(db_session, cpl_id, entidade_id, "G")

    evento_id = admin_client.post(
        "/api/eventos",
        json={
            "cpl_id": cpl_id,
            "titulo": "Capacitação de teste",
            "tipo": "capacitacao",
            "data_inicio": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
        },
    ).json()["id"]

    client_membro = login_como(client, usuario)
    resposta_detalhe = client_membro.get(f"/painel/eventos/{evento_id}")
    assert resposta_detalhe.status_code == 200

    resposta_inscricao = client_membro.post(
        f"/painel/eventos/{evento_id}/inscrever-me", follow_redirects=False
    )
    assert resposta_inscricao.status_code == 303

    # Consulta direto no banco, não via `admin_client` — `client`/`admin_client`
    # compartilham a mesma instância de TestClient, e `login_como` acima já
    # sobrescreveu o header de autenticação dela pro token da própria membro.
    inscricao = (
        db_session.query(InscricaoEvento)
        .filter(InscricaoEvento.evento_id == uuid.UUID(evento_id), InscricaoEvento.pessoa_id == pessoa.id)
        .first()
    )
    assert inscricao is not None


def test_empresa_membro_nao_se_autoinscreve_duas_vezes(admin_client, client, db_session):
    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "H")
    usuario, _pessoa = _membro_com_pessoa_vinculada(db_session, cpl_id, entidade_id, "H")
    evento_id = admin_client.post(
        "/api/eventos",
        json={
            "cpl_id": cpl_id,
            "titulo": "Mentoria de teste",
            "tipo": "mentoria",
            "data_inicio": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
        },
    ).json()["id"]
    client_membro = login_como(client, usuario)
    client_membro.post(f"/painel/eventos/{evento_id}/inscrever-me")

    resposta = client_membro.post(f"/painel/eventos/{evento_id}/inscrever-me")
    assert resposta.status_code == 400


def test_empresa_membro_nao_se_autoinscreve_em_evento_de_outra_cpl(admin_client, client, db_session):
    cpl_id, entidade_id = _cpl_e_entidade(admin_client, "I")
    cpl_outra_id, _entidade_outra_id = _cpl_e_entidade(admin_client, "I-outra")
    usuario, _pessoa = _membro_com_pessoa_vinculada(db_session, cpl_id, entidade_id, "I")
    evento_id = admin_client.post(
        "/api/eventos",
        json={
            "cpl_id": cpl_outra_id,
            "titulo": "Missão técnica de outra CPL",
            "tipo": "missao_tecnica",
            "data_inicio": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
        },
    ).json()["id"]
    client_membro = login_como(client, usuario)

    resposta = client_membro.post(f"/painel/eventos/{evento_id}/inscrever-me")
    assert resposta.status_code == 403


def test_usuario_sem_pessoa_vinculada_nao_consegue_autoinscrever(admin_client, client, db_session):
    cpl_id, _entidade_id = _cpl_e_entidade(admin_client, "J")
    usuario = criar_usuario_com_papel(db_session, Papel.EMPRESA_MEMBRO, cpl_id=uuid.UUID(cpl_id))
    evento_id = admin_client.post(
        "/api/eventos",
        json={
            "cpl_id": cpl_id,
            "titulo": "Evento sem pessoa vinculada",
            "tipo": "capacitacao",
            "data_inicio": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
        },
    ).json()["id"]
    client_membro = login_como(client, usuario)

    resposta = client_membro.post(f"/painel/eventos/{evento_id}/inscrever-me")
    assert resposta.status_code == 400
