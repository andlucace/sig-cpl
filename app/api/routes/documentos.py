import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_GESTAO, PAPEIS_GOVERNANCA_LEITURA, PAPEIS_IMPEDIMENTO_LEITURA, verificar_papel
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.documento import Documento
from app.models.enums import AcaoAuditoria, CategoriaDocumento, ConfidencialidadeDocumento
from app.models.governanca import Reuniao
from app.models.usuario import Usuario
from app.schemas.documento import DocumentoAprovacaoUpdate, DocumentoRead
from app.services.armazenamento import caminho_absoluto, salvar_arquivo
from app.services.auditoria import registrar_evento
from app.services.geracao_documentos import gerar_pdf_ata

router = APIRouter(prefix="/documentos", tags=["Documentos"])


def _get_cpl_or_404(db: Session, cpl_id: uuid.UUID) -> CPL:
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    return cpl


def _get_documento_or_404(db: Session, documento_id: uuid.UUID) -> Documento:
    documento = db.get(Documento, documento_id)
    if documento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento não encontrado.")
    return documento


def _verificar_leitura(db: Session, usuario: Usuario, documento: Documento) -> None:
    """RN-014: documento confidencial só para gestão/auditoria; público e
    interno seguem a mesma visibilidade do resto da governança."""

    if documento.confidencialidade == ConfidencialidadeDocumento.CONFIDENCIAL:
        verificar_papel(db, usuario, PAPEIS_IMPEDIMENTO_LEITURA, cpl_id=documento.cpl_id)
    else:
        verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=documento.cpl_id)


