import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import PAPEIS_GESTAO, PAPEIS_GOVERNANCA_LEITURA, PAPEIS_TAREFA_EXECUCAO, cpl_ids_visiveis, verificar_papel
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.documento import Documento
from app.models.enums import CategoriaDocumento, ConfidencialidadeDocumento
from app.models.planejamento import IndicadorEstrategico, IndicadorValorHistorico
from app.models.usuario import Usuario
from app.services.armazenamento import salvar_arquivo
from app.services.geracao_documentos import (
    gerar_pdf_relatorio_anual,
    gerar_pdf_relatorio_executivo,
    gerar_pdf_relatorio_impacto,
)
from app.services.indicadores import (
    catalogo_indicadores,
    registrar_valor_indicador,
    resumo_anual,
    resumo_cadastral,
    resumo_governanca,
    resumo_planejamento,
)
from app.services.maturidade import resumo_recadastramento
from app.services.projeto import resumo_projetos_cpl
from app.web.templates import templates

router = APIRouter(prefix="/painel/indicadores", tags=["Área restrita — Indicadores"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _pode_executar(usuario: Usuario, responsavel_id: uuid.UUID | None) -> bool:
    return usuario.pessoa_id is not None and usuario.pessoa_id == responsavel_id


@router.get("")
def selecionar_cpl(
    request: Request, db: Session = Depends(get_db), usuario=Depends(get_current_user_optional)
):
    if redir := _exigir_login(usuario):
        return redir
    ids = cpl_ids_visiveis(db, usuario)
    if ids is None:
        cpls = db.query(CPL).order_by(CPL.nome).all()
    elif ids:
        cpls = db.query(CPL).filter(CPL.id.in_(ids)).order_by(CPL.nome).all()
    else:
        cpls = []
    return templates.TemplateResponse(
        request, "restrito/indicadores/cpls.html", {"cpls": cpls, "usuario": usuario, "pagina_ativa": "indicadores"}
    )


@router.get("/cpls/{cpl_id}")
def dashboard(
    request: Request,
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        return RedirectResponse("/painel/indicadores", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)

    return templates.TemplateResponse(
        request,
        "restrito/indicadores/cpl_dashboard.html",
        {
            "cpl": cpl,
            "indicadores": catalogo_indicadores(db, cpl_id),
            "cadastral": resumo_cadastral(db, cpl_id),
            "governanca": resumo_governanca(db, cpl_id),
            "planejamento": resumo_planejamento(db, cpl_id),
            "projetos_resumo": resumo_projetos_cpl(db, cpl_id),
            "maturidade": resumo_recadastramento(db, cpl_id),
            "ano_atual": date.today().year,
            "usuario": usuario,
            "pagina_ativa": "indicadores",
        },
    )


@router.post("/cpls/{cpl_id}/relatorio-executivo")
def gerar_relatorio_executivo(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)

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
        criado_por_id=usuario.id,
    )
    db.add(documento)
    db.commit()
    return RedirectResponse(f"/painel/documentos/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/cpls/{cpl_id}/relatorio-anual")
def gerar_relatorio_anual(
    cpl_id: uuid.UUID,
    ano: int = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)

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
        criado_por_id=usuario.id,
    )
    db.add(documento)
    db.commit()
    return RedirectResponse(f"/painel/documentos/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/cpls/{cpl_id}/relatorio-impacto")
def gerar_relatorio_impacto(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)

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
        criado_por_id=usuario.id,
    )
    db.add(documento)
    db.commit()
    return RedirectResponse(f"/painel/documentos/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{indicador_id}/historico")
def historico(
    request: Request,
    indicador_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    indicador = db.get(IndicadorEstrategico, indicador_id)
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador não encontrado.")
    cpl_id = indicador.objetivo.planejamento.cpl_id
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    pode_registrar = True
    if not _pode_executar(usuario, indicador.responsavel_id):
        try:
            verificar_papel(db, usuario, PAPEIS_TAREFA_EXECUCAO, cpl_id=cpl_id)
        except HTTPException:
            pode_registrar = False

    valores = (
        db.query(IndicadorValorHistorico)
        .filter(IndicadorValorHistorico.indicador_id == indicador_id)
        .order_by(IndicadorValorHistorico.data_referencia.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/indicadores/indicador_historico.html",
        {
            "indicador": indicador,
            "valores": valores,
            "pode_registrar": pode_registrar,
            "cpl_id": cpl_id,
            "usuario": usuario,
            "pagina_ativa": "indicadores",
        },
    )


@router.post("/{indicador_id}/historico")
def registrar_valor(
    request: Request,
    indicador_id: uuid.UUID,
    valor: str = Form(...),
    data_referencia: str | None = Form(None),
    observacao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    indicador = db.get(IndicadorEstrategico, indicador_id)
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador não encontrado.")
    cpl_id = indicador.objetivo.planejamento.cpl_id
    if not _pode_executar(usuario, indicador.responsavel_id):
        verificar_papel(db, usuario, PAPEIS_TAREFA_EXECUCAO, cpl_id=cpl_id)

    registrar_valor_indicador(
        db,
        indicador,
        valor,
        usuario.id,
        data_referencia=date.fromisoformat(data_referencia) if data_referencia else None,
        observacao=observacao or None,
    )
    return RedirectResponse(f"/painel/indicadores/{indicador_id}/historico", status_code=status.HTTP_303_SEE_OTHER)
