import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import (
    PAPEIS_GESTAO,
    PAPEIS_GOVERNANCA_LEITURA,
    PAPEIS_GOVERNANCA_PARTICIPACAO,
    PAPEIS_TAREFA_EXECUCAO,
    cpl_ids_visiveis,
    verificar_papel,
)
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.enums import Elo, PrazoObjetivo, StatusPlanejamento, StatusTarefa, TipoDiagnostico
from app.models.pessoa import Pessoa
from app.models.planejamento import (
    DiagnosticoItem,
    IndicadorEstrategico,
    IniciativaEstrategica,
    MetaEstrategica,
    ObjetivoEstrategico,
    PlanejamentoEstrategico,
)
from app.models.usuario import Usuario
from app.web.templates import templates

router = APIRouter(prefix="/painel/planejamento", tags=["Área restrita — Planejamento"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _opt_float(valor: str | None) -> float | None:
    return float(valor) if valor else None


def _opt_date(valor: str | None) -> date | None:
    return date.fromisoformat(valor) if valor else None


def _opt_uuid(valor: str | None) -> uuid.UUID | None:
    return uuid.UUID(valor) if valor else None


def _opt_int(valor: str | None) -> int | None:
    return int(valor) if valor else None


def _pode_executar(usuario: Usuario, responsavel_id: uuid.UUID | None) -> bool:
    return usuario.pessoa_id is not None and usuario.pessoa_id == responsavel_id


# --- Seleção de CPL --------------------------------------------------------


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
        request,
        "restrito/planejamento/cpls.html",
        {"cpls": cpls, "usuario": usuario, "pagina_ativa": "planejamento"},
    )


# --- Planejamento Estratégico (RF-021) --------------------------------------


@router.get("/cpls/{cpl_id}")
def listar_planejamentos(
    request: Request,
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        return RedirectResponse("/painel/governanca", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    planejamentos = (
        db.query(PlanejamentoEstrategico)
        .filter(PlanejamentoEstrategico.cpl_id == cpl_id)
        .order_by(PlanejamentoEstrategico.ciclo.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/planejamento/cpl_planejamento.html",
        {"cpl": cpl, "planejamentos": planejamentos, "usuario": usuario, "pagina_ativa": "planejamento"},
    )


@router.post("/cpls/{cpl_id}")
def criar_planejamento(
    request: Request,
    cpl_id: uuid.UUID,
    ciclo: str = Form(...),
    caracterizacao: str | None = Form(None),
    historico: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)
    planejamento = PlanejamentoEstrategico(
        cpl_id=cpl_id,
        ciclo=ciclo,
        caracterizacao=caracterizacao or None,
        historico=historico or None,
    )
    db.add(planejamento)
    db.commit()
    db.refresh(planejamento)
    return templates.TemplateResponse(
        request, "restrito/planejamento/fragments/planejamento_item.html", {"planejamento": planejamento}
    )


@router.get("/{planejamento_id}")
def detalhe_planejamento(
    request: Request,
    planejamento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    planejamento = db.get(PlanejamentoEstrategico, planejamento_id)
    if planejamento is None:
        return RedirectResponse("/painel/governanca", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=planejamento.cpl_id)
    cpl = db.get(CPL, planejamento.cpl_id)
    diagnosticos = (
        db.query(DiagnosticoItem).filter(DiagnosticoItem.planejamento_id == planejamento_id).all()
    )
    objetivos = (
        db.query(ObjetivoEstrategico).filter(ObjetivoEstrategico.planejamento_id == planejamento_id).all()
    )
    pessoas = db.query(Pessoa).order_by(Pessoa.nome).all()
    return templates.TemplateResponse(
        request,
        "restrito/planejamento/planejamento_detail.html",
        {
            "planejamento": planejamento,
            "cpl": cpl,
            "diagnosticos": diagnosticos,
            "objetivos": objetivos,
            "pessoas": pessoas,
            "tipos_diagnostico": list(TipoDiagnostico),
            "elos": list(Elo),
            "prazos_objetivo": list(PrazoObjetivo),
            "status_opcoes": list(StatusPlanejamento),
            "status_opcoes_objetivo": list(StatusTarefa),
            "usuario": usuario,
            "pagina_ativa": "planejamento",
        },
    )


@router.post("/{planejamento_id}/narrativa")
def atualizar_narrativa_planejamento(
    planejamento_id: uuid.UUID,
    caracterizacao: str | None = Form(None),
    historico: str | None = Form(None),
    mercado: str | None = Form(None),
    inovacao: str | None = Form(None),
    impactos: str | None = Form(None),
    internacionalizacao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """Edição das seções narrativas do PEN (RF-021) — recarrega a página
    inteira (não é HTMX) porque atualiza vários blocos de texto ao mesmo
    tempo, não um item de lista."""

    if redir := _exigir_login(usuario):
        return redir
    planejamento = db.get(PlanejamentoEstrategico, planejamento_id)
    if planejamento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=planejamento.cpl_id)
    planejamento.caracterizacao = caracterizacao or None
    planejamento.historico = historico or None
    planejamento.mercado = mercado or None
    planejamento.inovacao = inovacao or None
    planejamento.impactos = impactos or None
    planejamento.internacionalizacao = internacionalizacao or None
    db.commit()
    return RedirectResponse(
        f"/painel/planejamento/{planejamento_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/{planejamento_id}/status")
def atualizar_status_planejamento(
    request: Request,
    planejamento_id: uuid.UUID,
    status_planejamento: StatusPlanejamento = Form(..., alias="status"),
    data_aprovacao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    planejamento = db.get(PlanejamentoEstrategico, planejamento_id)
    if planejamento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=planejamento.cpl_id)
    planejamento.status = status_planejamento
    planejamento.data_aprovacao = _opt_date(data_aprovacao)
    db.commit()
    db.refresh(planejamento)
    return templates.TemplateResponse(
        request,
        "restrito/planejamento/fragments/planejamento_status.html",
        {"planejamento": planejamento, "status_opcoes": list(StatusPlanejamento)},
    )


# --- Diagnóstico (RF-022) ---------------------------------------------------


@router.post("/{planejamento_id}/diagnosticos")
def criar_diagnostico(
    request: Request,
    planejamento_id: uuid.UUID,
    tipo: TipoDiagnostico = Form(...),
    descricao: str = Form(...),
    elo_relacionado: str | None = Form(None),
    prioridade: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    planejamento = db.get(PlanejamentoEstrategico, planejamento_id)
    if planejamento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_PARTICIPACAO, cpl_id=planejamento.cpl_id)
    item = DiagnosticoItem(
        planejamento_id=planejamento_id,
        tipo=tipo,
        descricao=descricao,
        elo_relacionado=Elo(elo_relacionado) if elo_relacionado else None,
        prioridade=_opt_int(prioridade),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return templates.TemplateResponse(
        request, "restrito/planejamento/fragments/diagnostico_item.html", {"item": item}
    )


# --- Objetivos (RF-023) ------------------------------------------------------


@router.post("/{planejamento_id}/objetivos")
def criar_objetivo(
    request: Request,
    planejamento_id: uuid.UUID,
    descricao: str = Form(...),
    prazo: PrazoObjetivo = Form(...),
    responsavel_id: str | None = Form(None),
    orcamento_estimado: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    planejamento = db.get(PlanejamentoEstrategico, planejamento_id)
    if planejamento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=planejamento.cpl_id)
    objetivo = ObjetivoEstrategico(
        planejamento_id=planejamento_id,
        descricao=descricao,
        prazo=prazo,
        responsavel_id=_opt_uuid(responsavel_id),
        orcamento_estimado=_opt_float(orcamento_estimado),
    )
    db.add(objetivo)
    db.commit()
    db.refresh(objetivo)
    return templates.TemplateResponse(
        request,
        "restrito/planejamento/fragments/objetivo_item.html",
        {"objetivo": objetivo, "status_opcoes": list(StatusTarefa)},
    )


@router.get("/objetivos/{objetivo_id}")
def detalhe_objetivo(
    request: Request,
    objetivo_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    objetivo = db.get(ObjetivoEstrategico, objetivo_id)
    if objetivo is None:
        return RedirectResponse("/painel/governanca", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=objetivo.planejamento.cpl_id)
    metas = db.query(MetaEstrategica).filter(MetaEstrategica.objetivo_id == objetivo_id).all()
    iniciativas = (
        db.query(IniciativaEstrategica).filter(IniciativaEstrategica.objetivo_id == objetivo_id).all()
    )
    indicadores = (
        db.query(IndicadorEstrategico).filter(IndicadorEstrategico.objetivo_id == objetivo_id).all()
    )
    pessoas = db.query(Pessoa).order_by(Pessoa.nome).all()
    return templates.TemplateResponse(
        request,
        "restrito/planejamento/objetivo_detail.html",
        {
            "objetivo": objetivo,
            "metas": metas,
            "iniciativas": iniciativas,
            "indicadores": indicadores,
            "pessoas": pessoas,
            "status_opcoes": list(StatusTarefa),
            "usuario": usuario,
            "pagina_ativa": "planejamento",
        },
    )


@router.post("/objetivos/{objetivo_id}/status")
def atualizar_status_objetivo(
    request: Request,
    objetivo_id: uuid.UUID,
    status_objetivo: StatusTarefa = Form(..., alias="status"),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    objetivo = db.get(ObjetivoEstrategico, objetivo_id)
    if objetivo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Objetivo não encontrado.")
    if not _pode_executar(usuario, objetivo.responsavel_id):
        verificar_papel(db, usuario, PAPEIS_TAREFA_EXECUCAO, cpl_id=objetivo.planejamento.cpl_id)
    objetivo.status = status_objetivo
    db.commit()
    db.refresh(objetivo)
    return templates.TemplateResponse(
        request,
        "restrito/planejamento/fragments/objetivo_item.html",
        {"objetivo": objetivo, "status_opcoes": list(StatusTarefa)},
    )


# --- Metas (RF-023/RN-010) ---------------------------------------------------


@router.post("/objetivos/{objetivo_id}/metas")
def criar_meta(
    request: Request,
    objetivo_id: uuid.UUID,
    descricao: str = Form(...),
    valor_alvo: str = Form(...),
    metodo_afericao: str | None = Form(None),
    prazo: str | None = Form(None),
    responsavel_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    objetivo = db.get(ObjetivoEstrategico, objetivo_id)
    if objetivo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Objetivo não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=objetivo.planejamento.cpl_id)
    meta = MetaEstrategica(
        objetivo_id=objetivo_id,
        descricao=descricao,
        valor_alvo=valor_alvo,
        metodo_afericao=metodo_afericao or None,
        prazo=_opt_date(prazo),
        responsavel_id=_opt_uuid(responsavel_id),
    )
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return templates.TemplateResponse(
        request,
        "restrito/planejamento/fragments/meta_item.html",
        {"meta": meta, "status_opcoes": list(StatusTarefa)},
    )


@router.post("/metas/{meta_id}/status")
def atualizar_status_meta(
    request: Request,
    meta_id: uuid.UUID,
    status_meta: StatusTarefa = Form(..., alias="status"),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    meta = db.get(MetaEstrategica, meta_id)
    if meta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Meta não encontrada.")
    if not _pode_executar(usuario, meta.responsavel_id):
        verificar_papel(db, usuario, PAPEIS_TAREFA_EXECUCAO, cpl_id=meta.objetivo.planejamento.cpl_id)
    meta.status = status_meta
    db.commit()
    db.refresh(meta)
    return templates.TemplateResponse(
        request,
        "restrito/planejamento/fragments/meta_item.html",
        {"meta": meta, "status_opcoes": list(StatusTarefa)},
    )


# --- Iniciativas (RF-023) ----------------------------------------------------


@router.post("/objetivos/{objetivo_id}/iniciativas")
def criar_iniciativa(
    request: Request,
    objetivo_id: uuid.UUID,
    titulo: str = Form(...),
    descricao: str | None = Form(None),
    responsavel_id: str | None = Form(None),
    prazo: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    objetivo = db.get(ObjetivoEstrategico, objetivo_id)
    if objetivo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Objetivo não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=objetivo.planejamento.cpl_id)
    iniciativa = IniciativaEstrategica(
        objetivo_id=objetivo_id,
        titulo=titulo,
        descricao=descricao or None,
        responsavel_id=_opt_uuid(responsavel_id),
        prazo=_opt_date(prazo),
    )
    db.add(iniciativa)
    db.commit()
    db.refresh(iniciativa)
    return templates.TemplateResponse(
        request,
        "restrito/planejamento/fragments/iniciativa_item.html",
        {"iniciativa": iniciativa, "status_opcoes": list(StatusTarefa)},
    )


@router.post("/iniciativas/{iniciativa_id}/status")
def atualizar_status_iniciativa(
    request: Request,
    iniciativa_id: uuid.UUID,
    status_iniciativa: StatusTarefa = Form(..., alias="status"),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    iniciativa = db.get(IniciativaEstrategica, iniciativa_id)
    if iniciativa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Iniciativa não encontrada.")
    if not _pode_executar(usuario, iniciativa.responsavel_id):
        verificar_papel(
            db, usuario, PAPEIS_TAREFA_EXECUCAO, cpl_id=iniciativa.objetivo.planejamento.cpl_id
        )
    iniciativa.status = status_iniciativa
    db.commit()
    db.refresh(iniciativa)
    return templates.TemplateResponse(
        request,
        "restrito/planejamento/fragments/iniciativa_item.html",
        {"iniciativa": iniciativa, "status_opcoes": list(StatusTarefa)},
    )


# --- Indicadores (RF-023) ----------------------------------------------------


@router.post("/objetivos/{objetivo_id}/indicadores")
def criar_indicador(
    request: Request,
    objetivo_id: uuid.UUID,
    nome: str = Form(...),
    formula: str | None = Form(None),
    unidade: str | None = Form(None),
    meta_valor: str | None = Form(None),
    periodicidade: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    objetivo = db.get(ObjetivoEstrategico, objetivo_id)
    if objetivo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Objetivo não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=objetivo.planejamento.cpl_id)
    indicador = IndicadorEstrategico(
        objetivo_id=objetivo_id,
        nome=nome,
        formula=formula or None,
        unidade=unidade or None,
        meta_valor=meta_valor or None,
        periodicidade=periodicidade or None,
    )
    db.add(indicador)
    db.commit()
    db.refresh(indicador)
    return templates.TemplateResponse(
        request, "restrito/planejamento/fragments/indicador_item.html", {"indicador": indicador}
    )


@router.post("/indicadores/{indicador_id}/valor")
def atualizar_valor_indicador(
    request: Request,
    indicador_id: uuid.UUID,
    valor_atual: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    indicador = db.get(IndicadorEstrategico, indicador_id)
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador não encontrado.")
    verificar_papel(db, usuario, PAPEIS_TAREFA_EXECUCAO, cpl_id=indicador.objetivo.planejamento.cpl_id)
    indicador.valor_atual = valor_atual or None
    db.commit()
    db.refresh(indicador)
    return templates.TemplateResponse(
        request, "restrito/planejamento/fragments/indicador_item.html", {"indicador": indicador}
    )
