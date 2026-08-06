import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_EDITAL_GESTAO, cpl_ids_visiveis, verificar_papel
from app.db.session import get_db
from app.models.biblioteca import RecursoBiblioteca
from app.models.enums import TipoRecursoBiblioteca
from app.models.usuario import Usuario
from app.schemas.biblioteca import RecursoBibliotecaRead, RecursoBibliotecaUpdate
from app.services.armazenamento import caminho_absoluto, salvar_arquivo_biblioteca

router = APIRouter(prefix="/biblioteca", tags=["Biblioteca de conhecimento (RF-051)"])


def _get_recurso_or_404(db: Session, recurso_id: uuid.UUID) -> RecursoBiblioteca:
    recurso = db.get(RecursoBiblioteca, recurso_id)
    if recurso is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recurso não encontrado.")
    return recurso


@router.post("", response_model=RecursoBibliotecaRead, status_code=status.HTTP_201_CREATED)
async def criar_recurso(
    titulo: str = Form(...),
    tipo: TipoRecursoBiblioteca = Form(...),
    descricao: str | None = Form(None),
    url_externa: str | None = Form(None),
    publicado: bool = Form(True),
    arquivo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> RecursoBiblioteca:
    """RF-051: cria um recurso da biblioteca — arquivo, link externo ou só
    texto (`descricao`); ao menos um dos três precisa estar preenchido.
    Gerido pela mesma autoridade de `Edital` (`PAPEIS_EDITAL_GESTAO`) —
    conteúdo compartilhado entre todas as CPLs, não algo que cada uma
    mantém pra si."""

    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    if not descricao and not url_externa and arquivo is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Informe ao menos um conteúdo: arquivo, link externo ou descrição."
        )

    recurso = RecursoBiblioteca(
        titulo=titulo,
        tipo=tipo,
        descricao=descricao or None,
        url_externa=url_externa or None,
        publicado=publicado,
        criado_por_id=usuario_atual.id,
    )
    if arquivo is not None:
        conteudo = await arquivo.read()
        recurso.arquivo_path = salvar_arquivo_biblioteca(arquivo.filename or "recurso", conteudo)
        recurso.nome_arquivo_original = arquivo.filename or "recurso"
        recurso.tipo_mime = arquivo.content_type
        recurso.tamanho_bytes = len(conteudo)

    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


@router.get("", response_model=list[RecursoBibliotecaRead])
def listar_recursos(
    tipo: TipoRecursoBiblioteca | None = None,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[RecursoBiblioteca]:
    """Qualquer usuário autenticado navega a biblioteca (é conteúdo pra
    ajudar todas as CPLs, não dado sensível) — só rascunho não publicado
    fica restrito a quem administra."""

    query = db.query(RecursoBiblioteca)
    if cpl_ids_visiveis(db, usuario_atual) is not None:
        query = query.filter(RecursoBiblioteca.publicado.is_(True))
    if tipo is not None:
        query = query.filter(RecursoBiblioteca.tipo == tipo)
    return query.order_by(RecursoBiblioteca.created_at.desc()).all()


@router.get("/{recurso_id}", response_model=RecursoBibliotecaRead)
def obter_recurso(
    recurso_id: uuid.UUID, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> RecursoBiblioteca:
    recurso = _get_recurso_or_404(db, recurso_id)
    if not recurso.publicado:
        verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    return recurso


@router.get("/{recurso_id}/arquivo")
def baixar_arquivo(
    recurso_id: uuid.UUID, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> FileResponse:
    recurso = _get_recurso_or_404(db, recurso_id)
    if not recurso.publicado:
        verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    if not recurso.arquivo_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Este recurso não tem arquivo anexado.")
    caminho = caminho_absoluto(recurso.arquivo_path)
    if not caminho.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo não encontrado em disco.")
    return FileResponse(caminho, filename=recurso.nome_arquivo_original, media_type=recurso.tipo_mime)


@router.patch("/{recurso_id}", response_model=RecursoBibliotecaRead)
def atualizar_recurso(
    recurso_id: uuid.UUID,
    dados: RecursoBibliotecaUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> RecursoBiblioteca:
    recurso = _get_recurso_or_404(db, recurso_id)
    verificar_papel(db, usuario_atual, PAPEIS_EDITAL_GESTAO, cpl_id=None)

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso
