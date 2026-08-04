import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import (
    PAPEIS_EDITAL_GESTAO,
    PAPEIS_PROJETO_GESTAO,
    PAPEIS_PROJETO_LEITURA,
    cpl_ids_visiveis,
    verificar_papel,
)
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.enums import (
    EstagioProjeto,
    ImpactoRisco,
    OrigemDemanda,
    PrioridadeProjeto,
    ProbabilidadeRisco,
    StatusDemanda,
    StatusRecurso,
    StatusRisco,
    StatusTarefa,
    TipoMeta,
    TipoRecursoSubmissao,
)
from app.models.pessoa import Pessoa
from app.models.planejamento import ObjetivoEstrategico, PlanejamentoEstrategico
from app.models.projeto import (
    AquisicaoProjeto,
    DemandaProjeto,
    EditalFomento,
    EquipeProjeto,
    EtapaProjeto,
    IndicadorProjeto,
    MetaProjeto,
    OrigemRecursoProjeto,
    Projeto,
    RecursoSubmissaoProjeto,
    RiscoProjeto,
)
from app.models.usuario import Usuario
from app.web.templates import templates

router = APIRouter(prefix="/painel/projetos", tags=["Área restrita — Projetos"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _opt_uuid(valor: str | None) -> uuid.UUID | None:
    return uuid.UUID(valor) if valor else None


def _e_administrador(db: Session, usuario: Usuario) -> bool:
    return cpl_ids_visiveis(db, usuario) is None


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
    editais_fomento = (
        db.query(EditalFomento).order_by(EditalFomento.data_abertura.desc().nullslast()).all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/projetos/cpls.html",
        {
            "cpls": cpls,
            "editais_fomento": editais_fomento,
            "e_administrador": _e_administrador(db, usuario),
            "usuario": usuario,
            "pagina_ativa": "projetos",
        },
    )


@router.post("/editais-fomento")
def criar_edital_fomento(
    titulo: str = Form(...),
    descricao: str | None = Form(None),
    requisitos: str | None = Form(None),
    documentos_exigidos: str | None = Form(None),
    data_abertura: str | None = Form(None),
    data_encerramento: str | None = Form(None),
    responsavel_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-029: edital de fomento — global, não escopado a uma CPL."""

    if redir := _exigir_login(usuario):
        return redir
    verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    edital = EditalFomento(
        titulo=titulo,
        descricao=descricao or None,
        requisitos=requisitos or None,
        documentos_exigidos=documentos_exigidos or None,
        data_abertura=date.fromisoformat(data_abertura) if data_abertura else None,
        data_encerramento=date.fromisoformat(data_encerramento) if data_encerramento else None,
        responsavel_id=_opt_uuid(responsavel_id),
    )
    db.add(edital)
    db.commit()
    db.refresh(edital)
    return RedirectResponse(f"/painel/projetos/editais-fomento/{edital.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/editais-fomento/{edital_id}")
def detalhe_edital_fomento(
    request: Request,
    edital_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    edital = db.get(EditalFomento, edital_id)
    if edital is None:
        return RedirectResponse("/painel/projetos", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_PROJETO_LEITURA, cpl_id=None)
    pessoas = db.query(Pessoa).order_by(Pessoa.nome).all()
    projetos_submetidos = (
        db.query(Projeto)
        .filter(Projeto.edital_fomento_id == edital_id)
        .order_by(Projeto.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/projetos/edital_fomento_detail.html",
        {
            "edital": edital,
            "pessoas": pessoas,
            "projetos_submetidos": projetos_submetidos,
            "e_administrador": _e_administrador(db, usuario),
            "usuario": usuario,
            "pagina_ativa": "projetos",
        },
    )


@router.post("/editais-fomento/{edital_id}")
def atualizar_edital_fomento(
    edital_id: uuid.UUID,
    titulo: str = Form(...),
    descricao: str | None = Form(None),
    requisitos: str | None = Form(None),
    documentos_exigidos: str | None = Form(None),
    data_abertura: str | None = Form(None),
    data_encerramento: str | None = Form(None),
    responsavel_id: str | None = Form(None),
    ativo: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    edital = db.get(EditalFomento, edital_id)
    if edital is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Edital de fomento não encontrado.")
    verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    edital.titulo = titulo
    edital.descricao = descricao or None
    edital.requisitos = requisitos or None
    edital.documentos_exigidos = documentos_exigidos or None
    edital.data_abertura = date.fromisoformat(data_abertura) if data_abertura else None
    edital.data_encerramento = date.fromisoformat(data_encerramento) if data_encerramento else None
    edital.responsavel_id = _opt_uuid(responsavel_id)
    edital.ativo = ativo == "on"
    db.commit()
    return RedirectResponse(f"/painel/projetos/editais-fomento/{edital_id}", status_code=status.HTTP_303_SEE_OTHER)


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
    metas = (
        db.query(MetaProjeto)
        .filter(MetaProjeto.projeto_id == projeto_id)
        .order_by(MetaProjeto.created_at)
        .all()
    )
    indicadores = (
        db.query(IndicadorProjeto)
        .filter(IndicadorProjeto.projeto_id == projeto_id)
        .order_by(IndicadorProjeto.created_at)
        .all()
    )
    riscos = (
        db.query(RiscoProjeto)
        .filter(RiscoProjeto.projeto_id == projeto_id)
        .order_by(RiscoProjeto.created_at)
        .all()
    )
    equipe = (
        db.query(EquipeProjeto)
        .filter(EquipeProjeto.projeto_id == projeto_id)
        .order_by(EquipeProjeto.created_at)
        .all()
    )
    origens_recurso = (
        db.query(OrigemRecursoProjeto)
        .filter(OrigemRecursoProjeto.projeto_id == projeto_id)
        .order_by(OrigemRecursoProjeto.created_at)
        .all()
    )
    editais_fomento_abertos = (
        db.query(EditalFomento).filter(EditalFomento.ativo.is_(True)).order_by(EditalFomento.titulo).all()
    )
    recursos_submissao = (
        db.query(RecursoSubmissaoProjeto)
        .filter(RecursoSubmissaoProjeto.projeto_id == projeto_id)
        .order_by(RecursoSubmissaoProjeto.created_at)
        .all()
    )
    aquisicoes = (
        db.query(AquisicaoProjeto)
        .filter(AquisicaoProjeto.projeto_id == projeto_id)
        .order_by(AquisicaoProjeto.created_at)
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
            "metas": metas,
            "tipos_meta": list(TipoMeta),
            "indicadores": indicadores,
            "riscos": riscos,
            "probabilidades_risco": list(ProbabilidadeRisco),
            "impactos_risco": list(ImpactoRisco),
            "status_risco_opcoes": list(StatusRisco),
            "equipe": equipe,
            "origens_recurso": origens_recurso,
            "editais_fomento_abertos": editais_fomento_abertos,
            "recursos_submissao": recursos_submissao,
            "tipos_recurso_submissao": list(TipoRecursoSubmissao),
            "status_recurso_opcoes": list(StatusRecurso),
            "aquisicoes": aquisicoes,
            "e_administrador": _e_administrador(db, usuario),
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
    impactos_socioambientais: str | None = Form(None),
    continuidade: str | None = Form(None),
    escalabilidade: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-033/034/035: informações básicas do plano de trabalho —
    separado do form de portfólio pra não misturar edição rápida de
    estágio/prioridade com o preenchimento mais longo do plano de
    trabalho."""

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
    projeto.impactos_socioambientais = impactos_socioambientais or None
    projeto.continuidade = continuidade or None
    projeto.escalabilidade = escalabilidade or None
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{projeto_id}/etapas")
def criar_etapa(
    projeto_id: uuid.UUID,
    titulo: str = Form(...),
    descricao: str | None = Form(None),
    data_inicio: str | None = Form(None),
    data_fim: str | None = Form(None),
    valor_previsto: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-034/035: etapa (ou atividade — mesmo nível) do plano de
    trabalho, com cronograma previsto e valor orçado (cronograma
    físico-financeiro). Entra no fim da lista."""

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
        valor_previsto=Decimal(valor_previsto) if valor_previsto else None,
    )
    db.add(etapa)
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/etapas/{etapa_id}/status")
def atualizar_status_etapa(
    etapa_id: uuid.UUID,
    status_etapa: StatusTarefa = Form(..., alias="status"),
    valor_executado: str | None = Form(None),
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
    etapa.valor_executado = Decimal(valor_executado) if valor_executado else None
    db.commit()
    return RedirectResponse(f"/painel/projetos/{etapa.projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{projeto_id}/metas")
def criar_meta(
    projeto_id: uuid.UUID,
    descricao: str = Form(...),
    tipo: TipoMeta = Form(...),
    valor_alvo: str | None = Form(None),
    prazo: str | None = Form(None),
    responsavel_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-034: meta quantitativa ou qualitativa do plano de trabalho."""

    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    meta = MetaProjeto(
        projeto_id=projeto_id,
        descricao=descricao,
        tipo=tipo,
        valor_alvo=valor_alvo or None,
        prazo=date.fromisoformat(prazo) if prazo else None,
        responsavel_id=_opt_uuid(responsavel_id),
    )
    db.add(meta)
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/metas/{meta_id}")
def atualizar_meta(
    meta_id: uuid.UUID,
    valor_alcancado: str | None = Form(None),
    status_meta: StatusTarefa = Form(..., alias="status"),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    meta = db.get(MetaProjeto, meta_id)
    if meta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Meta de projeto não encontrada.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=meta.projeto.cpl_id)
    meta.valor_alcancado = valor_alcancado or None
    meta.status = status_meta
    db.commit()
    return RedirectResponse(f"/painel/projetos/{meta.projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{projeto_id}/indicadores")
def criar_indicador(
    projeto_id: uuid.UUID,
    nome: str = Form(...),
    unidade_medida: str | None = Form(None),
    meta_valor: str | None = Form(None),
    responsavel_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-034: indicador de acompanhamento do projeto."""

    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    indicador = IndicadorProjeto(
        projeto_id=projeto_id,
        nome=nome,
        unidade_medida=unidade_medida or None,
        meta_valor=meta_valor or None,
        responsavel_id=_opt_uuid(responsavel_id),
    )
    db.add(indicador)
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/indicadores/{indicador_id}")
def atualizar_indicador(
    indicador_id: uuid.UUID,
    valor_atual: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    indicador = db.get(IndicadorProjeto, indicador_id)
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador de projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=indicador.projeto.cpl_id)
    indicador.valor_atual = valor_atual or None
    db.commit()
    return RedirectResponse(
        f"/painel/projetos/{indicador.projeto_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/{projeto_id}/riscos")
def criar_risco(
    projeto_id: uuid.UUID,
    descricao: str = Form(...),
    probabilidade: ProbabilidadeRisco = Form(...),
    impacto: ImpactoRisco = Form(...),
    resposta: str | None = Form(None),
    responsavel_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-034/040: risco identificado do projeto."""

    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    risco = RiscoProjeto(
        projeto_id=projeto_id,
        descricao=descricao,
        probabilidade=probabilidade,
        impacto=impacto,
        resposta=resposta or None,
        responsavel_id=_opt_uuid(responsavel_id),
    )
    db.add(risco)
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/riscos/{risco_id}/status")
def atualizar_status_risco(
    risco_id: uuid.UUID,
    status_risco: StatusRisco = Form(..., alias="status"),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    risco = db.get(RiscoProjeto, risco_id)
    if risco is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Risco de projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=risco.projeto.cpl_id)
    risco.status = status_risco
    db.commit()
    return RedirectResponse(f"/painel/projetos/{risco.projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{projeto_id}/equipe")
def adicionar_membro_equipe(
    projeto_id: uuid.UUID,
    pessoa_id: str = Form(...),
    funcao: str = Form(...),
    data_inicio: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-035: adiciona uma pessoa à equipe do projeto, com função e
    vigência — mesmo padrão de `MembroOrgao` (RF-016)."""

    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    membro = EquipeProjeto(
        projeto_id=projeto_id,
        pessoa_id=uuid.UUID(pessoa_id),
        funcao=funcao,
        data_inicio=date.fromisoformat(data_inicio),
    )
    db.add(membro)
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/equipe/{membro_id}/encerrar")
def encerrar_membro_equipe(
    membro_id: uuid.UUID,
    data_fim: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    membro = db.get(EquipeProjeto, membro_id)
    if membro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Membro de equipe do projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=membro.projeto.cpl_id)
    membro.data_fim = date.fromisoformat(data_fim) if data_fim else date.today()
    membro.ativo = False
    db.commit()
    return RedirectResponse(f"/painel/projetos/{membro.projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{projeto_id}/origens-recurso")
def criar_origem_recurso(
    projeto_id: uuid.UUID,
    fonte: str = Form(...),
    valor: str = Form(...),
    contrapartida: bool = Form(False),
    descricao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-035: registra uma fonte de recursos do projeto (própria, edital,
    parceria etc.) e o valor previsto."""

    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    origem = OrigemRecursoProjeto(
        projeto_id=projeto_id,
        fonte=fonte,
        valor=Decimal(valor),
        contrapartida=contrapartida,
        descricao=descricao or None,
    )
    db.add(origem)
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{projeto_id}/submeter")
def submeter_projeto(
    projeto_id: uuid.UUID,
    edital_fomento_id: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-029/030: submete o projeto a um edital de fomento — vincula o
    edital e move o estágio para SUBMETIDO na mesma ação."""

    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    edital = db.get(EditalFomento, uuid.UUID(edital_fomento_id))
    if edital is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Edital de fomento não encontrado.")
    projeto.edital_fomento_id = edital.id
    projeto.estagio = EstagioProjeto.SUBMETIDO
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{projeto_id}/recursos-submissao")
def criar_recurso_submissao(
    projeto_id: uuid.UUID,
    tipo: TipoRecursoSubmissao = Form(...),
    protocolo: str | None = Form(None),
    prazo: str | None = Form(None),
    descricao: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-030: recurso, contrarrazão ou diligência no processo de
    submissão do projeto a um edital de fomento."""

    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    recurso = RecursoSubmissaoProjeto(
        projeto_id=projeto_id,
        tipo=tipo,
        protocolo=protocolo or None,
        prazo=date.fromisoformat(prazo) if prazo else None,
        descricao=descricao,
        solicitado_por_id=usuario.id,
    )
    db.add(recurso)
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/recursos-submissao/{recurso_id}/decidir")
def decidir_recurso_submissao(
    recurso_id: uuid.UUID,
    status_recurso: StatusRecurso = Form(..., alias="status"),
    parecer_decisao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """Decisão é de quem administra o edital de fomento — autoridade
    diferente de quem gere o projeto que solicitou."""

    if redir := _exigir_login(usuario):
        return redir
    recurso = db.get(RecursoSubmissaoProjeto, recurso_id)
    if recurso is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recurso de submissão não encontrado.")
    verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    recurso.status = status_recurso
    recurso.parecer_decisao = parecer_decisao or None
    recurso.decidido_por_id = usuario.id
    recurso.data_decisao = date.today()
    db.commit()
    return RedirectResponse(f"/painel/projetos/{recurso.projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{projeto_id}/aquisicoes")
def criar_aquisicao(
    projeto_id: uuid.UUID,
    item: str = Form(...),
    descricao: str | None = Form(None),
    categoria: str | None = Form(None),
    quantidade: str | None = Form(None),
    valor_estimado: str | None = Form(None),
    data_prevista: str | None = Form(None),
    responsavel_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-035: item de aquisição planejado do projeto."""

    if redir := _exigir_login(usuario):
        return redir
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto não encontrado.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=projeto.cpl_id)
    aquisicao = AquisicaoProjeto(
        projeto_id=projeto_id,
        item=item,
        descricao=descricao or None,
        categoria=categoria or None,
        quantidade=quantidade or None,
        valor_estimado=Decimal(valor_estimado) if valor_estimado else None,
        data_prevista=date.fromisoformat(data_prevista) if data_prevista else None,
        responsavel_id=_opt_uuid(responsavel_id),
    )
    db.add(aquisicao)
    db.commit()
    return RedirectResponse(f"/painel/projetos/{projeto_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/aquisicoes/{aquisicao_id}/status")
def atualizar_status_aquisicao(
    aquisicao_id: uuid.UUID,
    status_aquisicao: StatusTarefa = Form(..., alias="status"),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    aquisicao = db.get(AquisicaoProjeto, aquisicao_id)
    if aquisicao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aquisição de projeto não encontrada.")
    verificar_papel(db, usuario, PAPEIS_PROJETO_GESTAO, cpl_id=aquisicao.projeto.cpl_id)
    aquisicao.status = status_aquisicao
    db.commit()
    return RedirectResponse(f"/painel/projetos/{aquisicao.projeto_id}", status_code=status.HTTP_303_SEE_OTHER)
