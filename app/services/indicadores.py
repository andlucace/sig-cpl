"""RF-044 a RF-047: catálogo de indicadores com série histórica e resumo
agregado de dados cadastrais (empresas, empregos, faturamento, inovação,
exportação, ODS) — insumos para o painel/relatório de RF-045/048."""

import uuid
from collections import Counter
from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models.cadastro_dinamico import DiagnosticoCadastral
from app.models.entidade import EntidadeCPL
from app.models.enums import ResultadoDeliberacao, StatusReuniao, StatusTarefa
from app.models.governanca import Deliberacao, OrgaoGovernanca, Reuniao, TarefaGovernanca
from app.models.planejamento import (
    IndicadorEstrategico,
    IndicadorValorHistorico,
    MetaEstrategica,
    ObjetivoEstrategico,
    PlanejamentoEstrategico,
)


def catalogo_indicadores(db: Session, cpl_id: uuid.UUID) -> list[IndicadorEstrategico]:
    """RF-044: todos os indicadores estratégicos de uma CPL, através de
    todos os ciclos de planejamento — não só o mais recente."""

    return (
        db.query(IndicadorEstrategico)
        .join(ObjetivoEstrategico, IndicadorEstrategico.objetivo_id == ObjetivoEstrategico.id)
        .join(PlanejamentoEstrategico, ObjetivoEstrategico.planejamento_id == PlanejamentoEstrategico.id)
        .filter(PlanejamentoEstrategico.cpl_id == cpl_id)
        .options(joinedload(IndicadorEstrategico.responsavel), joinedload(IndicadorEstrategico.objetivo))
        .order_by(IndicadorEstrategico.nome)
        .all()
    )


def registrar_valor_indicador(
    db: Session,
    indicador: IndicadorEstrategico,
    valor: str | None,
    usuario_id: uuid.UUID,
    data_referencia: date | None = None,
    observacao: str | None = None,
) -> IndicadorEstrategico:
    """Atualiza `valor_atual` e, se houver valor de verdade (não é só
    limpar o campo), preserva a aferição em `IndicadorValorHistorico` —
    é assim que RF-044 vira "série histórica" e não só um valor mutável."""

    valor = valor.strip() if valor else None
    if valor:
        db.add(
            IndicadorValorHistorico(
                indicador_id=indicador.id,
                data_referencia=data_referencia or date.today(),
                valor=valor,
                observacao=observacao or None,
                registrado_por_id=usuario_id,
            )
        )
    indicador.valor_atual = valor
    db.commit()
    db.refresh(indicador)
    return indicador


def resumo_cadastral(db: Session, cpl_id: uuid.UUID) -> dict:
    """RF-046/047: agrega o que já é coletado via campanha de atualização
    cadastral (`DiagnosticoCadastral`) — não introduz coleta de dado novo.
    Sustentabilidade, certificações, contatos internacionais e
    digitalização (também citados no RF-047) não têm campo hoje no
    cadastro; ficam de fora deste resumo até existirem."""

    entidade_ids = [
        row[0]
        for row in db.query(EntidadeCPL.entidade_id)
        .filter(EntidadeCPL.cpl_id == cpl_id, EntidadeCPL.ativo.is_(True))
        .all()
    ]
    diagnosticos = (
        db.query(DiagnosticoCadastral).filter(DiagnosticoCadastral.entidade_id.in_(entidade_ids)).all()
        if entidade_ids
        else []
    )
    total_com_diagnostico = len(diagnosticos)

    def percentual(campo: str) -> float | None:
        if not total_com_diagnostico:
            return None
        positivos = sum(1 for d in diagnosticos if getattr(d, campo) is True)
        return round(100 * positivos / total_com_diagnostico, 1)

    ods_contador: Counter[str] = Counter()
    for d in diagnosticos:
        if not d.ods_relacionados:
            continue
        for item in d.ods_relacionados.split(","):
            item = item.strip()
            if item:
                ods_contador[item] += 1

    return {
        "total_empresas": len(entidade_ids),
        "total_com_diagnostico": total_com_diagnostico,
        "soma_empregos_diretos": sum(d.empregos_diretos or 0 for d in diagnosticos),
        "soma_empregos_indiretos": sum(d.empregos_indiretos or 0 for d in diagnosticos),
        "distribuicao_faturamento": dict(
            Counter(d.faturamento_faixa for d in diagnosticos if d.faturamento_faixa)
        ),
        "percentual_inovacao": percentual("realiza_inovacao"),
        "percentual_pd": percentual("realiza_pd"),
        "percentual_exportacao": percentual("exporta"),
        "percentual_associativismo": percentual("participacao_associativa"),
        "ods_mais_citados": ods_contador.most_common(5),
    }


