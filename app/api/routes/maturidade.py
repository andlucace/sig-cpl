import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import (
    PAPEIS_AVALIACAO_EXECUCAO,
    PAPEIS_EDITAL_GESTAO,
    PAPEIS_GESTAO,
    PAPEIS_GOVERNANCA_LEITURA,
    cpl_ids_visiveis,
    verificar_papel,
)
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.maturidade import (
    Avaliacao,
    AvaliacaoCriterio,
    CriterioMaturidade,
    Edital,
    ItemHabilitacaoJuridica,
    RecursoAvaliacao,
)
from app.models.usuario import Usuario
from app.schemas.maturidade import (
    AvaliacaoCreate,
    AvaliacaoCriterioRead,
    AvaliacaoCriterioUpsert,
    AvaliacaoRead,
    CriterioMaturidadeCreate,
    CriterioMaturidadeRead,
    DecisaoNivelCreate,
    EditalCreate,
    EditalRead,
    EditalUpdate,
    ItemHabilitacaoAnalise,
    ItemHabilitacaoCreate,
    ItemHabilitacaoRead,
    RecursoAvaliacaoCreate,
    RecursoAvaliacaoDecisao,
    RecursoAvaliacaoRead,
    SimulacaoAvaliacaoRead,
)
from app.models.documento import Documento
from app.models.enums import CategoriaDocumento, ConfidencialidadeDocumento
from app.schemas.cpl import CPLRead
from app.schemas.documento import DocumentoRead
from app.services.armazenamento import salvar_arquivo
from app.services.geracao_documentos import gerar_pdf_relatorio_recadastramento
from app.services.maturidade import (
    concluir_avaliacao,
    cpls_com_vencimento_proximo,
    decidir_nivel,
    lacunas,
    resumo_recadastramento,
    simular_avaliacao,
)

router = APIRouter(prefix="/maturidade", tags=["Maturidade e reconhecimento"])


def _get_edital_or_404(db: Session, edital_id: uuid.UUID) -> Edital:
    edital = db.get(Edital, edital_id)
    if edital is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Edital não encontrado.")
    return edital


def _get_avaliacao_or_404(db: Session, avaliacao_id: uuid.UUID) -> Avaliacao:
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avaliação não encontrada.")
    return avaliacao


# --- Editais e critérios (RF-024/RN-006) — globais, só administrador -------


