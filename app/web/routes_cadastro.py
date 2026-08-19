import secrets
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import (
    PAPEIS_GESTAO,
    PAPEIS_GOVERNANCA_LEITURA,
    PAPEIS_LEITURA_MEMBRO,
    cpl_ids_visiveis,
    entidade_e_da_pessoa,
    verificar_papel,
)
from app.db.session import get_db
from app.models.adesao import SolicitacaoAdesao
from app.models.cadastro_dinamico import (
    CampanhaCadastral,
    CampanhaConvite,
    DiagnosticoCadastral,
    ImportacaoLote,
)
from app.models.cpl import CPL
from app.models.entidade import Entidade, EntidadeCPL, OfertaEntidade
from app.models.enums import StatusLoteImportacao, StatusSolicitacaoAdesao, TipoEntidade, TipoOferta
from app.models.usuario import Usuario
from app.services.adesao import SolicitacaoInvalida, aprovar_solicitacao, rejeitar_solicitacao
from app.services.armazenamento import caminho_absoluto
from app.services.campanhas import enviar_convite_email
from app.services.geocodificacao import GeocodificacaoIndisponivel, geocodificar_endereco
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
from app.services.indicadores import diagnostico_desatualizado
from app.services.integracao_publica import ConsultaCNPJIndisponivel, consultar_cnpj_publico
from app.services.validadores import cnpj_valido, cpf_valido, normalizar_cnpj, normalizar_cpf, uf_valida
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


@router.get("/modelo-planilha")
def modelo_planilha(
    formato: str = "xlsx",
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """Planilha-modelo pra ajudar quem vai importar (pedido explícito dos
    gestores) — mesmo cabeçalho de `CAMPOS_CONHECIDOS` que a importação
    reconhece, sem nenhuma linha de dado (`gerar_xlsx_entidades`/
    `gerar_csv_entidades` já aceitam lista vazia, mesma função usada na
    exportação real, RF-053 — não precisou de código novo ali). Não é
    escopado por CPL: o cabeçalho é sempre o mesmo, então `cpl_id=None`
    em `verificar_papel` já basta (qualquer papel de gestão em qualquer
    CPL serve)."""

    if redir := _exigir_login(usuario):
        return redir
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=None)
    if formato not in _MEDIA_TYPES_EXPORTACAO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato precisa ser 'xlsx' ou 'csv'.")

    conteudo = gerar_xlsx_entidades([]) if formato == "xlsx" else gerar_csv_entidades([])
    return Response(
        content=conteudo,
        media_type=_MEDIA_TYPES_EXPORTACAO[formato],
        headers={"Content-Disposition": f'attachment; filename="modelo-entidades.{formato}"'},
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
            "tipos_entidade": list(TipoEntidade),
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


def _validar_mascaras(cnpj: str | None, cpf: str | None, uf: str | None) -> None:
    """RF-014: mesma validação de formato (dígito verificador de CNPJ/CPF,
    UF pela lista fechada) já usada em `app/api/routes/entidades.py` —
    reaproveitada aqui pra não ficar divergente entre API e web."""

    if cnpj and not cnpj_valido(cnpj):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CNPJ inválido.")
    if cpf and not cpf_valido(cpf):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CPF inválido.")
    if uf and not uf_valida(uf):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "UF inválida.")


@router.post("/cpls/{cpl_id}/entidades")
def criar_entidade_para_cpl(
    cpl_id: uuid.UUID,
    tipo: TipoEntidade = Form(...),
    razao_social: str = Form(...),
    nome_fantasia: str | None = Form(None),
    cnpj: str | None = Form(None),
    cpf: str | None = Form(None),
    municipio: str | None = Form(None),
    uf: str | None = Form(None),
    email: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """Cadastra uma `Entidade` nova e já vincula direto a esta CPL, num
    passo só — diferente de `vincular_entidade` acima, que só linka uma
    entidade já existente. Antes disso só existia via API crua
    (`POST /api/entidades` + `POST .../vinculo` em duas chamadas), sem
    formulário nenhum na área restrita — o rodapé do card de "vincular
    entidade existente" chegava a apontar pro Swagger como alternativa.
    Escopado por `cpl_id` (`PAPEIS_GESTAO`) — mais estrito que
    `POST /api/entidades`, que não tem escopo de CPL porque cadastra sem
    necessariamente vincular a nenhuma; aqui o vínculo é imediato, então
    escopar pela CPL de destino é o comportamento certo."""

    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)
    _validar_mascaras(cnpj, cpf, uf)

    entidade = Entidade(
        tipo=tipo,
        razao_social=razao_social,
        nome_fantasia=nome_fantasia or None,
        cnpj=normalizar_cnpj(cnpj) if cnpj else None,
        cpf=normalizar_cpf(cpf) if cpf else None,
        municipio=municipio or None,
        uf=uf.strip().upper() if uf else None,
        email=email or None,
    )
    db.add(entidade)
    db.flush()
    db.add(EntidadeCPL(cpl_id=cpl_id, entidade_id=entidade.id, data_vinculo=date.today()))
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
    convite = enviar_convite_email(db, campanha, convite)
    return templates.TemplateResponse(
        request, "restrito/cadastro/fragments/convite_item.html", {"convite": convite}
    )


@router.post("/campanhas/{campanha_id}/convites/todas")
def convidar_todas_entidades(
    request: Request,
    campanha_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """Pedido explícito: convidar de uma vez todas as entidades vinculadas
    à CPL que ainda não foram convidadas nesta campanha, em vez de
    selecionar uma por vez no formulário ao lado."""

    if redir := _exigir_login(usuario):
        return redir
    campanha = db.get(CampanhaCadastral, campanha_id)
    if campanha is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campanha não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=campanha.cpl_id)

    ids_convidadas = {
        c.entidade_id
        for c in db.query(CampanhaConvite).filter(CampanhaConvite.campanha_id == campanha_id).all()
    }
    vinculos = db.query(EntidadeCPL).filter(
        EntidadeCPL.cpl_id == campanha.cpl_id, EntidadeCPL.ativo.is_(True)
    ).all()
    novos_convites = []
    for vinculo in vinculos:
        if vinculo.entidade_id in ids_convidadas:
            continue
        convite = CampanhaConvite(
            campanha_id=campanha_id, entidade_id=vinculo.entidade_id, token=secrets.token_urlsafe(24)
        )
        db.add(convite)
        db.commit()
        db.refresh(convite)
        novos_convites.append(enviar_convite_email(db, campanha, convite))
    return templates.TemplateResponse(
        request, "restrito/cadastro/fragments/convites_lista.html", {"convites": novos_convites}
    )


@router.post("/campanhas/convites/{convite_id}/reenviar")
def reenviar_convite(
    request: Request,
    convite_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """Pedido explícito: enviar o convite mais de uma vez para uma
    entidade já selecionada — reenvia o mesmo link/token, sem criar um
    `CampanhaConvite` novo."""

    if redir := _exigir_login(usuario):
        return redir
    convite = db.get(CampanhaConvite, convite_id)
    if convite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Convite não encontrado.")
    campanha = convite.campanha
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=campanha.cpl_id)
    convite = enviar_convite_email(db, campanha, convite)
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
    if entidade_e_da_pessoa(db, usuario, entidade_id):
        return entidade
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
    consultar_publico: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    # cpl_id=None: qualquer papel do grupo conta, independente da CPL — a
    # checagem fina de "esta entidade específica" é o papel de
    # `_entidade_visivel_ou_none` logo abaixo (via CPL visível ou vínculo
    # direto da própria pessoa com a entidade).
    verificar_papel(db, usuario, PAPEIS_LEITURA_MEMBRO, cpl_id=None)
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

    dados_publicos = None
    erro_consulta_publica = None
    if consultar_publico:
        if not entidade.cnpj:
            erro_consulta_publica = "Esta entidade não tem CNPJ cadastrado."
        else:
            try:
                dados_publicos = consultar_cnpj_publico(entidade.cnpj)
            except (ValueError, ConsultaCNPJIndisponivel) as exc:
                erro_consulta_publica = str(exc)

    return templates.TemplateResponse(
        request,
        "restrito/cadastro/entidade_detail.html",
        {
            "entidade": entidade,
            "diagnostico": diagnostico,
            "diagnostico_desatualizado": diagnostico_desatualizado(diagnostico) if diagnostico else False,
            "ofertas": ofertas,
            "tipos_oferta": list(TipoOferta),
            "dados_publicos": dados_publicos,
            "erro_consulta_publica": erro_consulta_publica,
            "usuario": usuario,
            "pagina_ativa": "cadastro",
        },
    )