@router.post("/cpls/{cpl_id}", response_model=DocumentoRead, status_code=status.HTTP_201_CREATED)
async def enviar_documento(
    cpl_id: uuid.UUID,
    arquivo: UploadFile,
    titulo: str = Form(...),
    categoria: CategoriaDocumento = Form(...),
    descricao: str | None = Form(None),
    confidencialidade: ConfidencialidadeDocumento = Form(ConfidencialidadeDocumento.INTERNO),
    data_validade: str | None = Form(None),
    reuniao_id: uuid.UUID | None = Form(None),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Documento:
    """RF-042: envia um novo documento para o repositório da CPL.

    `reuniao_id` (RF-017, "anexos de arquivo" da reunião) é opcional —
    mesma tabela `Documento` já usada pela ata gerada automaticamente
    (RF-043), sem entidade nova; a reunião precisa pertencer à mesma
    CPL do upload."""

    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)
    if reuniao_id is not None:
        reuniao = db.get(Reuniao, reuniao_id)
        if reuniao is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Reunião não encontrada.")
        if reuniao.orgao.cpl_id != cpl_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reunião não pertence a esta CPL.")

    conteudo = await arquivo.read()
    caminho = salvar_arquivo(cpl_id, arquivo.filename or "documento", conteudo)

    documento = Documento(
        cpl_id=cpl_id,
        titulo=titulo,
        categoria=categoria,
        descricao=descricao or None,
        confidencialidade=confidencialidade,
        arquivo_path=caminho,
        nome_arquivo_original=arquivo.filename or "documento",
        tipo_mime=arquivo.content_type,
        tamanho_bytes=len(conteudo),
        data_validade=date.fromisoformat(data_validade) if data_validade else None,
        criado_por_id=usuario_atual.id,
        reuniao_id=reuniao_id,
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento


@router.get("/reunioes/{reuniao_id}", response_model=list[DocumentoRead])
def listar_anexos_reuniao(
    reuniao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Documento]:
    """RF-017: anexos de uma reunião — mesmo repositório de Documentos
    (RF-042), filtrado por `reuniao_id`."""

    reuniao = db.get(Reuniao, reuniao_id)
    if reuniao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reunião não encontrada.")
    cpl_id = reuniao.orgao.cpl_id
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    documentos = (
        db.query(Documento)
        .filter(Documento.reuniao_id == reuniao_id)
        .order_by(Documento.created_at.desc())
        .all()
    )
    tem_acesso_confidencial = True
    try:
        verificar_papel(db, usuario_atual, PAPEIS_IMPEDIMENTO_LEITURA, cpl_id=cpl_id)
    except HTTPException:
        tem_acesso_confidencial = False
    if not tem_acesso_confidencial:
        documentos = [
            d for d in documentos if d.confidencialidade != ConfidencialidadeDocumento.CONFIDENCIAL
        ]
    return documentos


@router.get("/cpls/{cpl_id}", response_model=list[DocumentoRead])
def listar_documentos(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Documento]:
    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    documentos = db.query(Documento).filter(Documento.cpl_id == cpl_id).all()
    tem_acesso_confidencial = True
    try:
        verificar_papel(db, usuario_atual, PAPEIS_IMPEDIMENTO_LEITURA, cpl_id=cpl_id)
    except HTTPException:
        tem_acesso_confidencial = False
    if not tem_acesso_confidencial:
        documentos = [
            d for d in documentos if d.confidencialidade != ConfidencialidadeDocumento.CONFIDENCIAL
        ]
    return documentos


@router.get("/{documento_id}", response_model=DocumentoRead)
def obter_documento(
    documento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Documento:
    documento = _get_documento_or_404(db, documento_id)
    _verificar_leitura(db, usuario_atual, documento)
    return documento


@router.get("/{documento_id}/arquivo")
def baixar_documento(
    documento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> FileResponse:
    documento = _get_documento_or_404(db, documento_id)
    _verificar_leitura(db, usuario_atual, documento)
    caminho = caminho_absoluto(documento.arquivo_path)
    if not caminho.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo não encontrado em disco.")
    registrar_evento(
        db,
        usuario_id=usuario_atual.id,
        acao=AcaoAuditoria.DOWNLOAD,
        entidade_tipo="Documento",
        entidade_id=documento.id,
        cpl_id=documento.cpl_id,
        descricao=f"Download de '{documento.titulo}'.",
    )
    db.commit()
    return FileResponse(
        caminho, filename=documento.nome_arquivo_original, media_type=documento.tipo_mime
    )


@router.patch("/{documento_id}", response_model=DocumentoRead)
def atualizar_aprovacao(
    documento_id: uuid.UUID,
    dados: DocumentoAprovacaoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Documento:
    """RF-042: marca aprovação/assinatura e ajusta retenção — RN-007-like:
    nenhuma mudança sem usuário/data (já cobertos por `updated_at")."""

    documento = _get_documento_or_404(db, documento_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=documento.cpl_id)
    dados_dict = dados.model_dump(exclude_unset=True)
    if dados_dict.get("aprovado"):
        documento.data_aprovacao = date.today()
    for campo, valor in dados_dict.items():
        setattr(documento, campo, valor)
    db.commit()
    db.refresh(documento)
    return documento


@router.post(
    "/{documento_id}/nova-versao", response_model=DocumentoRead, status_code=status.HTTP_201_CREATED
)
async def enviar_nova_versao(
    documento_id: uuid.UUID,
    arquivo: UploadFile,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Documento:
    anterior = _get_documento_or_404(db, documento_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=anterior.cpl_id)

    conteudo = await arquivo.read()
    caminho = salvar_arquivo(anterior.cpl_id, arquivo.filename or anterior.nome_arquivo_original, conteudo)

    nova_versao = Documento(
        cpl_id=anterior.cpl_id,
        titulo=anterior.titulo,
        categoria=anterior.categoria,
        descricao=anterior.descricao,
        confidencialidade=anterior.confidencialidade,
        arquivo_path=caminho,
        nome_arquivo_original=arquivo.filename or anterior.nome_arquivo_original,
        tipo_mime=arquivo.content_type,
        tamanho_bytes=len(conteudo),
        versao=anterior.versao + 1,
        documento_anterior_id=anterior.id,
        criado_por_id=usuario_atual.id,
    )
    db.add(nova_versao)
    db.commit()
    db.refresh(nova_versao)
    return nova_versao


# --- Geração de documentos (RF-043) -----------------------------------------


@router.post(
    "/reunioes/{reuniao_id}/ata-pdf", response_model=DocumentoRead, status_code=status.HTTP_201_CREATED
)
def gerar_ata_pdf(
    reuniao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Documento:
    """RF-043: gera a ata da reunião em PDF e já cadastra no repositório
    de documentos (RF-042), ligada à reunião de origem."""

    reuniao = db.get(Reuniao, reuniao_id)
    if reuniao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reunião não encontrada.")
    cpl_id = reuniao.orgao.cpl_id
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)

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
        criado_por_id=usuario_atual.id,
        reuniao_id=reuniao_id,
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento
