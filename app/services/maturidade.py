"""RF-024 a RF-028: cálculo de pontuação/nível sugerido e identificação de
lacunas de uma avaliação de maturidade, decisão final de nível (RN-016: só
humana, nunca automática) e alertas de vencimento do reconhecimento
(RF-028, recadastro bienal — RN-005)."""

import uuid
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.cpl import CPL
from app.models.enums import NivelMaturidade, StatusAvaliacao
from app.models.maturidade import (
    Avaliacao,
    AvaliacaoCriterio,
    Edital,
    ItemHabilitacaoJuridica,
    RequisitoHabilitacaoEdital,
)

VALIDADE_RECONHECIMENTO_DIAS = 365 * 2  # RN-005: recadastramento bienal


def calcular_pontuacao(avaliacao: Avaliacao) -> float | None:
    """Média ponderada das notas (0-100) pelo peso do critério."""

    notas = avaliacao.notas
    if not notas:
        return None
    soma_pesos = sum(n.criterio.peso for n in notas)
    if not soma_pesos:
        return None
    return round(sum(n.nota * n.criterio.peso for n in notas) / soma_pesos, 2)


def sugerir_nivel(edital: Edital, pontuacao: float | None) -> NivelMaturidade | None:
    """RF-026: sugestão automática — nunca grava direto em `CPL`, é só um
    insumo para a decisão humana (`decidir_nivel`)."""

    if pontuacao is None:
        return None
    limiares = (edital.limiar_cpl_em_desenvolvimento, edital.limiar_cpl_consolidada, edital.limiar_cpl_madura)
    if all(limiar is None for limiar in limiares):
        return None  # edital sem limiares configurados — não há base pra sugerir nada
    if edital.limiar_cpl_madura is not None and pontuacao >= edital.limiar_cpl_madura:
        return NivelMaturidade.CPL_MADURA
    if edital.limiar_cpl_consolidada is not None and pontuacao >= edital.limiar_cpl_consolidada:
        return NivelMaturidade.CPL_CONSOLIDADA
    if edital.limiar_cpl_em_desenvolvimento is not None and pontuacao >= edital.limiar_cpl_em_desenvolvimento:
        return NivelMaturidade.CPL_EM_DESENVOLVIMENTO
    return NivelMaturidade.AGLOMERADO_PRODUTIVO


def lacunas(avaliacao: Avaliacao) -> list[AvaliacaoCriterio]:
    """RF-026 ("indicar lacunas"): critérios cuja nota ficou abaixo da
    nota de corte definida para eles."""

    return [
        nota
        for nota in avaliacao.notas
        if nota.criterio.nota_corte is not None and nota.nota < nota.criterio.nota_corte
    ]


def simular_avaliacao(avaliacao: Avaliacao) -> dict:
    """RF-026 ("simular cenários"): pontuação/nível que resultariam de
    concluir a avaliação *agora*, com as notas já lançadas até este
    ponto — sem persistir nada (`concluir_avaliacao` é quem persiste de
    verdade). Reaproveita `calcular_pontuacao`/`sugerir_nivel`/`lacunas`,
    que já eram puras (só leem `avaliacao.notas`, nunca escrevem); só
    formata o resultado num dict pronto pra tela.

    Deixar de ser "simulação" e virar fato é uma ação humana explícita
    (`POST .../concluir`), nunca implícita por só olhar essa tela —
    mesma cautela de RN-016 (decisão de nível também é sempre humana)."""

    pontuacao = calcular_pontuacao(avaliacao)
    return {
        "pontuacao_simulada": pontuacao,
        "nivel_sugerido_simulado": sugerir_nivel(avaliacao.edital, pontuacao),
        "total_criterios": len(avaliacao.edital.criterios),
        "total_notas_lancadas": len(avaliacao.notas),
        "lacunas": lacunas(avaliacao),
    }


def concluir_avaliacao(db: Session, avaliacao: Avaliacao) -> Avaliacao:
    avaliacao.pontuacao_calculada = calcular_pontuacao(avaliacao)
    avaliacao.nivel_sugerido = sugerir_nivel(avaliacao.edital, avaliacao.pontuacao_calculada)
    avaliacao.status = StatusAvaliacao.CONCLUIDA
    db.commit()
    db.refresh(avaliacao)
    return avaliacao


def decidir_nivel(
    db: Session,
    avaliacao: Avaliacao,
    nivel_decidido: NivelMaturidade,
    parecer: str | None,
    decidido_por_id: uuid.UUID | None,
) -> Avaliacao:
    """RN-016: só este passo — nunca `concluir_avaliacao` — atualiza o
    nível "oficial" da CPL. RF-028: renova a validade do reconhecimento
    por mais um ciclo bienal a partir de hoje."""

    hoje = date.today()
    avaliacao.nivel_decidido = nivel_decidido
    avaliacao.parecer = parecer
    avaliacao.decidido_por_id = decidido_por_id
    avaliacao.data_decisao = hoje

    cpl = db.get(CPL, avaliacao.cpl_id)
    cpl.nivel_maturidade = nivel_decidido
    cpl.data_reconhecimento = hoje
    cpl.data_validade_reconhecimento = hoje + timedelta(days=VALIDADE_RECONHECIMENTO_DIAS)

    db.commit()
    db.refresh(avaliacao)
    return avaliacao


def cpls_com_vencimento_proximo(db: Session, dias: int = 90) -> list[CPL]:
    """RF-028: alerta antecipado de recadastramento — CPLs cujo
    reconhecimento vence dentro da janela ou já venceu."""

    limite = date.today() + timedelta(days=dias)
    return (
        db.query(CPL)
        .filter(
            CPL.ativo.is_(True),
            CPL.data_validade_reconhecimento.is_not(None),
            CPL.data_validade_reconhecimento <= limite,
        )
        .order_by(CPL.data_validade_reconhecimento)
        .all()
    )


def resumo_recadastramento(db: Session, cpl_id: uuid.UUID) -> dict:
    """RF-048: dossiê de recadastramento — nível de maturidade vigente,
    validade do reconhecimento (RN-005, bienal) e histórico completo de
    avaliações/decisões de uma CPL, pra instruir o processo de renovação.
    Reaproveita dados que o módulo de Maturidade já mantém; não introduz
    coleta nova."""

    cpl = db.get(CPL, cpl_id)
    avaliacoes = (
        db.query(Avaliacao)
        .filter(Avaliacao.cpl_id == cpl_id)
        .order_by(Avaliacao.data_avaliacao.desc())
        .all()
    )
    avaliacao_vigente = next((a for a in avaliacoes if a.nivel_decidido is not None), None)

    hoje = date.today()
    dias_para_vencer = (
        (cpl.data_validade_reconhecimento - hoje).days if cpl.data_validade_reconhecimento else None
    )

    return {
        "nivel_maturidade_atual": cpl.nivel_maturidade,
        "data_reconhecimento": cpl.data_reconhecimento,
        "data_validade_reconhecimento": cpl.data_validade_reconhecimento,
        "dias_para_vencer": dias_para_vencer,
        "vencimento_proximo_ou_vencido": dias_para_vencer is not None and dias_para_vencer <= 90,
        "avaliacoes": avaliacoes,
        "lacunas_avaliacao_vigente": lacunas(avaliacao_vigente) if avaliacao_vigente else [],
    }


def pacote_submissao_habilitacao(db: Session, cpl_id: uuid.UUID, edital_id: uuid.UUID) -> dict:
    """RF-043: dados do "pacote de submissão com índice e checklist" de
    uma CPL perante um edital — reaproveita o checklist de habilitação
    (RF-027) contra o template do próprio edital (RF-003, RequisitoHabilitacaoEdital)
    pra listar também o que ainda nem foi iniciado, não só o que já virou
    item, mais a avaliação de maturidade mais recente contra o mesmo
    edital, se existir. Nenhuma coleta nova — só compõe dados que os
    módulos de Maturidade/Habilitação já mantêm."""

    itens = (
        db.query(ItemHabilitacaoJuridica)
        .filter(ItemHabilitacaoJuridica.cpl_id == cpl_id, ItemHabilitacaoJuridica.edital_id == edital_id)
        .order_by(ItemHabilitacaoJuridica.created_at)
        .all()
    )
    descricoes_instanciadas = {item.descricao for item in itens}
    requisitos = (
        db.query(RequisitoHabilitacaoEdital)
        .filter(RequisitoHabilitacaoEdital.edital_id == edital_id)
        .all()
    )
    requisitos_nao_iniciados = [r for r in requisitos if r.descricao not in descricoes_instanciadas]

    avaliacao = (
        db.query(Avaliacao)
        .filter(Avaliacao.cpl_id == cpl_id, Avaliacao.edital_id == edital_id)
        .order_by(Avaliacao.data_avaliacao.desc())
        .first()
    )

    return {
        "itens_habilitacao": itens,
        "requisitos_nao_iniciados": requisitos_nao_iniciados,
        "avaliacao": avaliacao,
        "lacunas": lacunas(avaliacao) if avaliacao else [],
    }
