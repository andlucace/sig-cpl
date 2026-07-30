import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import (
    PAPEIS_GESTAO,
    PAPEIS_GOVERNANCA_LEITURA,
    PAPEIS_IMPEDIMENTO_LEITURA,
    cpl_ids_visiveis,
    verificar_papel,
)
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.documento import Documento
from app.models.enums import AcaoAuditoria, CategoriaDocumento, ConfidencialidadeDocumento
from app.models.governanca import Reuniao
from app.models.usuario import Usuario
from app.services.armazenamento import caminho_absoluto, salvar_arquivo
from app.services.auditoria import registrar_evento
from app.services.geracao_documentos import gerar_pdf_ata
from app.web.templates import templates

router = APIRouter(prefix="/painel/documentos", tags=["Área restrita — Documentos"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _verificar_leitura(db: Session, usuario: Usuario, documento: Documento) -> None:
    if documento.confidencialidade == ConfidencialidadeDocumento.CONFIDENCIAL:
        verificar_papel(db, usuario, PAPEIS_IMPEDIMENTO_LEITURA, cpl_id=documento.cpl_id)
    else:
        verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=documento.cpl_id)


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
        request, "restrito/documentos/cpls.html", {"cpls": cpls, "usuario": usuario, "pagina_ativa": "documentos"}
    )


@router.get("/cpls/{cpl_id}")
def listar_documentos(
    request: Request,
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        return RedirectResponse("/painel/documentos", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)

    documentos = db.query(Documento).filter(Documento.cpl_id == cpl_id).order_by(Documento.created_at.desc()).all()
    tem_acesso_confidencial = True
    try:
        verificar_papel(db, usuario, PAPEIS_IMPEDIMENTO_LEITURA, cpl_id=cpl_id)
    except HTTPException:
        tem_acesso_confidencial = False
    if not tem_acesso_confidencial:
        documentos = [d for d in documentos if d.confidencialidade != ConfidencialidadeDocumento.CONFIDENCIAL]

    return templates.TemplateResponse(
        request,
        "restrito/documentos/cpl_documentos.html",
        {
            "cpl": cpl,
            "documentos": documentos,
            "categorias": list(CategoriaDocumento),
            "confidencialidades": list(ConfidencialidadeDocumento),
            "usuario": usuario,
            "pagina_ativa": "documentos",
        },
    )


@router.post("/cpls/{cpl_id}")
async def enviar_documento(
    cpl_id: uuid.UUID,
    arquivo: UploadFile,
    titulo: str = Form(...),
    categoria: CategoriaDocumento = Form(...),
    confidencialidade: ConfidencialidadeDocumento = Form(ConfidencialidadeDocumento.INTERNO),
    descricao: str | None = Form(None),
    data_validade: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)

    conteudo = await arquivo.read()
    caminho = salvar_arquivo(cpl_id, arquivo.filename or "documento", conteudo)
    documento = Documento(
        cpl_id=cpl_id,
        titulo=titulo,
        categoria=categoria,
        confidencialidade=confidencialidade,
        descricao=descricao or None,
        arquivo_path=caminho,
        nome_arquivo_original=arquivo.filename or "documento",
        tipo_mime=arquivo.content_type,
        tamanho_bytes=len(conteudo),
        data_validade=date.fromisoformat(data_validade) if data_validade else None,
        criado_por_id=usuario.id,
    )
    db.add(documento)
    db.commit()
    return RedirectResponse(f"/painel/documentos/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{documento_id}/aprovar")
def aprovar_documento(
    documento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    documento = db.get(Documento, documento_id)
    if documento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=documento.cpl_id)
    documento.aprovado = True
    documento.data_aprovacao = date.today()
    db.commit()
    return RedirectResponse(f"/painel/documentos/cpls/{documento.cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{documento_id}/assinar")
def assinar_documento(
    documento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    documento = db.get(Documento, documento_id)
    if documento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=documento.cpl_id)
    documento.assinado = True
    db.commit()
    return RedirectResponse(f"/painel/documentos/cpls/{documento.cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{documento_id}/arquivo")
def baixar_documento(
    documento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    documento = db.get(Documento, documento_id)
    if documento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento não encontrado.")
    _verificar_leitura(db, usuario, documento)
    caminho = caminho_absoluto(documento.arquivo_path)
    if not caminho.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo não encontrado em disco.")
    registrar_evento(
        db,
        usuario_id=usuario.id,
        acao=AcaoAuditoria.DOWNLOAD,
        entidade_tipo="Documento",
        entidade_id=documento.id,
        cpl_id=documento.cpl_id,
        descricao=f"Download de '{documento.titulo}'.",
    )
    db.commit()
    return FileResponse(caminho, filename=documento.nome_arquivo_original, media_type=documento.tipo_mime)


@router.post("/reunioes/{reuniao_id}/ata-pdf")
def gerar_ata_pdf(
    reuniao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    reuniao = db.get(Reuniao, reuniao_id)
    if reuniao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reunião não encontrada.")
    cpl_id = reuniao.orgao.cpl_id
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)

    pdf_bytes = gerar_pdf_ata(reuniao)
    nome_arquivo = f"Ata - {reuniao.titulo}.pdf"
    caminho = salvar_arquivo(cpl_id, nome_arquivo, pdf_bytes)
    documento = Documento(
        cpl_id=cpl_id,
        titulo=f"Ata — {reuniao.titulo}",
        categoria=CategoriaDocumento.ATA,
        confidencialidade=ConfidencialidadeDocumento.INTERNO,
        arquivo_path=caminho,
        nome_arquivo_original=nome_arquivo,
        tipo_mime="application/pdf",
        tamanho_bytes=len(pdf_bytes),
        criado_por_id=usuario.id,
        reuniao_id=reuniao_id,
    )
    db.add(documento)
    db.commit()
    return RedirectResponse(f"/painel/governanca/reunioes/{reuniao_id}", status_code=status.HTTP_303_SEE_OTHER)
