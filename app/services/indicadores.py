"""RF-044 a RF-047: catálogo de indicadores com série histórica e resumo
agregado de dados cadastrais (empresas, empregos, faturamento, inovação,
exportação, ODS) — insumos para o painel/relatório de RF-045/048."""

import uuid
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.cadastro_dinamico import DiagnosticoCadastral, DiagnosticoCadastralHistorico
from app.models.documento import Documento
from app.models.entidade import EntidadeCPL
from app.models.enums import ResultadoDeliberacao, StatusReuniao, StatusTarefa
from app.models.governanca import Deliberacao, MembroOrgao, OrgaoGovernanca, Reuniao, TarefaGovernanca
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


def _novos_empregos_diretos_periodo(
    db: Session, entidade_ids: list[uuid.UUID], inicio: datetime, fim: datetime
) -> int:
    """RF-046/048: soma, entre as entidades informadas, o crescimento de
    empregos diretos entre o snapshot mais antigo e o mais recente, ambos
    dentro de [inicio, fim] — requer ao menos 2 snapshots por entidade
    dentro do período pra contar (senão não há variação a medir, conta 0).
    Quedas não abatem o total (não é "saldo líquido" da CPL, é "empregos
    novos criados"). Usado tanto pelo resumo cadastral (janela rolante de
    12 meses) quanto pelo relatório anual (ano-calendário exato)."""

    if not entidade_ids:
        return 0

    historico = (
        db.query(DiagnosticoCadastralHistorico)
        .filter(
            DiagnosticoCadastralHistorico.entidade_id.in_(entidade_ids),
            DiagnosticoCadastralHistorico.registrado_em >= inicio,
            DiagnosticoCadastralHistorico.registrado_em <= fim,
        )
        .order_by(DiagnosticoCadastralHistorico.registrado_em.asc())
        .all()
    )
    mais_antigo: dict[uuid.UUID, DiagnosticoCadastralHistorico] = {}
    mais_recente: dict[uuid.UUID, DiagnosticoCadastralHistorico] = {}
    for h in historico:
        if h.entidade_id not in mais_antigo:
            mais_antigo[h.entidade_id] = h
        mais_recente[h.entidade_id] = h

    total = 0
    for entidade_id, recente in mais_recente.items():
        antigo = mais_antigo[entidade_id]
        if antigo.id == recente.id:
            continue
        diferenca = (recente.empregos_diretos or 0) - (antigo.empregos_diretos or 0)
        if diferenca > 0:
            total += diferenca
    return total


def _novos_empregos_diretos(db: Session, entidade_ids: list[uuid.UUID], dias: int = 365) -> int:
    agora = datetime.now(timezone.utc)
    return _novos_empregos_diretos_periodo(db, entidade_ids, agora - timedelta(days=dias), agora)


VALIDADE_DIAGNOSTICO_DIAS = 365
"""RF-014 ("validade temporal"): um diagnóstico cadastral sem nenhuma
atualização há mais de um ano é considerado desatualizado — não fica
inválido nem some do sistema (a última resposta continua valendo até
alguém responder de novo), só é sinalizado pra CPL saber que vale
revalidar. Um ano não está fixado no documento de requisitos — mesmo
ciclo de atualização já usado como janela padrão em `_novos_empregos_diretos`."""


def diagnostico_desatualizado(diagnostico: DiagnosticoCadastral) -> bool:
    limite = datetime.now(timezone.utc) - timedelta(days=VALIDADE_DIAGNOSTICO_DIAS)
    atualizado_em = diagnostico.updated_at
    if atualizado_em.tzinfo is None:
        atualizado_em = atualizado_em.replace(tzinfo=timezone.utc)
    return atualizado_em < limite


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
        "total_diagnosticos_desatualizados": sum(1 for d in diagnosticos if diagnostico_desatualizado(d)),
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


def resumo_orgao(db: Session, orgao_id: uuid.UUID) -> dict:
    """RF-048: relatório de comissão — mesma lógica de `resumo_governanca`,
    mas escopada a um único órgão de governança em vez de toda a CPL.
    Serve qualquer `TipoOrgao` (conselho, câmara, comissão temática,
    grupo de trabalho) — o requisito fala especificamente de "comissão",
    mas não há razão técnica pra restringir a esse tipo. Tarefas só
    entram se estiverem ligadas a uma deliberação deste órgão
    (`TarefaGovernanca.deliberacao_id`); tarefas soltas da CPL como um
    todo não são atribuíveis a um órgão específico."""

    membros_ativos = (
        db.query(MembroOrgao)
        .filter(MembroOrgao.orgao_id == orgao_id, MembroOrgao.ativo.is_(True))
        .all()
    )
    reunioes = db.query(Reuniao).filter(Reuniao.orgao_id == orgao_id).order_by(Reuniao.data_hora.desc()).all()
    deliberacoes = (
        db.query(Deliberacao)
        .join(Reuniao, Deliberacao.reuniao_id == Reuniao.id)
        .filter(Reuniao.orgao_id == orgao_id)
        .order_by(Reuniao.data_hora.desc())
        .all()
    )
    tarefas_q = (
        db.query(TarefaGovernanca)
        .join(Deliberacao, TarefaGovernanca.deliberacao_id == Deliberacao.id)
        .join(Reuniao, Deliberacao.reuniao_id == Reuniao.id)
        .filter(Reuniao.orgao_id == orgao_id)
    )
    return {
        "membros_ativos": membros_ativos,
        "reunioes": reunioes,
        "reunioes_realizadas": sum(1 for r in reunioes if r.status == StatusReuniao.REALIZADA),
        "deliberacoes": deliberacoes,
        "deliberacoes_aprovadas": sum(1 for d in deliberacoes if d.resultado == ResultadoDeliberacao.APROVADA),
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


def resumo_anual(db: Session, cpl_id: uuid.UUID, ano: int) -> dict:
    """RF-048: relatório anual — mesma base de dados dos outros resumos,
    mas recortada ao ano-calendário informado (o executivo é o acumulado
    desde sempre; este é "o que aconteceu em {ano}"). "Concluída no ano"
    para tarefa/meta usa `updated_at` como aproximação — nenhum dos dois
    modelos guarda uma data de conclusão própria; documentado como
    recorte de escopo, não um bug (ver HANDOFF)."""

    inicio_data = date(ano, 1, 1)
    fim_data = date(ano, 12, 31)
    inicio_dt = datetime(ano, 1, 1, tzinfo=timezone.utc)
    fim_dt = datetime(ano, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    reunioes_no_ano = (
        db.query(Reuniao)
        .join(OrgaoGovernanca, Reuniao.orgao_id == OrgaoGovernanca.id)
        .filter(
            OrgaoGovernanca.cpl_id == cpl_id,
            Reuniao.status == StatusReuniao.REALIZADA,
            Reuniao.data_hora >= inicio_dt,
            Reuniao.data_hora <= fim_dt,
        )
        .count()
    )
    deliberacoes_no_ano = (
        db.query(Deliberacao)
        .join(Reuniao, Deliberacao.reuniao_id == Reuniao.id)
        .join(OrgaoGovernanca, Reuniao.orgao_id == OrgaoGovernanca.id)
        .filter(
            OrgaoGovernanca.cpl_id == cpl_id,
            Deliberacao.resultado == ResultadoDeliberacao.APROVADA,
            Reuniao.data_hora >= inicio_dt,
            Reuniao.data_hora <= fim_dt,
        )
        .count()
    )
    tarefas_concluidas_no_ano = (
        db.query(TarefaGovernanca)
        .filter(
            TarefaGovernanca.cpl_id == cpl_id,
            TarefaGovernanca.status == StatusTarefa.CONCLUIDA,
            TarefaGovernanca.updated_at >= inicio_dt,
            TarefaGovernanca.updated_at <= fim_dt,
        )
        .count()
    )
    metas_concluidas_no_ano = (
        db.query(MetaEstrategica)
        .join(ObjetivoEstrategico, MetaEstrategica.objetivo_id == ObjetivoEstrategico.id)
        .join(PlanejamentoEstrategico, ObjetivoEstrategico.planejamento_id == PlanejamentoEstrategico.id)
        .filter(
            PlanejamentoEstrategico.cpl_id == cpl_id,
            MetaEstrategica.status == StatusTarefa.CONCLUIDA,
            MetaEstrategica.updated_at >= inicio_dt,
            MetaEstrategica.updated_at <= fim_dt,
        )
        .count()
    )
    documentos_no_ano = (
        db.query(Documento)
        .filter(Documento.cpl_id == cpl_id, Documento.created_at >= inicio_dt, Documento.created_at <= fim_dt)
        .count()
    )
    indicadores_atualizados_no_ano = (
        db.query(IndicadorValorHistorico)
        .join(IndicadorEstrategico, IndicadorValorHistorico.indicador_id == IndicadorEstrategico.id)
        .join(ObjetivoEstrategico, IndicadorEstrategico.objetivo_id == ObjetivoEstrategico.id)
        .join(PlanejamentoEstrategico, ObjetivoEstrategico.planejamento_id == PlanejamentoEstrategico.id)
        .filter(
            PlanejamentoEstrategico.cpl_id == cpl_id,
            IndicadorValorHistorico.data_referencia >= inicio_data,
            IndicadorValorHistorico.data_referencia <= fim_data,
        )
        .count()
    )
    entidade_ids = [
        row[0]
        for row in db.query(EntidadeCPL.entidade_id)
        .filter(EntidadeCPL.cpl_id == cpl_id, EntidadeCPL.ativo.is_(True))
        .all()
    ]

    return {
        "ano": ano,
        "reunioes_realizadas_no_ano": reunioes_no_ano,
        "deliberacoes_aprovadas_no_ano": deliberacoes_no_ano,
        "tarefas_concluidas_no_ano": tarefas_concluidas_no_ano,
        "metas_concluidas_no_ano": metas_concluidas_no_ano,
        "documentos_gerados_no_ano": documentos_no_ano,
        "indicadores_atualizados_no_ano": indicadores_atualizados_no_ano,
        "novos_empregos_diretos_no_ano": _novos_empregos_diretos_periodo(
            db, entidade_ids, inicio_dt, fim_dt
        ),
    }
