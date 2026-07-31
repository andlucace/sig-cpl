import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import PAPEIS_GOVERNANCA_LEITURA, cpl_ids_visiveis, verificar_papel
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.entidade import Entidade
from app.models.enums import Papel
from app.models.usuario import Usuario
from app.web.templates import templates

router = APIRouter(prefix="/painel/cpls", tags=["Área restrita — CPLs"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _e_administrador(db: Session, usuario: Usuario) -> bool:
    return cpl_ids_visiveis(db, usuario) is None


def _opt_uuid(valor: str | None) -> uuid.UUID | None:
    return uuid.UUID(valor) if valor else None


@router.get("")
def listar(request: Request, db: Session = Depends(get_db), usuario=Depends(get_current_user_optional)):
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
        request,
        "restrito/cpls/lista.html",
        {
            "cpls": cpls,
            "e_administrador": _e_administrador(db, usuario),
            "usuario": usuario,
            "pagina_ativa": "cpls",
        },
    )


@router.post("")
def criar(
    request: Request,
    nome: str = Form(...),
    sigla: str = Form(...),
    setor: str | None = Form(None),
    municipio: str | None = Form(None),
    uf: str | None = Form(None),
    entidade_gestora_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    verificar_papel(db, usuario, {Papel.ADMINISTRADOR_PLATAFORMA})
    if db.query(CPL).filter(CPL.sigla == sigla).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sigla já utilizada por outra CPL.")
    cpl = CPL(
        nome=nome,
        sigla=sigla,
        setor=setor or None,
        municipio=municipio or None,
        uf=uf or None,
        entidade_gestora_id=_opt_uuid(entidade_gestora_id),
    )
    db.add(cpl)
    db.commit()
    db.refresh(cpl)
    return RedirectResponse(f"/painel/cpls/{cpl.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{cpl_id}")
def detalhe(
    request: Request,
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        return RedirectResponse("/painel/cpls", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    entidades = db.query(Entidade).order_by(Entidade.razao_social).all()
    return templates.TemplateResponse(
        request,
        "restrito/cpls/detail.html",
        {
            "cpl": cpl,
            "entidades": entidades,
            "e_administrador": _e_administrador(db, usuario),
            "usuario": usuario,
            "pagina_ativa": "cpls",
        },
    )


@router.post("/{cpl_id}")
def atualizar(
    cpl_id: uuid.UUID,
    nome: str | None = Form(None),
    sigla: str | None = Form(None),
    setor: str | None = Form(None),
    municipio: str | None = Form(None),
    uf: str | None = Form(None),
    entidade_gestora_id: str | None = Form(None),
    ativo: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, {Papel.ADMINISTRADOR_PLATAFORMA})

    if sigla and sigla != cpl.sigla:
        if db.query(CPL).filter(CPL.sigla == sigla, CPL.id != cpl_id).first():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sigla já utilizada por outra CPL.")
        cpl.sigla = sigla
    if nome:
        cpl.nome = nome
    cpl.setor = setor or None
    cpl.municipio = municipio or None
    cpl.uf = uf or None
    cpl.entidade_gestora_id = _opt_uuid(entidade_gestora_id)
    cpl.ativo = ativo == "on"
    db.commit()
    return RedirectResponse(f"/painel/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)
