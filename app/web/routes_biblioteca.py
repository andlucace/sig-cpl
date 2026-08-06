import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import PAPEIS_EDITAL_GESTAO, cpl_ids_visiveis, verificar_papel
from app.db.session import get_db
from app.models.biblioteca import RecursoBiblioteca
from app.models.enums import TipoRecursoBiblioteca
from app.models.usuario import Usuario
from app.services.armazenamento import caminho_absoluto, salvar_arquivo_biblioteca
from app.web.templates import templates

router = APIRouter(prefix="/painel/biblioteca", tags=["Área restrita — Biblioteca"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _e_administrador(db: Session, usuario: Usuario) -> bool:
    return cpl_ids_visiveis(db, usuario) is None


@router.get("")
def listar(
    request: Request,
    tipo: str | None = None,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    e_admin = _e_administrador(db, usuario)
    query = db.query(RecursoBiblioteca)
    if not e_admin:
        query = query.filter(RecursoBiblioteca.publicado.is_(True))
    tipo_filtro = TipoRecursoBiblioteca(tipo) if tipo else None
    if tipo_filtro is not None:
        query = query.filter(RecursoBiblioteca.tipo == tipo_filtro)
    recursos = query.order_by(RecursoBiblioteca.created_at.desc()).all()

    return templates.TemplateResponse(
        request,
        "restrito/biblioteca/lista.html",
        {
            "recursos": recursos,
            "tipos": list(TipoRecursoBiblioteca),
            "filtro_tipo": tipo_filtro,
            "e_administrador": e_admin,
            "usuario": usuario,
            "pagina_ativa": "biblioteca",
        },
    )


@router.post("")
async def criar(
    request: Request,
    titulo: str = Form(...),
    tipo: TipoRecursoBiblioteca = Form(...),
    descricao: str | None = Form(None),
    url_externa: str | None = Form(None),
    publicado: str | None = Form(None),
    arquivo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    if not descricao and not url_externa and (arquivo is None or not arquivo.filename):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Informe ao menos um conteúdo: arquivo, link externo ou descrição."
        )

    recurso = RecursoBiblioteca(
        titulo=titulo,
        tipo=tipo,
        descricao=descricao or None,
        url_externa=url_externa or None,
        publicado=publicado == "on",
        criado_por_id=usuario.id,
    )
    if arquivo is not None and arquivo.filename:
        conteudo = await arquivo.read()
        recurso.arquivo_path = salvar_arquivo_biblioteca(arquivo.filename, conteudo)
        recurso.nome_arquivo_original = arquivo.filename
        recurso.tipo_mime = arquivo.content_type
        recurso.tamanho_bytes = len(conteudo)

    db.add(recurso)
    db.commit()
    return RedirectResponse("/painel/biblioteca", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{recurso_id}/publicar")
def alternar_publicacao(
    recurso_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    recurso = db.get(RecursoBiblioteca, recurso_id)
    if recurso is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recurso não encontrado.")
    recurso.publicado = not recurso.publicado
    db.commit()
    return RedirectResponse("/painel/biblioteca", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{recurso_id}/arquivo")
def baixar_arquivo(
    recurso_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    recurso = db.get(RecursoBiblioteca, recurso_id)
    if recurso is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recurso não encontrado.")
    if not recurso.publicado:
        verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    if not recurso.arquivo_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Este recurso não tem arquivo anexado.")
    caminho = caminho_absoluto(recurso.arquivo_path)
    if not caminho.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo não encontrado em disco.")
    return FileResponse(caminho, filename=recurso.nome_arquivo_original, media_type=recurso.tipo_mime)