@router.post("/editais", response_model=EditalRead, status_code=status.HTTP_201_CREATED)
def criar_edital(
    dados: EditalCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> Edital:
    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    edital = Edital(**dados.model_dump())
    db.add(edital)
    db.commit()
    db.refresh(edital)
    return edital


@router.get("/editais", response_model=list[EditalRead])
def listar_editais(
    db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> list[Edital]:
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=None)
    return db.query(Edital).order_by(Edital.ciclo.desc()).all()


@router.patch("/editais/{edital_id}", response_model=EditalRead)
def atualizar_edital(
    edital_id: uuid.UUID,
    dados: EditalUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Edital:
    edital = _get_edital_or_404(db, edital_id)
    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(edital, campo, valor)
    db.commit()
    db.refresh(edital)
    return edital


@router.post(
    "/editais/{edital_id}/criterios", response_model=CriterioMaturidadeRead, status_code=status.HTTP_201_CREATED
)
def criar_criterio(
    edital_id: uuid.UUID,
    dados: CriterioMaturidadeCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> CriterioMaturidade:
    _get_edital_or_404(db, edital_id)
    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    criterio = CriterioMaturidade(edital_id=edital_id, **dados.model_dump())
    db.add(criterio)
    db.commit()
    db.refresh(criterio)
    return criterio


@router.get("/editais/{edital_id}/criterios", response_model=list[CriterioMaturidadeRead])
def listar_criterios(
    edital_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[CriterioMaturidade]:
    _get_edital_or_404(db, edital_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=None)
    return db.query(CriterioMaturidade).filter(CriterioMaturidade.edital_id == edital_id).all()


# --- Avaliações (RF-024/025/026) --------------------------------------------


@router.post(
    "/cpls/{cpl_id}/avaliacoes", response_model=AvaliacaoRead, status_code=status.HTTP_201_CREATED
)
def criar_avaliacao(
    cpl_id: uuid.UUID,
    dados: AvaliacaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Avaliacao:
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    _get_edital_or_404(db, dados.edital_id)
    verificar_papel(db, usuario_atual, PAPEIS_AVALIACAO_EXECUCAO, cpl_id=cpl_id)
    avaliacao = Avaliacao(cpl_id=cpl_id, avaliador_id=usuario_atual.id, **dados.model_dump())
    db.add(avaliacao)
    db.commit()
    db.refresh(avaliacao)
    return avaliacao


@router.get("/cpls/{cpl_id}/avaliacoes", response_model=list[AvaliacaoRead])
def listar_avaliacoes(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Avaliacao]:
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return (
        db.query(Avaliacao)
        .filter(Avaliacao.cpl_id == cpl_id)
        .order_by(Avaliacao.data_avaliacao.desc())
        .all()
    )


@router.get("/avaliacoes/{avaliacao_id}", response_model=AvaliacaoRead)
def obter_avaliacao(
    avaliacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Avaliacao:
    avaliacao = _get_avaliacao_or_404(db, avaliacao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=avaliacao.cpl_id)
    return avaliacao


@router.put("/avaliacoes/{avaliacao_id}/notas", response_model=AvaliacaoCriterioRead)
def lancar_nota(
    avaliacao_id: uuid.UUID,
    dados: AvaliacaoCriterioUpsert,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> AvaliacaoCriterio:
    """RF-025: lança (ou substitui) a nota/evidência de um critério dentro
    da avaliação — chamável múltiplas vezes até a conclusão."""

    avaliacao = _get_avaliacao_or_404(db, avaliacao_id)
    verificar_papel(db, usuario_atual, PAPEIS_AVALIACAO_EXECUCAO, cpl_id=avaliacao.cpl_id)

    nota = (
        db.query(AvaliacaoCriterio)
        .filter(
            AvaliacaoCriterio.avaliacao_id == avaliacao_id,
            AvaliacaoCriterio.criterio_id == dados.criterio_id,
        )
        .first()
    )
    if nota is None:
        nota = AvaliacaoCriterio(avaliacao_id=avaliacao_id, criterio_id=dados.criterio_id, nota=dados.nota)
        db.add(nota)
    nota.nota = dados.nota
    nota.evidencia_documento_id = dados.evidencia_documento_id
    nota.observacao = dados.observacao
    db.commit()
    db.refresh(nota)
    return nota


@router.get("/avaliacoes/{avaliacao_id}/simulacao", response_model=SimulacaoAvaliacaoRead)
def obter_simulacao(
    avaliacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> dict:
    """RF-026: pontuação/nível sugerido/lacunas com base nas notas já
    lançadas até agora — sem precisar concluir a avaliação pra ver."""

    avaliacao = _get_avaliacao_or_404(db, avaliacao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=avaliacao.cpl_id)
    return simular_avaliacao(avaliacao)


@router.get("/avaliacoes/{avaliacao_id}/lacunas", response_model=list[AvaliacaoCriterioRead])
def obter_lacunas(
    avaliacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[AvaliacaoCriterio]:
    avaliacao = _get_avaliacao_or_404(db, avaliacao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=avaliacao.cpl_id)
    return lacunas(avaliacao)


@router.post("/avaliacoes/{avaliacao_id}/concluir", response_model=AvaliacaoRead)
def concluir(
    avaliacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Avaliacao:
    """RF-026: calcula pontuação e nível sugerido — não decide o nível
    oficial da CPL (RN-016), ver `POST /avaliacoes/{id}/decidir`."""

    avaliacao = _get_avaliacao_or_404(db, avaliacao_id)
    verificar_papel(db, usuario_atual, PAPEIS_AVALIACAO_EXECUCAO, cpl_id=avaliacao.cpl_id)
    return concluir_avaliacao(db, avaliacao)


@router.post("/avaliacoes/{avaliacao_id}/decidir", response_model=AvaliacaoRead)
def decidir(
    avaliacao_id: uuid.UUID,
    dados: DecisaoNivelCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Avaliacao:
    """RN-016: decisão humana do nível de maturidade — só quem tem papel de
    gestão decide (mais restrito que quem pode avaliar/lançar nota)."""

    avaliacao = _get_avaliacao_or_404(db, avaliacao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=avaliacao.cpl_id)
    return decidir_nivel(db, avaliacao, dados.nivel_decidido, dados.parecer, dados.decidido_por_id)


# --- Recursos (RF-027) -------------------------------------------------------


@router.post(
    "/avaliacoes/{avaliacao_id}/recurso", response_model=RecursoAvaliacaoRead, status_code=status.HTTP_201_CREATED
)
def solicitar_recurso(
    avaliacao_id: uuid.UUID,
    dados: RecursoAvaliacaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> RecursoAvaliacao:
    avaliacao = _get_avaliacao_or_404(db, avaliacao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=avaliacao.cpl_id)
    if avaliacao.recurso is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Já existe um recurso para esta avaliação.")
    recurso = RecursoAvaliacao(
        avaliacao_id=avaliacao_id, justificativa=dados.justificativa, solicitado_por_id=usuario_atual.id
    )
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


@router.get("/avaliacoes/{avaliacao_id}/recurso", response_model=RecursoAvaliacaoRead)
def obter_recurso(
    avaliacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> RecursoAvaliacao:
    avaliacao = _get_avaliacao_or_404(db, avaliacao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=avaliacao.cpl_id)
    if avaliacao.recurso is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nenhum recurso solicitado para esta avaliação.")
    return avaliacao.recurso


@router.post("/recursos/{recurso_id}/decidir", response_model=RecursoAvaliacaoRead)
def decidir_recurso(
    recurso_id: uuid.UUID,
    dados: RecursoAvaliacaoDecisao,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> RecursoAvaliacao:
    """Decisão do recurso é de quem gere os editais (administrador da
    plataforma) — autoridade diferente de quem avaliou/decidiu o nível
    originalmente, por ser uma contestação."""

    recurso = db.get(RecursoAvaliacao, recurso_id)
    if recurso is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recurso não encontrado.")
    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    recurso.status = dados.status
    recurso.parecer_decisao = dados.parecer_decisao
    recurso.decidido_por_id = usuario_atual.id
    recurso.data_decisao = date.today()
    db.commit()
    db.refresh(recurso)
    return recurso


# --- Habilitação jurídica (RF-027) -------------------------------------------


@router.post(
    "/cpls/{cpl_id}/habilitacao", response_model=ItemHabilitacaoRead, status_code=status.HTTP_201_CREATED
)
def criar_item_habilitacao(
    cpl_id: uuid.UUID,
    dados: ItemHabilitacaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> ItemHabilitacaoJuridica:
    """RF-027: item do checklist de habilitação jurídica da CPL perante
    um edital — etapa que precede a avaliação de maturidade."""

    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    _get_edital_or_404(db, dados.edital_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)
    item = ItemHabilitacaoJuridica(cpl_id=cpl_id, **dados.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/cpls/{cpl_id}/habilitacao", response_model=list[ItemHabilitacaoRead])
def listar_itens_habilitacao(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[ItemHabilitacaoJuridica]:
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return (
        db.query(ItemHabilitacaoJuridica)
        .filter(ItemHabilitacaoJuridica.cpl_id == cpl_id)
        .order_by(ItemHabilitacaoJuridica.created_at)
        .all()
    )


@router.post("/habilitacao/{item_id}/analisar", response_model=ItemHabilitacaoRead)
def analisar_item_habilitacao(
    item_id: uuid.UUID,
    dados: ItemHabilitacaoAnalise,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> ItemHabilitacaoJuridica:
    """Análise (aprovar/rejeitar) é sempre de quem gere os editais —
    mesma autoridade de `RecursoAvaliacao` — é o órgão externo do
    edital validando a regularidade jurídica, não uma decisão interna
    da CPL."""

    item = db.get(ItemHabilitacaoJuridica, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item de habilitação não encontrado.")
    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    item.status = dados.status
    item.parecer = dados.parecer
    item.analisado_por_id = usuario_atual.id
    item.data_analise = date.today()
    db.commit()
    db.refresh(item)
    return item


# --- Alertas de vencimento (RF-028) ------------------------------------------


@router.get("/cpls/vencimento-proximo", response_model=list[CPLRead])
def cpls_vencimento_proximo(
    dias: int = 90,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[CPL]:
    """RF-028: CPLs cujo reconhecimento vence dentro da janela informada
    (ou já venceu) — escopado às CPLs visíveis pelo usuário."""

    cpls = cpls_com_vencimento_proximo(db, dias)
    ids_visiveis = cpl_ids_visiveis(db, usuario_atual)
    if ids_visiveis is None:
        return cpls
    return [cpl for cpl in cpls if cpl.id in ids_visiveis]


# --- Relatório de recadastramento (RF-048) -----------------------------------


@router.post(
    "/cpls/{cpl_id}/relatorio-recadastramento",
    response_model=DocumentoRead,
    status_code=status.HTTP_201_CREATED,
)
def gerar_relatorio_recadastramento(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Documento:
    """RF-048: dossiê de recadastramento em PDF, já cadastrado no
    repositório de documentos (RF-042) — mesmo padrão do relatório
    executivo (RF-045/046/047)."""

    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)

    pdf_bytes = gerar_pdf_relatorio_recadastramento(cpl, resumo_recadastramento(db, cpl_id))
    nome_arquivo = f"Relatorio de Recadastramento - {cpl.nome}.pdf"
    caminho = salvar_arquivo(cpl_id, nome_arquivo, pdf_bytes)

    documento = Documento(
        cpl_id=cpl_id,
        titulo=f"Relatório de Recadastramento — {cpl.nome}",
        categoria=CategoriaDocumento.RELATORIO,
        confidencialidade=ConfidencialidadeDocumento.INTERNO,
        arquivo_path=caminho,
        nome_arquivo_original=nome_arquivo,
        tipo_mime="application/pdf",
        tamanho_bytes=len(pdf_bytes),
        criado_por_id=usuario_atual.id,
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento
