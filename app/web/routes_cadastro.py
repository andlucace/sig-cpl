import secrets
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import PAPEIS_GESTAO, PAPEIS_GOVERNANCA_LEITURA, cpl_ids_visiveis, verificar_papel
from app.db.session import get_db
from app.models.cadastro_dinamico import CampanhaCadastral, CampanhaConvite, DiagnosticoCadastral, ImportacaoLote
from app.models.cpl import CPL
from app.models.entidade import Entidade, EntidadeCPL, OfertaEntidade
from app.models.enums import StatusLoteImportacao, TipoOferta
from app.models.usuario import Usuario
from app.services.armazenamento import caminho_absoluto
from app.services.indicadores import diagnostico_desatualizado
from app.services.importacao_entidades import (
    CAMPOS_CONHECIDOS,
    confirmar_importacao,
    exportar_entidades,
    gerar_csv_entidades,
    gerar_xlsx_entidades,
    ler_planilha,
    mapear_colunas,
    preparar_importacao,
)
from app.web.templates import templates

_MEDIA_TYPES_EXPORTACAO = {
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

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
    """RF-013 (remapeamento manual): só salva o arquivo e sugere o
    mapeamento — não processa nenhuma linha ainda. Confirme (ou ajuste)
    em `/painel/cadastro/importacoes/{lote_id}/mapear`."""

    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)
    if not arquivo.filename or not arquivo.filename.lower().endswith((".csv", ".xlsx", ".xlsm")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Envie um arquivo .csv, .xlsx ou .xlsm.")
    conteudo = await arquivo.read()
    lote, _, _ = preparar_importacao(db, cpl_id, usuario.id, arquivo.filename, conteudo)
    return RedirectResponse(
        f"/painel/cadastro/importacoes/{lote.id}/mapear", status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/importacoes/{lote_id}/mapear")
def form_mapeamento_importacao(
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
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=lote.cpl_id)
    if lote.status != StatusLoteImportacao.PENDENTE_MAPEAMENTO:
        return RedirectResponse(
            f"/painel/cadastro/importacoes/{lote_id}", status_code=status.HTTP_303_SEE_OTHER
        )

    conteudo = caminho_absoluto(lote.arquivo_path).read_bytes()
    cabecalhos, linhas_dados = ler_planilha(lote.nome_arquivo, conteudo)
    mapeamento_sugerido = mapear_colunas(cabecalhos)
    return templates.TemplateResponse(
        request,
        "restrito/cadastro/importacao_mapear.html",
        {
            "lote": lote,
            "cabecalhos": list(enumerate(cabecalhos)),
            "total_linhas": len(linhas_dados),
            "campos": CAMPOS_CONHECIDOS,
            "mapeamento_sugerido": mapeamento_sugerido,
            "usuario": usuario,
            "pagina_ativa": "cadastro",
        },
    )


@router.post("/importacoes/{lote_id}/mapear")
async def confirmar_mapeamento_importacao(
    request: Request,
    lote_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    lote = db.get(ImportacaoLote, lote_id)
    if lote is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lote de importação não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=lote.cpl_id)
    if lote.status != StatusLoteImportacao.PENDENTE_MAPEAMENTO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este lote já foi processado.")

    # Número variável de campos (um <select> por campo conhecido) — não dá
    # pra declarar como parâmetros Form() fixos, por isso lê o form direto.
    form = await request.form()
    mapeamento = {}
    for campo in CAMPOS_CONHECIDOS:
        valor = form.get(f"campo__{campo}")
        if valor:
            mapeamento[campo] = int(valor)

    confirmar_importacao(db, lote, mapeamento)
    return RedirectResponse(f"/painel/cadastro/importacoes/{lote_id}", status_code=status.HTTP_303_SEE_OTHER)


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
    if lote.status == StatusLoteImportacao.PENDENTE_MAPEAMENTO:
        return RedirectResponse(
            f"/painel/cadastro/importacoes/{lote_id}/mapear", status_code=status.HTTP_303_SEE_OTHER
        )
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


@router.get("/cpls/{cpl_id}/exportar-entidades")
def exportar_entidades_cpl(
    cpl_id: uuid.UUID,
    formato: str = "xlsx",
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-053: exportação de entidades + diagnóstico cadastral em XLSX/CSV
    — simétrica à importação, mesmo cabeçalho de `CAMPOS_CONHECIDOS`."""

    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    if formato not in _MEDIA_TYPES_EXPORTACAO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato precisa ser 'xlsx' ou 'csv'.")

    linhas = exportar_entidades(db, cpl_id)
    conteudo = gerar_xlsx_entidades(linhas) if formato == "xlsx" else gerar_csv_entidades(linhas)
    return Response(
        content=conteudo,
        media_type=_MEDIA_TYPES_EXPORTACAO[formato],
        headers={"Content-Disposition": f'attachment; filename="entidades.{formato}"'},
    )


# --- Detalhe da entidade: canais digitais e ofertas (RF-010) ----------------


def _entidade_visivel_ou_none(db: Session, usuario: Usuario, entidade_id: uuid.UUID) -> Entidade | None:
    entidade = db.get(Entidade, entidade_id)
    if entidade is None:
        return None
    ids_visiveis = cpl_ids_visiveis(db, usuario)
    if ids_visiveis is not None:
        vinculada = (
            db.query(EntidadeCPL)
            .filter(EntidadeCPL.entidade_id == entidade_id, EntidadeCPL.cpl_id.in_(ids_visiveis))
            .first()
        )
        if vinculada is None:
            return None
    return entidade


@router.get("/entidades/{entidade_id}")
def detalhe_entidade(
    request: Request,
    entidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA)
    entidade = _entidade_visivel_ou_none(db, usuario, entidade_id)
    if entidade is None:
        return RedirectResponse("/painel/cadastro", status_code=status.HTTP_303_SEE_OTHER)

    diagnostico = (
        db.query(DiagnosticoCadastral).filter(DiagnosticoCadastral.entidade_id == entidade_id).first()
    )
    ofertas = (
        db.query(OfertaEntidade)
        .filter(OfertaEntidade.entidade_id == entidade_id)
        .order_by(OfertaEntidade.tipo, OfertaEntidade.nome)
        .all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/cadastro/entidade_detail.html",
        {
            "entidade": entidade,
            "diagnostico": diagnostico,
            "diagnostico_desatualizado": diagnostico_desatualizado(diagnostico) if diagnostico else False,
            "ofertas": ofertas,
            "tipos_oferta": list(TipoOferta),
            "usuario": usuario,
            "pagina_ativa": "cadastro",
        },
    )


@router.post("/entidades/{entidade_id}/canais-digitais")
def atualizar_canais_digitais(
    entidade_id: uuid.UUID,
    site: str | None = Form(None),
    instagram: str | None = Form(None),
    facebook: str | None = Form(None),
    linkedin: str | None = Form(None),
    whatsapp: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    entidade = db.get(Entidade, entidade_id)
    if entidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO)

    canais = {
        chave: valor
        for chave, valor in {
            "site": site,
            "instagram": instagram,
            "facebook": facebook,
            "linkedin": linkedin,
            "whatsapp": whatsapp,
        }.items()
        if valor
    }
    entidade.canais_digitais = canais or None
    db.commit()
    return RedirectResponse(
        f"/painel/cadastro/entidades/{entidade_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/entidades/{entidade_id}/ofertas")
def criar_oferta(
    entidade_id: uuid.UUID,
    tipo: TipoOferta = Form(...),
    nome: str = Form(...),
    descricao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-010: produto, serviço ou tecnologia ofertado pela entidade."""

    if redir := _exigir_login(usuario):
        return redir
    if db.get(Entidade, entidade_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO)

    oferta = OfertaEntidade(entidade_id=entidade_id, tipo=tipo, nome=nome, descricao=descricao or None)
    db.add(oferta)
    db.commit()
    return RedirectResponse(
        f"/painel/cadastro/entidades/{entidade_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/ofertas/{oferta_id}/desativar")
def desativar_oferta(
    oferta_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    oferta = db.get(OfertaEntidade, oferta_id)
    if oferta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Oferta não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO)
    oferta.ativo = False
    db.commit()
    return RedirectResponse(
        f"/painel/cadastro/entidades/{oferta.entidade_id}", status_code=status.HTTP_303_SEE_OTHER
    )
