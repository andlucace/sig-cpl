"""RF-044 a RF-047: catálogo de indicadores com série histórica e resumo
agregado de dados cadastrais (empresas, empregos, faturamento, inovação,
exportação, ODS) — insumos para o painel/relatório de RF-045/048."""

import uuid
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.cadastro_dinamico import DiagnosticoCadastral, DiagnosticoCadastralHistorico
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


def registrar_snapshot_diagnostico(db: Session, diagnostico: DiagnosticoCadastral) -> None:
    """RF-046: preserva um snapshot de empregos a cada atualização de
    diagnóstico (chamado pelos 3 pontos de escrita — API, formulário
    público de campanha e importação de planilha), já que
    `DiagnosticoCadastral` guarda só o valor atual. Sem isso, "novos
    empregos" (variação no tempo) não seria calculável — só o total
    corrente."""

    db.add(
        DiagnosticoCadastralHistorico(
            entidade_id=diagnostico.entidade_id,
            empregos_diretos=diagnostico.empregos_diretos,
            empregos_indiretos=diagnostico.empregos_indiretos,
        )
    )


def _novos_empregos_diretos(db: Session, entidade_ids: list[uuid.UUID], dias: int = 365) -> int:
    """RF-046: soma, entre as entidades informadas, o crescimento de
    empregos diretos entre o snapshot mais antigo dentro da janela e o
    mais recente disponível — requer ao menos 2 snapshots por entidade
    dentro do período pra contar (senão não há variação a medir, conta 0).
    Quedas não abatem o total (não é "saldo líquido" da CPL, é "empregos
    novos criados")."""

    if not entidade_ids:
        return 0

    limite = datetime.now(timezone.utc) - timedelta(days=dias)
    historico = (
        db.query(DiagnosticoCadastralHistorico)
        .filter(DiagnosticoCadastralHistorico.entidade_id.in_(entidade_ids))
        .order_by(DiagnosticoCadastralHistorico.registrado_em.asc())
        .all()
    )
    mais_antigo_na_janela: dict[uuid.UUID, DiagnosticoCadastralHistorico] = {}
    mais_recente: dict[uuid.UUID, DiagnosticoCadastralHistorico] = {}
    for h in historico:
        mais_recente[h.entidade_id] = h
        if h.registrado_em >= limite and h.entidade_id not in mais_antigo_na_janela:
            mais_antigo_na_janela[h.entidade_id] = h

    total = 0
    for entidade_id, recente in mais_recente.items():
        antigo = mais_antigo_na_janela.get(entidade_id)
        if antigo is None or antigo.id == recente.id:
            continue
        diferenca = (recente.empregos_diretos or 0) - (antigo.empregos_diretos or 0)
        if diferenca > 0:
            total += diferenca
    return total


def resumo_cadastral(db: Session, cpl_id: uuid.UUID) -> dict:
    """RF-046/047: agrega o que já é coletado via campanha de atualização
    cadastral (`DiagnosticoCadastral`) — não introduz coleta de dado novo."""

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

    def contador_lista(campo: str) -> Counter[str]:
        contador: Counter[str] = Counter()
        for d in diagnosticos:
            valor = getattr(d, campo)
            if not valor:
                continue
            for item in valor.split(","):
                item = item.strip()
                if item:
                    contador[item] += 1
        return contador

    return {
        "total_empresas": len(entidade_ids),
        "total_com_diagnostico": total_com_diagnostico,
        "soma_empregos_diretos": sum(d.empregos_diretos or 0 for d in diagnosticos),
        "soma_empregos_indiretos": sum(d.empregos_indiretos or 0 for d in diagnosticos),
        "novos_empregos_diretos_12_meses": _novos_empregos_diretos(db, entidade_ids),
        "distribuicao_faturamento": dict(
            Counter(d.faturamento_faixa for d in diagnosticos if d.faturamento_faixa)
        ),
        "percentual_inovacao": percentual("realiza_inovacao"),
        "percentual_pd": percentual("realiza_pd"),
        "percentual_exportacao": percentual("exporta"),
        "percentual_associativismo": percentual("participacao_associativa"),
        "ods_mais_citados": contador_lista("ods_relacionados").most_common(5),
        "percentual_qualificacao": percentual("oferece_qualificacao_colaboradores"),
        "percentual_sustentabilidade": percentual("adota_praticas_sustentabilidade"),
        "percentual_contatos_internacionais": percentual("possui_contatos_internacionais"),
        "percentual_certificacoes": percentual("possui_certificacoes"),
        "certificacoes_mais_citadas": contador_lista("certificacoes").most_common(5),
        "distribuicao_digitalizacao": dict(
            Counter(d.nivel_digitalizacao for d in diagnosticos if d.nivel_digitalizacao)
        ),
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
