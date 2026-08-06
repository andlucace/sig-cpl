import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import (
    PAPEIS_GESTAO,
    PAPEIS_GOVERNANCA_LEITURA,
    Papel,
    cpl_ids_visiveis,
    papeis_do_usuario,
    verificar_papel,
)
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.enums import StatusEvento, TipoEvento
from app.models.evento import Evento, InscricaoEvento
from app.models.pessoa import Pessoa
from app.models.usuario import Usuario
from app.web.templates import templates

router = APIRouter(prefix="/painel/eventos", tags=["Área restrita — Eventos"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _cpls_gestao(db: Session, usuario: Usuario) -> list[CPL] | None:
    """None = administrador da plataforma (gere evento de qualquer CPL, e
    também os abertos a todas); lista = CPLs onde o usuário tem papel de
    gestão de verdade (não só leitura, ver `PAPEIS_GESTAO`)."""

    vinculos = papeis_do_usuario(db, usuario)
    if any(v.papel == Papel.ADMINISTRADOR_PLATAFORMA for v in vinculos):
        return None
    ids = {v.cpl_id for v in vinculos if v.papel in PAPEIS_GESTAO and v.cpl_id is not None}
    if not ids:
        return []
    return db.query(CPL).filter(CPL.id.in_(ids)).order_by(CPL.nome).all()


def _verificar_gestao_evento(db: Session, usuario: Usuario, cpl_id: uuid.UUID | None) -> None:
    if cpl_id is None:
        verificar_papel(db, usuario, {Papel.ADMINISTRADOR_PLATAFORMA}, cpl_id=None)
    else:
        verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)


@router.get("")
def listar(
    request: Request, db: Session = Depends(get_db), usuario=Depends(get_current_user_optional)
):
    if redir := _exigir_login(usuario):
        return redir
    ids = cpl_ids_visiveis(db, usuario)
    eventos = db.query(Evento).order_by(Evento.data_inicio.desc()).all()
    if ids is not None:
        eventos = [e for e in eventos if e.cpl_id is None or e.cpl_id in ids]

    cpls_gestao = _cpls_gestao(db, usuario)
    opcoes_cpl = db.query(CPL).order_by(CPL.nome).all() if cpls_gestao is None else cpls_gestao
    return templates.TemplateResponse(
        request,
        "restrito/eventos/lista.html",
        {
            "eventos": eventos,
            "cpls_gestao": cpls_gestao,
            "opcoes_cpl": opcoes_cpl,
            "e_administrador": cpls_gestao is None,
            "tipos": list(TipoEvento),
            "usuario": usuario,
            "pagina_ativa": "eventos",
        },
    )


@router.post("")
def criar(
    request: Request,
    titulo: str = Form(...),
    tipo: TipoEvento = Form(...),
    descricao: str | None = Form(None),
    data_inicio: str = Form(...),
    data_fim: str | None = Form(None),
    local: str | None = Form(None),
    vagas: int | None = Form(None),
    cpl_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl_uuid = uuid.UUID(cpl_id) if cpl_id else None
    _verificar_gestao_evento(db, usuario, cpl_uuid)

    evento = Evento(
        cpl_id=cpl_uuid,
        titulo=titulo,
        tipo=tipo,
        descricao=descricao or None,
        data_inicio=datetime.fromisoformat(data_inicio),
        data_fim=datetime.fromisoformat(data_fim) if data_fim else None,
        local=local or None,
        vagas=vagas,
        criado_por_id=usuario.id,
    )
    db.add(evento)
    db.commit()
    return RedirectResponse("/painel/eventos", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{evento_id}")
def detalhe(
    request: Request,
    evento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    evento = db.get(Evento, evento_id)
    if evento is None:
        return RedirectResponse("/painel/eventos", status_code=status.HTTP_303_SEE_OTHER)
    if evento.cpl_id is not None:
        verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=evento.cpl_id)

    cpls_gestao = _cpls_gestao(db, usuario)
    if cpls_gestao is None:
        cpls_inscricao = [evento.cpl] if evento.cpl_id else db.query(CPL).order_by(CPL.nome).all()
        pode_inscrever = True
    elif evento.cpl_id is not None:
        cpls_inscricao = [c for c in cpls_gestao if c.id == evento.cpl_id]
        pode_inscrever = bool(cpls_inscricao)
    else:
        cpls_inscricao = cpls_gestao
        pode_inscrever = bool(cpls_gestao)

    inscricoes = (
        db.query(InscricaoEvento)
        .filter(InscricaoEvento.evento_id == evento_id)
        .order_by(InscricaoEvento.created_at)
        .all()
    )
    if cpls_gestao is not None and evento.cpl_id is None:
        ids_gestao = {c.id for c in cpls_gestao}
        inscricoes = [i for i in inscricoes if i.cpl_id in ids_gestao]

    pessoas = db.query(Pessoa).order_by(Pessoa.nome).all()
    return templates.TemplateResponse(
        request,
        "restrito/eventos/detalhe.html",
        {
            "evento": evento,
            "inscricoes": inscricoes,
            "pessoas": pessoas,
            "cpls_inscricao": cpls_inscricao,
            "pode_inscrever": pode_inscrever,
            "pode_gerir_evento": cpls_gestao is None
            or (evento.cpl_id is not None and evento.cpl_id in {c.id for c in cpls_gestao}),
            "status_opcoes": list(StatusEvento),
            "usuario": usuario,
            "pagina_ativa": "eventos",
        },
    )


@router.post("/{evento_id}/status")
def atualizar_status(
    evento_id: uuid.UUID,
    status_novo: StatusEvento = Form(..., alias="status"),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento não encontrado.")
    _verificar_gestao_evento(db, usuario, evento.cpl_id)
    evento.status = status_novo
    db.commit()
    return RedirectResponse(f"/painel/eventos/{evento_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{evento_id}/inscricoes")
def inscrever(
    evento_id: uuid.UUID,
    pessoa_id: uuid.UUID = Form(...),
    cpl_id: uuid.UUID = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento não encontrado.")
    if evento.cpl_id is not None and cpl_id != evento.cpl_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este evento é restrito à CPL que o criou.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)

    pessoa = db.get(Pessoa, pessoa_id)
    if pessoa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pessoa não encontrada.")
    ja_inscrita = (
        db.query(InscricaoEvento)
        .filter(InscricaoEvento.evento_id == evento_id, InscricaoEvento.pessoa_id == pessoa_id)
        .first()
    )
    if ja_inscrita is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta pessoa já está inscrita neste evento.")
    if evento.vagas is not None:
        total = db.query(InscricaoEvento).filter(InscricaoEvento.evento_id == evento_id).count()
        if total >= evento.vagas:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Não há mais vagas disponíveis neste evento.")

    db.add(InscricaoEvento(evento_id=evento_id, pessoa_id=pessoa_id, cpl_id=cpl_id))
    db.commit()
    return RedirectResponse(f"/painel/eventos/{evento_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/inscricoes/{inscricao_id}")
def atualizar_inscricao(
    inscricao_id: uuid.UUID,
    presente: str | None = Form(None),
    nota_avaliacao: int | None = Form(None),
    comentario_avaliacao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    inscricao = db.get(InscricaoEvento, inscricao_id)
    if inscricao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inscrição não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=inscricao.cpl_id)

    if presente is not None:
        inscricao.presente = presente == "true"
    if nota_avaliacao is not None:
        inscricao.nota_avaliacao = nota_avaliacao
    if comentario_avaliacao is not None:
        inscricao.comentario_avaliacao = comentario_avaliacao or None
    db.commit()
    return RedirectResponse(
        f"/painel/eventos/{inscricao.evento_id}", status_code=status.HTTP_303_SEE_OTHER
    )
