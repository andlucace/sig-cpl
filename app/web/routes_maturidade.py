import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import (
    PAPEIS_AVALIACAO_EXECUCAO,
    PAPEIS_EDITAL_GESTAO,
    PAPEIS_GESTAO,
    PAPEIS_GOVERNANCA_LEITURA,
    cpl_ids_visiveis,
    verificar_papel,
)
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.documento import Documento
from app.models.enums import (
    CategoriaDocumento,
    ConfidencialidadeDocumento,
    DimensaoMaturidade,
    NivelMaturidade,
    StatusAvaliacao,
    StatusItemHabilitacao,
)
from app.models.maturidade import (
    Avaliacao,
    AvaliacaoCriterio,
    CriterioMaturidade,
    Edital,
    ItemHabilitacaoJuridica,
    RecursoAvaliacao,
)
from app.models.pessoa import Pessoa
from app.models.usuario import Usuario
from app.services.armazenamento import salvar_arquivo
from app.services.geracao_documentos import gerar_pdf_relatorio_recadastramento
from app.services.maturidade import (
    concluir_avaliacao,
    cpls_com_vencimento_proximo,
    decidir_nivel,
    lacunas,
    resumo_recadastramento,
    simular_avaliacao,
)
from app.web.templates import templates

router = APIRouter(prefix="/painel/maturidade", tags=["Área restrita — Maturidade"])


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _e_administrador(db: Session, usuario: Usuario) -> bool:
    return cpl_ids_visiveis(db, usuario) is None


def _opt_uuid(valor: str | None) -> uuid.UUID | None:
    return uuid.UUID(valor) if valor else None


@router.get("")
def dashboard(
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

    vencendo = cpls_com_vencimento_proximo(db, 90)
    if ids is not None:
        vencendo = [cpl for cpl in vencendo if cpl.id in ids]

    editais = db.query(Edital).order_by(Edital.ciclo.desc()).all()
    return templates.TemplateResponse(
        request,
        "restrito/maturidade/dashboard.html",
        {
            "cpls": cpls,
            "editais": editais,
            "vencendo": vencendo,
            "e_administrador": _e_administrador(db, usuario),
            "usuario": usuario,
            "pagina_ativa": "maturidade",
        },
    )


@router.post("/editais")
def criar_edital(
    request: Request,
    nome: str = Form(...),
    ciclo: str = Form(...),
    descricao: str | None = Form(None),
    data_inicio: str | None = Form(None),
    data_fim: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    edital = Edital(
        nome=nome,
        ciclo=ciclo,
        descricao=descricao or None,
        data_inicio=date.fromisoformat(data_inicio) if data_inicio else None,
        data_fim=date.fromisoformat(data_fim) if data_fim else None,
    )
    db.add(edital)
    db.commit()
    return RedirectResponse("/painel/maturidade", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/editais/{edital_id}")
def edital_detail(
    request: Request,
    edital_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    edital = db.get(Edital, edital_id)
    if edital is None:
        return RedirectResponse("/painel/maturidade", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=None)
    criterios = db.query(CriterioMaturidade).filter(CriterioMaturidade.edital_id == edital_id).all()
    return templates.TemplateResponse(
        request,
        "restrito/maturidade/edital_detail.html",
        {
            "edital": edital,
            "criterios": criterios,
            "dimensoes": list(DimensaoMaturidade),
            "e_administrador": _e_administrador(db, usuario),
            "usuario": usuario,
            "pagina_ativa": "maturidade",
        },
    )


@router.post("/editais/{edital_id}")
def atualizar_edital(
    edital_id: uuid.UUID,
    limiar_cpl_em_desenvolvimento: str | None = Form(None),
    limiar_cpl_consolidada: str | None = Form(None),
    limiar_cpl_madura: str | None = Form(None),
    ativo: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    edital = db.get(Edital, edital_id)
    if edital is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Edital não encontrado.")
    verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    edital.limiar_cpl_em_desenvolvimento = float(limiar_cpl_em_desenvolvimento) if limiar_cpl_em_desenvolvimento else None
    edital.limiar_cpl_consolidada = float(limiar_cpl_consolidada) if limiar_cpl_consolidada else None
    edital.limiar_cpl_madura = float(limiar_cpl_madura) if limiar_cpl_madura else None
    edital.ativo = ativo == "on"
    db.commit()
    return RedirectResponse(f"/painel/maturidade/editais/{edital_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/editais/{edital_id}/criterios")
def criar_criterio(
    edital_id: uuid.UUID,
    nome: str = Form(...),
    descricao: str | None = Form(None),
    dimensao: DimensaoMaturidade = Form(...),
    peso: float = Form(1.0),
    nota_corte: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    if db.get(Edital, edital_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Edital não encontrado.")
    verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    criterio = CriterioMaturidade(
        edital_id=edital_id,
        nome=nome,
        descricao=descricao or None,
        dimensao=dimensao,
        peso=peso,
        nota_corte=float(nota_corte) if nota_corte else None,
    )
    db.add(criterio)
    db.commit()
    return RedirectResponse(f"/painel/maturidade/editais/{edital_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/cpls/{cpl_id}")
def cpl_avaliacoes(
    request: Request,
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        return RedirectResponse("/painel/maturidade", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    avaliacoes = (
        db.query(Avaliacao).filter(Avaliacao.cpl_id == cpl_id).order_by(Avaliacao.data_avaliacao.desc()).all()
    )
    editais_ativos = db.query(Edital).filter(Edital.ativo.is_(True)).order_by(Edital.ciclo.desc()).all()
    itens_habilitacao = (
        db.query(ItemHabilitacaoJuridica)
        .filter(ItemHabilitacaoJuridica.cpl_id == cpl_id)
        .order_by(ItemHabilitacaoJuridica.created_at)
        .all()
    )
    pode_gerir_habilitacao = True
    try:
        verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)
    except HTTPException:
        pode_gerir_habilitacao = False

    return templates.TemplateResponse(
        request,
        "restrito/maturidade/cpl_avaliacoes.html",
        {
            "cpl": cpl,
            "avaliacoes": avaliacoes,
            "editais_ativos": editais_ativos,
            "itens_habilitacao": itens_habilitacao,
            "pode_gerir_habilitacao": pode_gerir_habilitacao,
            "e_administrador": _e_administrador(db, usuario),
            "usuario": usuario,
            "pagina_ativa": "maturidade",
        },
    )


@router.post("/cpls/{cpl_id}/relatorio-recadastramento")
def gerar_relatorio_recadastramento(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)

    pdf_bytes = gerar_pdf_relatorio_recadastramento(cpl, resumo_recadastramento(db, cpl_id))
    nome_arquivo = f"Relatorio de Recadastramento - {cpl.nome}.pdf"
    caminho = salvar_arquivo(cpl_id, nome_arquivo, pdf_bytes)
    documento = Documento(
        cpl_id=cpl_id,
        titulo=f"Relatório de Recadastramento — {cpl.nome}",
        categoria=CategoriaDocumento.RELATORIO,
        confidencialidade=ConfidencialidadeDocumento.INTERNO,
        arquivo_path=caminho,
        nome_arquivo_original=nome_arquivo,
        tipo_mime="application/pdf",
        tamanho_bytes=len(pdf_bytes),
        criado_por_id=usuario.id,
    )
    db.add(documento)
    db.commit()
    return RedirectResponse(f"/painel/documentos/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/cpls/{cpl_id}/avaliacoes")
def criar_avaliacao(
    cpl_id: uuid.UUID,
    edital_id: uuid.UUID = Form(...),
    data_avaliacao: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None or db.get(Edital, edital_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL ou edital não encontrado.")
    verificar_papel(db, usuario, PAPEIS_AVALIACAO_EXECUCAO, cpl_id=cpl_id)
    avaliacao = Avaliacao(
        cpl_id=cpl_id,
        edital_id=edital_id,
        avaliador_id=usuario.id,
        data_avaliacao=date.fromisoformat(data_avaliacao),
    )
    db.add(avaliacao)
    db.commit()
    db.refresh(avaliacao)
    return RedirectResponse(f"/painel/maturidade/avaliacoes/{avaliacao.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/avaliacoes/{avaliacao_id}")
def avaliacao_detail(
    request: Request,
    avaliacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avaliação não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=avaliacao.cpl_id)

    criterios = db.query(CriterioMaturidade).filter(CriterioMaturidade.edital_id == avaliacao.edital_id).all()
    notas_por_criterio = {n.criterio_id: n for n in avaliacao.notas}
    ids_lacunas = {n.id for n in lacunas(avaliacao)}
    simulacao = simular_avaliacao(avaliacao) if avaliacao.status == StatusAvaliacao.EM_ANDAMENTO else None

    pode_avaliar = True
    try:
        verificar_papel(db, usuario, PAPEIS_AVALIACAO_EXECUCAO, cpl_id=avaliacao.cpl_id)
    except HTTPException:
        pode_avaliar = False
    pode_decidir = True
    try:
        verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=avaliacao.cpl_id)
    except HTTPException:
        pode_decidir = False

    pessoas = db.query(Pessoa).order_by(Pessoa.nome).all()

    return templates.TemplateResponse(
        request,
        "restrito/maturidade/avaliacao_detail.html",
        {
            "avaliacao": avaliacao,
            "criterios": criterios,
            "notas_por_criterio": notas_por_criterio,
            "ids_lacunas": ids_lacunas,
            "simulacao": simulacao,
            "niveis": list(NivelMaturidade),
            "pessoas": pessoas,
            "pode_avaliar": pode_avaliar,
            "pode_decidir": pode_decidir,
            "e_administrador": _e_administrador(db, usuario),
            "usuario": usuario,
            "pagina_ativa": "maturidade",
        },
    )


@router.post("/avaliacoes/{avaliacao_id}/notas")
def lancar_nota(
    avaliacao_id: uuid.UUID,
    criterio_id: uuid.UUID = Form(...),
    nota: float = Form(...),
    observacao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avaliação não encontrada.")
    verificar_papel(db, usuario, PAPEIS_AVALIACAO_EXECUCAO, cpl_id=avaliacao.cpl_id)

    registro = (
        db.query(AvaliacaoCriterio)
        .filter(AvaliacaoCriterio.avaliacao_id == avaliacao_id, AvaliacaoCriterio.criterio_id == criterio_id)
        .first()
    )
    if registro is None:
        registro = AvaliacaoCriterio(avaliacao_id=avaliacao_id, criterio_id=criterio_id, nota=nota)
        db.add(registro)
    registro.nota = nota
    registro.observacao = observacao or None
    db.commit()
    return RedirectResponse(f"/painel/maturidade/avaliacoes/{avaliacao_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/avaliacoes/{avaliacao_id}/concluir")
def concluir(
    avaliacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avaliação não encontrada.")
    verificar_papel(db, usuario, PAPEIS_AVALIACAO_EXECUCAO, cpl_id=avaliacao.cpl_id)
    concluir_avaliacao(db, avaliacao)
    return RedirectResponse(f"/painel/maturidade/avaliacoes/{avaliacao_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/avaliacoes/{avaliacao_id}/decidir")
def decidir(
    avaliacao_id: uuid.UUID,
    nivel_decidido: NivelMaturidade = Form(...),
    parecer: str | None = Form(None),
    decidido_por_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avaliação não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=avaliacao.cpl_id)
    decidir_nivel(db, avaliacao, nivel_decidido, parecer or None, _opt_uuid(decidido_por_id))
    return RedirectResponse(f"/painel/maturidade/avaliacoes/{avaliacao_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/avaliacoes/{avaliacao_id}/recurso")
def solicitar_recurso(
    avaliacao_id: uuid.UUID,
    justificativa: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avaliação não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=avaliacao.cpl_id)
    if avaliacao.recurso is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Já existe um recurso para esta avaliação.")
    db.add(
        RecursoAvaliacao(avaliacao_id=avaliacao_id, justificativa=justificativa, solicitado_por_id=usuario.id)
    )
    db.commit()
    return RedirectResponse(f"/painel/maturidade/avaliacoes/{avaliacao_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/recursos/{recurso_id}/decidir")
def decidir_recurso(
    recurso_id: uuid.UUID,
    decisao: str = Form(...),
    parecer_decisao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    recurso = db.get(RecursoAvaliacao, recurso_id)
    if recurso is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recurso não encontrado.")
    verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    recurso.status = decisao
    recurso.parecer_decisao = parecer_decisao or None
    recurso.decidido_por_id = usuario.id
    recurso.data_decisao = date.today()
    db.commit()
    return RedirectResponse(
        f"/painel/maturidade/avaliacoes/{recurso.avaliacao_id}", status_code=status.HTTP_303_SEE_OTHER
    )


# --- Habilitação jurídica (RF-027) -------------------------------------------


@router.post("/cpls/{cpl_id}/habilitacao")
def criar_item_habilitacao(
    cpl_id: uuid.UUID,
    edital_id: uuid.UUID = Form(...),
    descricao: str = Form(...),
    obrigatorio: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-027: item do checklist de habilitação jurídica da CPL perante
    um edital — etapa que precede a avaliação de maturidade."""

    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None or db.get(Edital, edital_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL ou edital não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)
    db.add(
        ItemHabilitacaoJuridica(
            cpl_id=cpl_id, edital_id=edital_id, descricao=descricao, obrigatorio=obrigatorio == "on"
        )
    )
    db.commit()
    return RedirectResponse(f"/painel/maturidade/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/habilitacao/{item_id}/comprovante")
async def anexar_comprovante_habilitacao(
    item_id: uuid.UUID,
    arquivo: UploadFile,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    item = db.get(ItemHabilitacaoJuridica, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item de habilitação não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=item.cpl_id)

    conteudo = await arquivo.read()
    caminho = salvar_arquivo(item.cpl_id, arquivo.filename or "comprovante", conteudo)
    documento = Documento(
        cpl_id=item.cpl_id,
        titulo=f"Habilitação jurídica — {item.descricao}",
        categoria=CategoriaDocumento.DECLARACAO,
        confidencialidade=ConfidencialidadeDocumento.INTERNO,
        arquivo_path=caminho,
        nome_arquivo_original=arquivo.filename or "comprovante",
        tipo_mime=arquivo.content_type,
        tamanho_bytes=len(conteudo),
        criado_por_id=usuario.id,
    )
    db.add(documento)
    db.flush()
    item.documento_id = documento.id
    item.status = StatusItemHabilitacao.ENTREGUE
    db.commit()
    return RedirectResponse(f"/painel/maturidade/cpls/{item.cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/habilitacao/{item_id}/analisar")
def analisar_item_habilitacao(
    item_id: uuid.UUID,
    status_item: StatusItemHabilitacao = Form(..., alias="status"),
    parecer: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """Análise (aprovar/rejeitar) é sempre de quem gere os editais —
    mesma autoridade de `decidir_recurso` — é o órgão externo do edital
    validando a regularidade jurídica, não uma decisão interna da CPL."""

    if redir := _exigir_login(usuario):
        return redir
    item = db.get(ItemHabilitacaoJuridica, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item de habilitação não encontrado.")
    verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    item.status = status_item
    item.parecer = parecer or None
    item.analisado_por_id = usuario.id
    item.data_analise = date.today()
    db.commit()
    return RedirectResponse(f"/painel/maturidade/cpls/{item.cpl_id}", status_code=status.HTTP_303_SEE_OTHER)