@router.post("/entidades/{entidade_id}/dados-publicos/aplicar")
def aplicar_dados_publicos(
    entidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-054: reconsulta (não confia em valor vindo do formulário) e
    aplica os dados oficiais do CNPJ na entidade — só os campos que têm
    lugar próprio no cadastro (`Entidade` não guarda telefone/e-mail de
    contato, esses ficam só na tela de conferência)."""

    if redir := _exigir_login(usuario):
        return redir
    verificar_papel(db, usuario, PAPEIS_GESTAO)
    entidade = _entidade_visivel_ou_none(db, usuario, entidade_id)
    if entidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    if not entidade.cnpj:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta entidade não tem CNPJ cadastrado.")

    try:
        dados = consultar_cnpj_publico(entidade.cnpj)
    except (ValueError, ConsultaCNPJIndisponivel) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    if dados["razao_social"]:
        entidade.razao_social = dados["razao_social"]
    entidade.nome_fantasia = dados["nome_fantasia"]
    entidade.situacao_cadastral = dados["situacao_cadastral"]
    entidade.cnae = dados["cnae"]
    entidade.endereco = dados["endereco"]
    entidade.municipio = dados["municipio"]
    entidade.uf = dados["uf"]
    db.commit()
    return RedirectResponse(f"/painel/cadastro/entidades/{entidade_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/entidades/{entidade_id}/geocodificar")
def geocodificar_entidade_web(
    entidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-011: geocodifica a partir de endereco/municipio/uf via
    Nominatim/OpenStreetMap — endereço não encontrado só impede a
    entidade de aparecer no mapa, não é erro que trava a tela."""

    if redir := _exigir_login(usuario):
        return redir
    verificar_papel(db, usuario, PAPEIS_GESTAO)
    entidade = _entidade_visivel_ou_none(db, usuario, entidade_id)
    if entidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")

    try:
        resultado = geocodificar_endereco(entidade.endereco, entidade.municipio, entidade.uf)
    except (ValueError, GeocodificacaoIndisponivel):
        pass
    else:
        entidade.latitude = resultado["latitude"]
        entidade.longitude = resultado["longitude"]
        db.commit()
    return RedirectResponse(f"/painel/cadastro/entidades/{entidade_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/entidades/{entidade_id}/localizacao")
def definir_localizacao_web(
    entidade_id: uuid.UUID,
    latitude: float = Form(...),
    longitude: float = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    verificar_papel(db, usuario, PAPEIS_GESTAO)
    entidade = _entidade_visivel_ou_none(db, usuario, entidade_id)
    if entidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    entidade.latitude = latitude
    entidade.longitude = longitude
    db.commit()
    return RedirectResponse(f"/painel/cadastro/entidades/{entidade_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/cpls/{cpl_id}/mapa")
def mapa_cpl(
    request: Request,
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-011: mapa de concentração territorial da CPL — entidades
    geocodificadas, coloridas por tipo (empresa, universidade, ICT,
    prestador, ambiente de inovação) como proxy visual dos diferentes
    elos da cadeia. Não desenha vínculo formal de elo entre entidades
    (RF-009 `EntidadeElo` ainda não tem rota própria de API) — decisão
    de escopo, não lacuna esquecida."""

    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        return RedirectResponse("/painel/cadastro", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)

    entidades_geo = (
        db.query(Entidade)
        .join(EntidadeCPL, EntidadeCPL.entidade_id == Entidade.id)
        .filter(
            EntidadeCPL.cpl_id == cpl_id,
            EntidadeCPL.ativo.is_(True),
            Entidade.latitude.is_not(None),
            Entidade.longitude.is_not(None),
        )
        .all()
    )
    total_vinculadas = (
        db.query(EntidadeCPL).filter(EntidadeCPL.cpl_id == cpl_id, EntidadeCPL.ativo.is_(True)).count()
    )
    return templates.TemplateResponse(
        request,
        "restrito/cadastro/mapa.html",
        {
            "cpl": cpl,
            "entidades_geo": entidades_geo,
            "total_geocodificadas": len(entidades_geo),
            "total_vinculadas": total_vinculadas,
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


@router.post("/entidades/{entidade_id}/email")
def atualizar_email_entidade(
    entidade_id: uuid.UUID,
    email: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """RF-012: e-mail de comunicações da entidade, editável a qualquer
    momento — é o destinatário usado pelo convite automático de campanha
    (`app/services/campanhas.py`), então precisa dar pra corrigir/
    preencher depois, não só na criação."""

    if redir := _exigir_login(usuario):
        return redir
    entidade = db.get(Entidade, entidade_id)
    if entidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO)
    entidade.email = email or None
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


@router.get("/cpls/{cpl_id}/solicitacoes-adesao")
def solicitacoes_adesao_cpl(
    cpl_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """F01: tela de "validação" do fluxo de autoatendimento — pendentes
    primeiro, histórico (aprovadas/rejeitadas) depois."""

    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)

    solicitacoes = (
        db.query(SolicitacaoAdesao)
        .filter(SolicitacaoAdesao.cpl_id == cpl_id)
        .order_by(SolicitacaoAdesao.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/cadastro/solicitacoes_adesao.html",
        {
            "cpl": cpl,
            "pendentes": [s for s in solicitacoes if s.status == StatusSolicitacaoAdesao.PENDENTE],
            "analisadas": [s for s in solicitacoes if s.status != StatusSolicitacaoAdesao.PENDENTE],
        },
    )


def _solicitacao_do_gestor_ou_404(db: Session, usuario: Usuario, solicitacao_id: uuid.UUID) -> SolicitacaoAdesao:
    solicitacao = db.get(SolicitacaoAdesao, solicitacao_id)
    if solicitacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Solicitação de adesão não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=solicitacao.cpl_id)
    return solicitacao


@router.post("/solicitacoes-adesao/{solicitacao_id}/aprovar")
def aprovar_solicitacao_adesao_web(
    solicitacao_id: uuid.UUID,
    parecer: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    solicitacao = _solicitacao_do_gestor_ou_404(db, usuario, solicitacao_id)
    try:
        aprovar_solicitacao(db, solicitacao, usuario.id, parecer or None)
    except SolicitacaoInvalida as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return RedirectResponse(
        f"/painel/cadastro/cpls/{solicitacao.cpl_id}/solicitacoes-adesao", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/solicitacoes-adesao/{solicitacao_id}/rejeitar")
def rejeitar_solicitacao_adesao_web(
    solicitacao_id: uuid.UUID,
    parecer: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    solicitacao = _solicitacao_do_gestor_ou_404(db, usuario, solicitacao_id)
    try:
        rejeitar_solicitacao(db, solicitacao, usuario.id, parecer or None)
    except SolicitacaoInvalida as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return RedirectResponse(
        f"/painel/cadastro/cpls/{solicitacao.cpl_id}/solicitacoes-adesao", status_code=status.HTTP_303_SEE_OTHER
    )
