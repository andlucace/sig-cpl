"""RNF-012: métricas em memória e rastreamento de falhas — funções
puras/quase-puras, sem precisar do servidor rodando de verdade."""

from app.services import observabilidade
from app.services.observabilidade import metricas_requisicoes, registrar_requisicao


def test_registrar_requisicao_acumula_metricas():
    observabilidade._TOTAL_REQUISICOES = 0
    observabilidade._SOMA_DURACAO_MS = 0.0
    observabilidade._CONTAGEM_STATUS.clear()

    registrar_requisicao(200, 10.0)
    registrar_requisicao(200, 20.0)
    registrar_requisicao(500, 30.0)

    metricas = metricas_requisicoes()
    assert metricas["total_requisicoes"] == 3
    assert metricas["por_status"]["2xx"] == 2
    assert metricas["por_status"]["5xx"] == 1
    assert metricas["latencia_media_ms"] == 20.0


def test_falha_registrada_aparece_no_banco(db_session):
    from app.models.observabilidade import RegistroFalha
    from app.services.observabilidade import registrar_falha

    try:
        raise RuntimeError("erro de teste")
    except RuntimeError as exc:
        registrar_falha(db_session, metodo="GET", rota="/teste", excecao=exc)

    falhas = db_session.query(RegistroFalha).filter(RegistroFalha.rota == "/teste").all()
    assert len(falhas) == 1
    assert falhas[0].tipo_excecao == "RuntimeError"
    assert falhas[0].mensagem == "erro de teste"


def test_verificar_banco_retorna_true_com_conexao_valida(db_session):
    from app.services.observabilidade import verificar_banco

    assert verificar_banco(db_session) is True
