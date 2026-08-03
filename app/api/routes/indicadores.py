import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_GESTAO, PAPEIS_GOVERNANCA_LEITURA, verificar_papel
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.documento import Documento
from app.models.enums import CategoriaDocumento, ConfidencialidadeDocumento
from app.models.planejamento import IndicadorEstrategico, IndicadorValorHistorico
from app.models.usuario import Usuario
from app.schemas.documento import DocumentoRead
from app.schemas.indicadores import ResumoCadastralRead
from app.schemas.planejamento import IndicadorEstrategicoRead, IndicadorValorHistoricoRead
from app.services.armazenamento import salvar_arquivo
from app.services.geracao_documentos import (
    gerar_pdf_relatorio_anual,
    gerar_pdf_relatorio_executivo,
    gerar_pdf_relatorio_impacto,
)
from app.services.indicadores import (
    catalogo_indicadores,
    resumo_anual,
    resumo_cadastral,
    resumo_governanca,
    resumo_planejamento,
)

router = APIRouter(prefix="/indicadores", tags=["Indicadores e relatórios"])


def _get_cpl_or_404(db: Session, cpl_id: uuid.UUID) -> CPL:
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    return cpl


@router.get("/cpls/{cpl_id}/catalogo", response_model=list[IndicadorEstrategicoRead])
def obter_catalogo(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[IndicadorEstrategico]:
    """RF-044: catálogo de indicadores estratégicos de uma CPL, através de
    todos os ciclos de planejamento."""

    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return catalogo_indicadores(db, cpl_id)


@router.get("/cpls/{cpl_id}/resumo-cadastral", response_model=ResumoCadastralRead)
def obter_resumo_cadastral(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> dict:
    """RF-046/047: agregado de empresas, empregos, faturamento, inovação,
    exportação e ODS a partir do diagnóstico cadastral já coletado."""

    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return resumo_cadastral(db, cpl_id)


@router.get("/{indicador_id}/historico", response_model=list[IndicadorValorHistoricoRead])
def obter_historico(
    indicador_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[IndicadorValorHistorico]:
    indicador = db.get(IndicadorEstrategico, indicador_id)
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador não encontrado.")
    verificar_papel(
        db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=indicador.objetivo.planejamento.cpl_id
    )
    return (
        db.query(IndicadorValorHistorico)
        .filter(IndicadorValorHistorico.indicador_id == indicador_id)
        .order_by(IndicadorValorHistorico.data_referencia.desc())
        .all()
    )


@router.post(
    "/cpls/{cpl_id}/relatorio-executivo", response_model=DocumentoRead, status_code=status.HTTP_201_CREATED
)
def gerar_relatorio_executivo(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Documento:
    """RF-048: gera o relatório executivo em PDF e já cadastra no
    repositório de documentos (RF-042), igual ao padrão da ata de reunião."""

    cpl = _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)

    pdf_bytes = gerar_pdf_relatorio_executivo(
        cpl,
        resumo_governanca(db, cpl_id),
        resumo_planejamento(db, cpl_id),
        resumo_cadastral(db, cpl_id),
        catalogo_indicadores(db, cpl_id),
    )
    nome_arquivo = f"Relatorio Executivo - {cpl.nome}.pdf"
    caminho = salvar_arquivo(cpl_id, nome_arquivo, pdf_bytes)

    documento = Documento(
        cpl_id=cpl_id,
        titulo=f"Relatório Executivo — {cpl.nome}",
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


@router.post(
    "/cpls/{cpl_id}/relatorio-anual", response_model=DocumentoRead, status_code=status.HTTP_201_CREATED
)
def gerar_relatorio_anual(
    cpl_id: uuid.UUID,
    ano: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Documento:
    """RF-048: relatório anual em PDF — recortado a um ano-calendário
    (diferente do executivo, que é o acumulado desde sempre). Salvo no
    repositório de documentos igual ao padrão dos outros relatórios."""

    cpl = _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)

    pdf_bytes = gerar_pdf_relatorio_anual(cpl, resumo_anual(db, cpl_id, ano))
    nome_arquivo = f"Relatorio Anual {ano} - {cpl.nome}.pdf"
    caminho = salvar_arquivo(cpl_id, nome_arquivo, pdf_bytes)

    documento = Documento(
        cpl_id=cpl_id,
        titulo=f"Relatório Anual {ano} — {cpl.nome}",
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


@router.post(
    "/cpls/{cpl_id}/relatorio-impacto", response_model=DocumentoRead, status_code=status.HTTP_201_CREATED
)
def gerar_relatorio_impacto(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Documento:
    """RF-048/RF-047: relatório de impacto em PDF — recorte do resumo
    cadastral (sustentabilidade, inovação, ODS, exportação,
    certificações, empregos), sem consolidar governança/planejamento
    como o executivo. Salvo no repositório de documentos igual ao
    padrão dos outros relatórios."""

    cpl = _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)

    pdf_bytes = gerar_pdf_relatorio_impacto(cpl, resumo_cadastral(db, cpl_id))
    nome_arquivo = f"Relatorio de Impacto - {cpl.nome}.pdf"
    caminho = salvar_arquivo(cpl_id, nome_arquivo, pdf_bytes)

    documento = Documento(
        cpl_id=cpl_id,
        titulo=f"Relatório de Impacto — {cpl.nome}",
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
