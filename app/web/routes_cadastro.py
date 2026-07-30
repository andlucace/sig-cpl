import secrets
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import PAPEIS_GESTAO, PAPEIS_GOVERNANCA_LEITURA, cpl_ids_visiveis, verificar_papel
from app.db.session import get_db
from app.models.cadastro_dinamico import CampanhaCadastral, CampanhaConvite, ImportacaoLote
from app.models.cpl import CPL
from app.models.entidade import Entidade, EntidadeCPL
from app.models.usuario import Usuario
from app.services.importacao_entidades import processar_planilha
from app.web.templates import templates

router = APIRouter(prefix="/painel/cadastro", tags=["Área restrita — Cadastro"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


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
        request, "restrito/cadastro/cpls.html", {"cpls": cpls, "usuario": usuario, "pagina_ativa": "cadastro"}
    )


@router.get("/cpls/{cpl_id}")
def detalhe_cpl(
    request: Request,
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        return RedirectResponse("/painel/cadastro", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)

    vinculos = db.query(EntidadeCPL).filter(EntidadeCPL.cpl_id == cpl_id, EntidadeCPL.ativo.is_(True)).all()
    ids_vinculadas = {v.entidade_id for v in vinculos}
    query_disponiveis = db.query(Entidade)
    if ids_vinculadas:
        query_disponiveis = query_disponiveis.filter(~Entidade.id.in_(ids_vinculadas))
    entidades_disponiveis = query_disponiveis.order_by(Entidade.razao_social).all()
    campanhas = db.query(CampanhaCadastral).filter(CampanhaCadastral.cpl_id == cpl_id).all()
    importacoes = (
        db.query(ImportacaoLote)
        .filter(ImportacaoLote.cpl_id == cpl_id)
        .order_by(ImportacaoLote.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/cadastro/cpl_cadastro.html",
        {
            "cpl": cpl,
            "vinculos": vinculos,
            "entidades_disponiveis": entidades_disponiveis,
            "campanhas": campanhas,
            "importacoes": importacoes,
            "usuario": usuario,
            "pagina_ativa": "cadastro",
        },
    )


@router.post("/cpls/{cpl_id}/vincular")
def vincular_entidade(
    cpl_id: uuid.UUID,
    entidade_id: uuid.UUID = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)
    if not db.query(EntidadeCPL).filter(
        EntidadeCPL.cpl_id == cpl_id, EntidadeCPL.entidade_id == entidade_id
    ).first():
        db.add(EntidadeCPL(cpl_id=cpl_id, entidade_id=entidade_id, data_vinculo=date.today()))
        db.commit()
    return RedirectResponse(f"/painel/cadastro/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/cpls/{cpl_id}/campanhas")
def criar_campanha(
    cpl_id: uuid.UUID,
    titulo: str = Form(...),
    descricao: str | None = Form(None),
    data_inicio: str | None = Form(None),
    data_fim: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)

    campanha = CampanhaCadastral(
        cpl_id=cpl_id,
        titulo=titulo,
        descricao=descricao or None,
        data_inicio=date.fromisoformat(data_inicio) if data_inicio else None,
        data_fim=date.fromisoformat(data_fim) if data_fim else None,
    )
    db.add(campanha)
    db.commit()
    return RedirectResponse(f"/painel/cadastro/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/cpls/{cpl_id}/importacoes")
async def importar_planilha(
    cpl_id: uuid.UUID,
    arquivo: UploadFile,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)
    if not arquivo.filename or not arquivo.filename.lower().endswith((".csv", ".xlsx", ".xlsm")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Envie um arquivo .csv, .xlsx ou .xlsm.")
    conteudo = await arquivo.read()
    lote = processar_planilha(db, cpl_id, usuario.id, arquivo.filename, conteudo)
    return RedirectResponse(f"/painel/cadastro/importacoes/{lote.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/importacoes/{lote_id}")
def detalhe_importacao(
    request: Request,
    lote_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    lote = db.get(ImportacaoLote, lote_id)
    if lote is None:
        return RedirectResponse("/painel/cadastro", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=lote.cpl_id)
    return templates.TemplateResponse(
        request,
        "restrito/cadastro/importacao_detail.html",
        {"lote": lote, "usuario": usuario, "pagina_ativa": "cadastro"},
    )


@router.get("/campanhas/{campanha_id}")
def detalhe_campanha(
    request: Request,
    campanha_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    campanha = db.get(CampanhaCadastral, campanha_id)
    if campanha is None:
        return RedirectResponse("/painel/cadastro", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=campanha.cpl_id)

    convites = db.query(CampanhaConvite).filter(CampanhaConvite.campanha_id == campanha_id).all()
    ids_convidadas = {c.entidade_id for c in convites}
    vinculos = db.query(EntidadeCPL).filter(
        EntidadeCPL.cpl_id == campanha.cpl_id, EntidadeCPL.ativo.is_(True)
    ).all()
    entidades_convidaveis = [v.entidade for v in vinculos if v.entidade_id not in ids_convidadas]

    return templates.TemplateResponse(
        request,
        "restrito/cadastro/campanha_detail.html",
        {
            "campanha": campanha,
            "convites": convites,
            "entidades_convidaveis": entidades_convidaveis,
            "usuario": usuario,
            "pagina_ativa": "cadastro",
        },
    )


@router.post("/campanhas/{campanha_id}/convites")
def convidar_entidade(
    request: Request,
    campanha_id: uuid.UUID,
    entidade_id: uuid.UUID = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    campanha = db.get(CampanhaCadastral, campanha_id)
    if campanha is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campanha não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=campanha.cpl_id)

    convite = CampanhaConvite(campanha_id=campanha_id, entidade_id=entidade_id, token=secrets.token_urlsafe(24))
    db.add(convite)
    db.commit()
    db.refresh(convite)
    return templates.TemplateResponse(
        request, "restrito/cadastro/fragments/convite_item.html", {"convite": convite}
    )
