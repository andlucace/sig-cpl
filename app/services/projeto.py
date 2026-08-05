"""RF-041: relatório de execução do objeto, relatório financeiro e dossiê
de evidências de um projeto — mesmo padrão de resumo agregado pronto pra
formatação já usado em `app/services/indicadores.py` (RF-048), mas
escopado a um único `Projeto` em vez de uma CPL inteira (mesmo raciocínio
de `resumo_orgao`). Fecha o módulo de Projetos (RF-029 a RF-041) e
também o tipo de relatório "de projeto" que RF-048 tinha deixado em
aberto (ver `app/services/geracao_documentos.py`)."""

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.models.enums import StatusRecurso, StatusRisco, StatusTarefa
from app.models.projeto import (
    AlteracaoPlanoProjeto,
    AquisicaoProjeto,
    CotacaoAquisicao,
    DesembolsoProjeto,
    EntregaProjeto,
    EtapaProjeto,
    IndicadorProjeto,
    MetaProjeto,
    OrigemRecursoProjeto,
    RiscoProjeto,
)


def resumo_execucao_projeto(db: Session, projeto_id: uuid.UUID) -> dict:
    """RF-041/039/040: execução física do projeto — cronograma (etapas e
    marcos), metas, indicadores, entregas, riscos e alterações de plano."""

    etapas = (
        db.query(EtapaProjeto)
        .filter(EtapaProjeto.projeto_id == projeto_id)
        .order_by(EtapaProjeto.ordem)
        .all()
    )
    metas = db.query(MetaProjeto).filter(MetaProjeto.projeto_id == projeto_id).all()
    indicadores = db.query(IndicadorProjeto).filter(IndicadorProjeto.projeto_id == projeto_id).all()
    entregas = (
        db.query(EntregaProjeto)
        .filter(EntregaProjeto.projeto_id == projeto_id)
        .options(joinedload(EntregaProjeto.etapa))
        .all()
    )
    riscos = db.query(RiscoProjeto).filter(RiscoProjeto.projeto_id == projeto_id).all()
    alteracoes_plano = (
        db.query(AlteracaoPlanoProjeto)
        .filter(AlteracaoPlanoProjeto.projeto_id == projeto_id)
        .order_by(AlteracaoPlanoProjeto.data_solicitacao)
        .all()
    )

    return {
        "etapas": etapas,
        "total_etapas": len(etapas),
        "etapas_concluidas": sum(1 for e in etapas if e.status == StatusTarefa.CONCLUIDA),
        "marcos": [e for e in etapas if e.marco],
        "metas": metas,
        "total_metas": len(metas),
        "metas_concluidas": sum(1 for m in metas if m.status == StatusTarefa.CONCLUIDA),
        "indicadores": indicadores,
        "entregas": entregas,
        "total_entregas": len(entregas),
        "entregas_realizadas": sum(1 for e in entregas if e.data_entrega is not None),
        "entregas_aprovadas": sum(1 for e in entregas if e.aprovado),
        "riscos": riscos,
        "riscos_ativos": sum(1 for r in riscos if r.status == StatusRisco.ATIVO),
        "riscos_mitigados": sum(1 for r in riscos if r.status == StatusRisco.MITIGADO),
        "riscos_materializados": sum(1 for r in riscos if r.status == StatusRisco.MATERIALIZADO),
        "alteracoes_plano": alteracoes_plano,
        "alteracoes_plano_pendentes": sum(
            1 for a in alteracoes_plano if a.status == StatusRecurso.PENDENTE
        ),
    }


def resumo_financeiro_projeto(db: Session, projeto_id: uuid.UUID) -> dict:
    """RF-041/035/036/037/038: financeiro do projeto — origens de recursos
    (com saldo calculado, mesmo raciocínio já usado na tela de detalhe),
    aquisições/cotações e desembolsos/conciliação."""

    origens = (
        db.query(OrigemRecursoProjeto).filter(OrigemRecursoProjeto.projeto_id == projeto_id).all()
    )
    aquisicoes = (
        db.query(AquisicaoProjeto)
        .filter(AquisicaoProjeto.projeto_id == projeto_id)
        .options(joinedload(AquisicaoProjeto.etapa), joinedload(AquisicaoProjeto.origem_recurso))
        .all()
    )
    desembolsos = (
        db.query(DesembolsoProjeto)
        .filter(DesembolsoProjeto.projeto_id == projeto_id)
        .order_by(DesembolsoProjeto.data)
        .all()
    )

    saldos_por_origem = {
        origem.id: origem.valor
        - sum((d.valor for d in desembolsos if d.origem_recurso_id == origem.id), Decimal("0"))
        for origem in origens
    }
    total_previsto = sum((o.valor for o in origens), Decimal("0"))
    total_desembolsado = sum((d.valor for d in desembolsos), Decimal("0"))
    total_estimado_aquisicoes = sum(
        (a.valor_estimado for a in aquisicoes if a.valor_estimado is not None), Decimal("0")
    )

    return {
        "origens": origens,
        "saldos_por_origem": saldos_por_origem,
        "total_previsto": total_previsto,
        "aquisicoes": aquisicoes,
        "total_aquisicoes": len(aquisicoes),
        "total_estimado_aquisicoes": total_estimado_aquisicoes,
        "desembolsos": desembolsos,
        "total_desembolsado": total_desembolsado,
        "desembolsos_conciliados": sum(1 for d in desembolsos if d.conciliado),
        "desembolsos_pendentes_conciliacao": sum(1 for d in desembolsos if not d.conciliado),
        "saldo_total": total_previsto - total_desembolsado,
    }


def dossie_evidencias_projeto(db: Session, projeto_id: uuid.UUID) -> dict:
    """RF-041: dossiê de evidências — reúne num único lugar todos os
    documentos já vinculados ao projeto como comprovação/evidência em
    fatias anteriores (cotações, comprovantes de desembolso, evidência de
    mitigação de risco, documento de entrega); não cria nenhum vínculo
    novo, só agrega o que já existe."""

    cotacoes = (
        db.query(CotacaoAquisicao)
        .join(AquisicaoProjeto, CotacaoAquisicao.aquisicao_id == AquisicaoProjeto.id)
        .filter(AquisicaoProjeto.projeto_id == projeto_id, CotacaoAquisicao.documento_id.isnot(None))
        .options(joinedload(CotacaoAquisicao.documento), joinedload(CotacaoAquisicao.aquisicao))
        .all()
    )
    desembolsos = (
        db.query(DesembolsoProjeto)
        .filter(
            DesembolsoProjeto.projeto_id == projeto_id,
            DesembolsoProjeto.documento_comprovante_id.isnot(None),
        )
        .options(joinedload(DesembolsoProjeto.documento_comprovante))
        .all()
    )
    riscos = (
        db.query(RiscoProjeto)
        .filter(RiscoProjeto.projeto_id == projeto_id, RiscoProjeto.evidencia_documento_id.isnot(None))
        .options(joinedload(RiscoProjeto.evidencia_documento))
        .all()
    )
    entregas = (
        db.query(EntregaProjeto)
        .filter(EntregaProjeto.projeto_id == projeto_id, EntregaProjeto.documento_id.isnot(None))
        .options(joinedload(EntregaProjeto.documento))
        .all()
    )

    return {
        "cotacoes": cotacoes,
        "desembolsos": desembolsos,
        "riscos": riscos,
        "entregas": entregas,
        "total_evidencias": len(cotacoes) + len(desembolsos) + len(riscos) + len(entregas),
    }
