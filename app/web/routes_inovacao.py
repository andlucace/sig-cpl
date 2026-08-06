import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import PAPEIS_PROJETO_GESTAO, PAPEIS_PROJETO_LEITURA, papeis_do_usuario, verificar_papel
from app.db.session import get_db
from app.models.entidade import Entidade, OfertaEntidade
from app.models.enums import StatusMatchInovacao, TipoEntidade
from app.models.inovacao import MatchInovacao
from app.models.projeto import DemandaProjeto
from app.models.usuario import Usuario
from app.services.inovacao import TIPOS_COMPETENCIA_PADRAO, buscar_competencias
from app.web.templates import templates

router = APIRouter(prefix="/painel/inovacao", tags=["Área restrita — Inovação"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _pode_gerir(db: Session, usuario: Usuario, cpl_id: uuid.UUID) -> bool:
    return any(
        v.papel in PAPEIS_PROJETO_GESTAO and (v.cpl_id is None or v.cpl_id == cpl_id)
        for v in papeis_do_usuario(db, usuario)
    )


@router.get("/demandas/{demanda_id}")
def matchmaking(
    request: Request,
    demanda_id: uuid.UUID,
    termo: str | None = None,
    tipo: str | None = None,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    demanda = db.get(DemandaProjeto, demanda_id)
    if demanda is None:
        return RedirectResponse("/painel/projetos", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_PROJETO_LEITURA, cpl_id=demanda.cpl_id)

    tipo_filtro = TipoEntidade(tipo) if tipo else None
    candidatos = buscar_competencias(db, termo=termo, tipos=[tipo_filtro] if tipo_filtro else None)
    ofertas_por_entidade = {
        entidade.id: db.query(OfertaEntidade).filter(OfertaEntidade.entidade_id == entidade.id).all()
        for entidade in candidatos
    }

    matches = (
        db.query(MatchInovacao)
        .filter(MatchInovacao.demanda_id == demanda_id)
        .order_by(MatchInovacao.created_at.desc())
        .all()
    )
    entidades_ja_sugeridas = {m.entidade_id for m in matches}

    return templates.TemplateResponse(
        request,
        "restrito/inovacao/demanda_matches.html",
        {
            "demanda": demanda,
            "candidatos": candidatos,
            "ofertas_por_entidade": ofertas_por_entidade,
            "entidades_ja_sugeridas": entidades_ja_sugeridas,
            "matches": matches,
            "tipos": TIPOS_COMPETENCIA_PADRAO,
            "filtro_termo": termo or "",
            "filtro_tipo": tipo_filtro,
            "status_opcoes": list(StatusMatchInovacao),
            "pode_gerir": _pode_gerir(db, usuario, demanda.cpl_id),
            "usuario": usuario,
            "pagina_ativa": "projetos",
        },
    )


@router.post("/demandas/{demanda_id}/matches")
def sugerir_match(
    demanda_id: uuid.UUID,
    entidade_id: uuid.UUID = Form(...),
    oferta_id: str | None = Form(None),
    observacao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    demanda = db.get(DemandaProjeto, demanda_id)
    if demanda is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demanda não encontrada.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=demanda.cpl_id)

    if db.get(Entidade, entidade_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    ja_existe = (
        db.query(MatchInovacao)
        .filter(MatchInovacao.demanda_id == demanda_id, MatchInovacao.entidade_id == entidade_id)
        .first()
    )
    if ja_existe is None:
        db.add(
            MatchInovacao(
                demanda_id=demanda_id,
                entidade_id=entidade_id,
                oferta_id=uuid.UUID(oferta_id) if oferta_id else None,
                observacao=observacao or None,
                sugerido_por_id=usuario.id,
            )
        )
        db.commit()
    return RedirectResponse(f"/painel/inovacao/demandas/{demanda_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/matches/{match_id}")
def atualizar_match(
    match_id: uuid.UUID,
    status_novo: StatusMatchInovacao = Form(..., alias="status"),
    observacao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    match = db.get(MatchInovacao, match_id)
    if match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Match não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=match.demanda.cpl_id)

    match.status = status_novo
    if observacao is not None:
        match.observacao = observacao or None
    db.commit()
    return RedirectResponse(
        f"/painel/inovacao/demandas/{match.demanda_id}", status_code=status.HTTP_303_SEE_OTHER
    )