def resumo_governanca(db: Session, cpl_id: uuid.UUID) -> dict:
    """RF-045: painel de governança da CPL (mesma contagem usada no
    `/painel` geral, mas escopada a uma única CPL em vez de todas as
    visíveis pelo usuário)."""

    total_orgaos = (
        db.query(OrgaoGovernanca)
        .filter(OrgaoGovernanca.cpl_id == cpl_id, OrgaoGovernanca.ativo.is_(True))
        .count()
    )
    reunioes_realizadas = (
        db.query(Reuniao)
        .join(OrgaoGovernanca, Reuniao.orgao_id == OrgaoGovernanca.id)
        .filter(OrgaoGovernanca.cpl_id == cpl_id, Reuniao.status == StatusReuniao.REALIZADA)
        .count()
    )
    deliberacoes_aprovadas = (
        db.query(Deliberacao)
        .join(Reuniao, Deliberacao.reuniao_id == Reuniao.id)
        .join(OrgaoGovernanca, Reuniao.orgao_id == OrgaoGovernanca.id)
        .filter(OrgaoGovernanca.cpl_id == cpl_id, Deliberacao.resultado == ResultadoDeliberacao.APROVADA)
        .count()
    )
    tarefas_q = db.query(TarefaGovernanca).filter(TarefaGovernanca.cpl_id == cpl_id)
    return {
        "total_orgaos": total_orgaos,
        "reunioes_realizadas": reunioes_realizadas,
        "deliberacoes_aprovadas": deliberacoes_aprovadas,
        "tarefas_concluidas": tarefas_q.filter(TarefaGovernanca.status == StatusTarefa.CONCLUIDA).count(),
        "tarefas_pendentes": tarefas_q.filter(
            TarefaGovernanca.status.in_([StatusTarefa.PENDENTE, StatusTarefa.EM_ANDAMENTO])
        ).count(),
    }


def resumo_planejamento(db: Session, cpl_id: uuid.UUID) -> dict:
    """RF-045: painel de planejamento estratégico da CPL — objetivos e
    metas por status, através de todos os ciclos."""

    objetivos_q = (
        db.query(ObjetivoEstrategico)
        .join(PlanejamentoEstrategico, ObjetivoEstrategico.planejamento_id == PlanejamentoEstrategico.id)
        .filter(PlanejamentoEstrategico.cpl_id == cpl_id)
    )
    metas_q = (
        db.query(MetaEstrategica)
        .join(ObjetivoEstrategico, MetaEstrategica.objetivo_id == ObjetivoEstrategico.id)
        .join(PlanejamentoEstrategico, ObjetivoEstrategico.planejamento_id == PlanejamentoEstrategico.id)
        .filter(PlanejamentoEstrategico.cpl_id == cpl_id)
    )
    return {
        "total_ciclos": db.query(PlanejamentoEstrategico).filter(PlanejamentoEstrategico.cpl_id == cpl_id).count(),
        "total_objetivos": objetivos_q.count(),
        "objetivos_concluidos": objetivos_q.filter(
            ObjetivoEstrategico.status == StatusTarefa.CONCLUIDA
        ).count(),
        "total_metas": metas_q.count(),
        "metas_concluidas": metas_q.filter(MetaEstrategica.status == StatusTarefa.CONCLUIDA).count(),
    }
