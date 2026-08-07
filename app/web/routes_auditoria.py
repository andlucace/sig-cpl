import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import (
    PAPEIS_EDITAL_GESTAO,
    PAPEIS_IMPEDIMENTO_LEITURA,
    cpl_ids_visiveis,
    verificar_papel,
)
from app.db.session import get_db
from app.models.auditoria import RegistroAuditoria
from app.models.cpl import CPL
from app.models.enums import AcaoAuditoria
from app.models.usuario import Usuario
from app.services.auditoria import LIMITE_PADRAO, consultar_registros
from app.web.templates import templates

router = APIRouter(prefix="/painel/auditoria", tags=["Área restrita — Auditoria"])

TAMANHO_PAGINA = LIMITE_PADRAO


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
    eh_admin = ids is None
    if eh_admin:
        cpls = db.query(CPL).order_by(CPL.nome).all()
    elif ids:
        cpls = db.query(CPL).filter(CPL.id.in_(ids)).order_by(CPL.nome).all()
    else:
        cpls = []
    return templates.TemplateResponse(
        request,
        "restrito/auditoria/cpls.html",
        {"cpls": cpls, "eh_admin": eh_admin, "usuario": usuario, "pagina_ativa": "auditoria"},
    )


@router.get("/cpls/{cpl_id}")
def listar_registros(
    request: Request,
    cpl_id: uuid.UUID,
    acao: str | None = None,
    entidade_tipo: str | None = None,
    pagina: int = 1,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        return RedirectResponse("/painel/auditoria", status_code=status.HTTP_303_SEE_OTHER)
    try:
        verificar_papel(db, usuario, PAPEIS_IMPEDIMENTO_LEITURA, cpl_id=cpl_id)
    except HTTPException:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Trilha de auditoria restrita à gestão e à auditoria/controle."
        ) from None

    # RF-056: os <select> do formulário de filtro sempre enviam os dois
    # campos, mesmo quando o usuário só mexeu em um deles — a opção
    # "Todas"/"Todos" tem value="", que chega aqui como string vazia, não
    # ausente. Tratar como "sem filtro" evita tanto um 422 (acao="" não é
    # um AcaoAuditoria válido) quanto um filtro que não bate com nada.
    acao_filtro = AcaoAuditoria(acao) if acao else None
    pagina = max(pagina, 1)

    registros, total = consultar_registros(
        db,
        cpl_id=cpl_id,
        acao=acao_filtro,
        entidade_tipo=entidade_tipo,
        offset=(pagina - 1) * TAMANHO_PAGINA,
        limite=TAMANHO_PAGINA,
    )

    tipos_disponiveis = sorted(
        {
            linha[0]
            for linha in db.query(RegistroAuditoria.entidade_tipo)
            .filter(RegistroAuditoria.cpl_id == cpl_id)
            .distinct()
            .all()
        }
    )

    return templates.TemplateResponse(
        request,
        "restrito/auditoria/cpl_auditoria.html",
        {
            "cpl": cpl,
            "registros": registros,
            "acoes": list(AcaoAuditoria),
            "tipos_disponiveis": tipos_disponiveis,
            "filtro_acao": acao_filtro,
            "filtro_entidade_tipo": entidade_tipo,
            "pagina": pagina,
            "total_paginas": max((total + TAMANHO_PAGINA - 1) // TAMANHO_PAGINA, 1),
            "total": total,
            "url_base": f"/painel/auditoria/cpls/{cpl_id}",
            "usuario": usuario,
            "pagina_ativa": "auditoria",
        },
    )


@router.get("/global")
def listar_registros_globais(
    request: Request,
    acao: str | None = None,
    entidade_tipo: str | None = None,
    pagina: int = 1,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    try:
        verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO)
    except HTTPException:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Visão global da auditoria restrita ao administrador da plataforma."
        ) from None

    acao_filtro = AcaoAuditoria(acao) if acao else None
    pagina = max(pagina, 1)

    registros, total = consultar_registros(
        db,
        somente_global=True,
        acao=acao_filtro,
        entidade_tipo=entidade_tipo,
        offset=(pagina - 1) * TAMANHO_PAGINA,
        limite=TAMANHO_PAGINA,
    )

    tipos_disponiveis = sorted(
        {
            linha[0]
            for linha in db.query(RegistroAuditoria.entidade_tipo)
            .filter(RegistroAuditoria.cpl_id.is_(None))
            .distinct()
            .all()
        }
    )

    return templates.TemplateResponse(
        request,
        "restrito/auditoria/global.html",
        {
            "registros": registros,
            "acoes": list(AcaoAuditoria),
            "tipos_disponiveis": tipos_disponiveis,
            "filtro_acao": acao_filtro,
            "filtro_entidade_tipo": entidade_tipo,
            "pagina": pagina,
            "total_paginas": max((total + TAMANHO_PAGINA - 1) // TAMANHO_PAGINA, 1),
            "total": total,
            "url_base": "/painel/auditoria/global",
            "usuario": usuario,
            "pagina_ativa": "auditoria",
        },
    )
