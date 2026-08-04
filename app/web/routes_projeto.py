import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import PAPEIS_PROJETO_GESTAO, PAPEIS_PROJETO_LEITURA, cpl_ids_visiveis, verificar_papel
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.enums import (
    EstagioProjeto,
    OrigemDemanda,
    PrioridadeProjeto,
    StatusDemanda,
    StatusTarefa,
)
from app.models.pessoa import Pessoa
from app.models.planejamento import ObjetivoEstrategico, PlanejamentoEstrategico
from app.models.projeto import DemandaProjeto, EtapaProjeto, Projeto
from app.models.usuario import Usuario
from app.web.templates import templates

router = APIRouter(prefix="/painel/projetos", tags=["Área restrita — Projetos"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _opt_uuid(valor: str | None) -> uuid.UUID | None:
    return uuid.UUID(valor) if valor else None


def _pessoas_e_objetivos(db: Session, cpl_id: uuid.UUID) -> tuple[list[Pessoa], list[ObjetivoEstrategico]]:
    pessoas = db.query(Pessoa).order_by(Pessoa.nome).all()
    objetivos = (
        db.query(ObjetivoEstrategico)
        .join(PlanejamentoEstrategico, ObjetivoEstrategico.planejamento_id == PlanejamentoEstrategico.id)
        .filter(PlanejamentoEstrategico.cpl_id == cpl_id)
        .order_by(ObjetivoEstrategico.created_at.desc())
        .all()
    )
    return pessoas, objetivos


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
        request, "restrito/projetos/cpls.html", {"cpls": cpls, "usuario": usuario, "pagina_ativa": "projetos"}
    )


@router.get("/cpls/{cpl_id}")
def portfolio(
    request: Request,
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        return RedirectResponse("/painel/projetos", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_PROJETO_LEITURA, cpl_id=cpl_id)

    demandas = (
        db.query(DemandaProjeto)
        .filter(DemandaProjeto.cpl_id == cpl_id, DemandaProjeto.status != StatusDemanda.CONVERTIDA_EM_PROJETO)
        .order_by(DemandaProjeto.created_at.desc())
        .all()
    )
    projetos = db.query(Projeto).filter(Projeto.cpl_id == cpl_id).order_by(Projeto.created_at.desc()).all()
    pessoas, objetivos = _pessoas_e_objetivos(db, cpl_id)
    return templates.TemplateResponse(
        request,
        "restrito/projetos/cpl_portfolio.html",
        {
            "cpl": cpl,
            "demandas": demandas,
            "projetos": projetos,
            "origens": list(OrigemDemanda),
            "prioridades": list(PrioridadeProjeto),
            "pessoas": pessoas,
            "objetivos": objetivos,
            "usuario": usuario,
            "pagina_ativa": "projetos",
        },
    )


@router.post("/cpls/{cpl_id}/demandas")
def criar_demanda(
    cpl_id: uuid.UUID,
    titulo: str = Form(...),
    descricao: str | None = Form(None),
    origem_tipo: OrigemDemanda = Form(...),
    origem_detalhe: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=cpl_id)
    demanda = DemandaProjeto(
        cpl_id=cpl_id,
        titulo=titulo,
        descricao=descricao or None,
        origem_tipo=origem_tipo,
        origem_detalhe=origem_detalhe or None,
        registrado_por_id=usuario.id,
    )
    db.add(demanda)
    db.commit()
    db.refresh(demanda)
    return RedirectResponse(f"/painel/projetos/demandas/{demanda.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/demandas/{demanda_id}")
def detalhe_demanda(
    request: Request,
    demanda_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    demanda = db.get(DemandaProjeto, demanda_id)
    if demanda is None:
        return RedirectResponse("/painel/projetos", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_PROJETO_LEITURA, cpl_id=demanda.cpl_id)
    cpl = db.get(CPL, demanda.cpl_id)
    pessoas, objetivos = _pessoas_e_objetivos(db, demanda.cpl_id)
    return templates.TemplateResponse(
        request,
        "restrito/projetos/demanda_detail.html",
        {
            "demanda": demanda,
            "cpl": cpl,
            "prioridades": list(PrioridadeProjeto),
            "pessoas": pessoas,
            "objetivos": objetivos,
            "usuario": usuario,
            "pagina_ativa": "projetos",
        },
    )


@router.post("/demandas/{demanda_id}/converter")
def converter_demanda(
    demanda_id: uuid.UUID,
    titulo: str = Form(...),
    descricao: str | None = Form(None),
    eixo_sp_produz: str | None = Form(None),
    prioridade: PrioridadeProjeto = Form(PrioridadeProjeto.MEDIA),
    responsavel_id: str | None = Form(None),
    objetivo_estrategico_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    demanda = db.get(DemandaProjeto, demanda_id)
    if demanda is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demanda de projeto não encontrada.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=demanda.cpl_id)
    if demanda.status == StatusDemanda.CONVERTIDA_EM_PROJETO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Demanda já foi convertida em projeto.")

    projeto = Projeto(
        cpl_id=demanda.cpl_id,
        demanda_origem_id=demanda.id,
        titulo=titulo,
        descricao=descricao or None,
        eixo_sp_produz=eixo_sp_produz or None,
        prioridade=prioridade,
        responsavel_id=_opt_uuid(responsavel_id),
        objetivo_estrategico_id=_opt_uuid(objetivo_estrategico_id),
    )
    demanda.status = StatusDemanda.CONVERTIDA_EM_PROJETO
    db.add(projeto)
    db.commit()
    db.refresh(projeto)
    return RedirectResponse(f"/painel/projetos/{projeto.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/cpls/{cpl_id}/projetos")
def criar_projeto(
    cpl_id: uuid.UUID,
    titulo: str = Form(...),
    descricao: str | None = Form(None),
    eixo_sp_produz: str | None = Form(None),
    prioridade: PrioridadeProjeto = Form(PrioridadeProjeto.MEDIA),
    responsavel_id: str | None = Form(None),
    objetivo_estrategico_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=cpl_id)
    projeto = Projeto(
        cpl_id=cpl_id,
        titulo=titulo,
        descricao=descricao or None,
        eixo_sp_produz=eixo_sp_produz or None,
        prioridade=prioridade,
        responsavel_id=_opt_uuid(responsavel_id),
        objetivo_estrategico_id=_opt_uuid(objetivo_estrategico_id),
    )
    db.add(projeto)
    db.commit()
    db.refresh(projeto)
    return RedirectResponse(f"/painel/projetos/{projeto.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{projeto_id}")
def detalhe_projeto(
    request: Request,
    projeto_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        return RedirectResponse("/painel/projetos", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_PROJETO_LEITURA, cpl_id=projeto.cpl_id)
    cpl = db.get(CPL, projeto.cpl_id)
    pessoas, objetivos = _pessoas_e_objetivos(db, projeto.cpl_id)
    etapas = (
        db.query(EtapaProjeto)
        .filter(EtapaProjeto.projeto_id == projeto_id)
        .order_by(EtapaProjeto.ordem)
        .all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/projetos/projeto_detail.html",
        {
            "projeto": projeto,
            "cpl": cpl,
            "estagios": list(EstagioProjeto),
            "prioridades": list(PrioridadeProjeto),
            "pessoas": pessoas,
            "objetivos": objetivos,
            "etapas": etapas,
            "status_opcoes": list(StatusTarefa),
            "usuario": usuario,
            "pagina_ativa": "projetos",
        },
    )


@router.post("/{projeto_id}")
def atualizar_projeto(
    projeto_id: uuid.UUID,
    titulo: str = Form(...),
    descricao: str | None = Form(None),
    eixo_sp_produz: str | None = Form(None),
    estagio: EstagioProjeto = Form(...),
    prioridade: PrioridadeProjeto = Form(...),
    responsavel_id: str | None = Form(None),
    objetivo_estrategico_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    projeto.titulo = titulo
    projeto.descricao = descricao or None
    projeto.eixo_sp_produz = eixo_sp_produz or None
    projeto.estagio = estagio
    projeto.prioridade = prioridade
    projeto.responsavel_id = _opt_uuid(responsavel_id)
    projeto.objetivo_estrategico_id = _opt_uuid(objetivo_estrategico_id)
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{projeto_id}/plano-de-trabalho")
def atualizar_plano_de_trabalho(
    projeto_id: uuid.UUID,
    introducao: str | None = Form(None),
    objeto: str | None = Form(None),
    objetivos: str | None = Form(None),
    justificativa: str | None = Form(None),
    impactos: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-033: informações básicas do plano de trabalho — separado do
    form de portfólio pra não misturar edição rápida de estágio/
    prioridade com o preenchimento mais longo do plano de trabalho."""

    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    projeto.introducao = introducao or None
    projeto.objeto = objeto or None
    projeto.objetivos = objetivos or None
    projeto.justificativa = justificativa or None
    projeto.impactos = impactos or None
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{projeto_id}/etapas")
def criar_etapa(
    projeto_id: uuid.UUID,
    titulo: str = Form(...),
    descricao: str | None = Form(None),
    data_inicio: str | None = Form(None),
    data_fim: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-034: etapa (ou atividade — mesmo nível) do plano de trabalho,
    com cronograma previsto. Entra no fim da lista."""

    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    maior_ordem = db.query(EtapaProjeto).filter(EtapaProjeto.projeto_id == projeto_id).count()
    etapa = EtapaProjeto(
        projeto_id=projeto_id,
        titulo=titulo,
        descricao=descricao or None,
        ordem=maior_ordem,
        data_inicio=date.fromisoformat(data_inicio) if data_inicio else None,
        data_fim=date.fromisoformat(data_fim) if data_fim else None,
    )
    db.add(etapa)
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/etapas/{etapa_id}/status")
def atualizar_status_etapa(
    etapa_id: uuid.UUID,
    status_etapa: StatusTarefa = Form(..., alias="status"),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    etapa = db.get(EtapaProjeto, etapa_id)
    if etapa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Etapa de projeto não encontrada.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=etapa.projeto.cpl_id)
    etapa.status = status_etapa
    db.commit()
    return RedirectResponse(f"/painel/projetos/{etapa.projeto_id}", status_code=status.HTTP_303_SEE_OTHER)
