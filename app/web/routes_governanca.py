import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import (
    PAPEIS_GESTAO,
    PAPEIS_GOVERNANCA_LEITURA,
    PAPEIS_TAREFA_EXECUCAO,
    cpl_ids_visiveis,
    verificar_papel,
    verificar_participacao_orgao,
)
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.documento import Documento
from app.models.enums import (
    CategoriaDocumento,
    ConfidencialidadeDocumento,
    ResultadoDeliberacao,
    StatusReuniao,
    StatusTarefa,
    TipoOrgao,
    TipoVoto,
)
from app.models.governanca import (
    Deliberacao,
    MembroOrgao,
    OrgaoGovernanca,
    Presenca,
    Reuniao,
    TarefaGovernanca,
    VotoRegistro,
)
from app.models.pessoa import Pessoa
from app.models.usuario import Usuario
from app.services.armazenamento import salvar_arquivo
from app.services.geracao_documentos import gerar_pdf_relatorio_comissao
from app.services.governanca import enviar_convocacao_email
from app.services.indicadores import resumo_orgao
from app.web.templates import templates

router = APIRouter(prefix="/painel/governanca", tags=["Área restrita — Governança"])


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
        "restrito/governanca/cpls.html",
        {"cpls": cpls, "usuario": usuario, "pagina_ativa": "governanca"},
    )


# --- Órgãos (RF-015/RF-016) ------------------------------------------------


@router.get("/cpls/{cpl_id}")
def listar_orgaos(
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
    orgaos = (
        db.query(OrgaoGovernanca).filter(OrgaoGovernanca.cpl_id == cpl_id).order_by(OrgaoGovernanca.nome).all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/governanca/orgaos.html",
        {
            "cpl": cpl,
            "orgaos": orgaos,
            "tipos_orgao": list(TipoOrgao),
            "usuario": usuario,
            "pagina_ativa": "governanca",
        },
    )


@router.post("/cpls/{cpl_id}/orgaos")
def criar_orgao(
    request: Request,
    cpl_id: uuid.UUID,
    nome: str = Form(...),
    tipo: TipoOrgao = Form(...),
    competencias: str | None = Form(None),
    quorum_minimo_percentual: str | None = Form(None),
    periodicidade: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)
    orgao = OrgaoGovernanca(
        cpl_id=cpl_id,
        nome=nome,
        tipo=tipo,
        competencias=competencias or None,
        quorum_minimo_percentual=_opt_float(quorum_minimo_percentual),
        periodicidade=periodicidade or None,
    )
    db.add(orgao)
    db.commit()
    db.refresh(orgao)
    return templates.TemplateResponse(
        request, "restrito/governanca/fragments/orgao_item.html", {"orgao": orgao}
    )


@router.get("/orgaos/{orgao_id}")
def detalhe_orgao(
    request: Request,
    orgao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    orgao = db.get(OrgaoGovernanca, orgao_id)
    if orgao is None:
        return RedirectResponse("/painel/governanca", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=orgao.cpl_id)
    cpl = db.get(CPL, orgao.cpl_id)
    membros = db.query(MembroOrgao).filter(MembroOrgao.orgao_id == orgao_id).all()
    reunioes = (
        db.query(Reuniao).filter(Reuniao.orgao_id == orgao_id).order_by(Reuniao.data_hora.desc()).all()
    )
    pessoas = db.query(Pessoa).order_by(Pessoa.nome).all()
    documentos_orgao = (
        db.query(Documento).filter(Documento.orgao_id == orgao_id).order_by(Documento.created_at.desc()).all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/governanca/orgao_detail.html",
        {
            "orgao": orgao,
            "cpl": cpl,
            "membros": membros,
            "reunioes": reunioes,
            "pessoas": pessoas,
            "documentos_orgao": documentos_orgao,
            "categorias_documento": list(CategoriaDocumento),
            "confidencialidades_documento": list(ConfidencialidadeDocumento),
            "usuario": usuario,
            "pagina_ativa": "governanca",
        },
    )


@router.post("/orgaos/{orgao_id}/relatorio-comissao")
def gerar_relatorio_comissao(
    orgao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    orgao = db.get(OrgaoGovernanca, orgao_id)
    if orgao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Órgão de governança não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=orgao.cpl_id)

    pdf_bytes = gerar_pdf_relatorio_comissao(orgao, resumo_orgao(db, orgao_id))
    nome_arquivo = f"Relatorio de Comissao - {orgao.nome}.pdf"
    caminho = salvar_arquivo(orgao.cpl_id, nome_arquivo, pdf_bytes)
    documento = Documento(
        cpl_id=orgao.cpl_id,
        titulo=f"Relatório de Comissão — {orgao.nome}",
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
    return RedirectResponse(f"/painel/documentos/cpls/{orgao.cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


# --- Pessoas (cadastro rápido, RF-007) -------------------------------------


@router.post("/orgaos/{orgao_id}/pessoas-rapidas")
def criar_pessoa_rapida(
    orgao_id: uuid.UUID,
    nome: str = Form(...),
    email: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """Cadastro mínimo de pessoa (RF-007) direto da tela de órgão, para não
    obrigar o usuário a sair do fluxo de governança só para poder indicar um
    novo membro. Redireciona de volta (a lista de pessoas é recarregada)."""

    if redir := _exigir_login(usuario):
        return redir
    orgao = db.get(OrgaoGovernanca, orgao_id)
    if orgao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Órgão de governança não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=orgao.cpl_id)
    db.add(Pessoa(nome=nome, email=email or None))
    db.commit()
    return RedirectResponse(f"/painel/governanca/orgaos/{orgao_id}", status_code=status.HTTP_303_SEE_OTHER)


# --- Membros / mandatos (RF-016) -------------------------------------------


@router.post("/orgaos/{orgao_id}/membros")
def adicionar_membro(
    request: Request,
    orgao_id: uuid.UUID,
    pessoa_id: uuid.UUID = Form(...),
    funcao: str = Form(...),
    data_inicio: date = Form(...),
    data_fim: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    orgao = db.get(OrgaoGovernanca, orgao_id)
    if orgao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Órgão de governança não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=orgao.cpl_id)
    membro = MembroOrgao(
        orgao_id=orgao_id,
        pessoa_id=pessoa_id,
        funcao=funcao,
        data_inicio=data_inicio,
        data_fim=_opt_date(data_fim),
    )
    db.add(membro)
    db.commit()
    db.refresh(membro)
    return templates.TemplateResponse(
        request, "restrito/governanca/fragments/membro_item.html", {"membro": membro}
    )


@router.post("/membros/{membro_id}/remover")
def remover_membro(
    request: Request,
    membro_id: uuid.UUID,
    motivo: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """Exclusão de membro exige motivo (texto) — pedido explícito. Feita
    como desativação (`ativo=False`), não `DELETE` de verdade: preserva o
    histórico de mandato já registrado (presenças, votos) e cai sozinha
    na trilha de auditoria automática (`ativo`/`motivo_remocao` viram um
    ATUALIZACAO com o antes/depois, incluindo o motivo — sem chamada
    manual a `registrar_evento`, ver app/services/auditoria.py)."""

    if redir := _exigir_login(usuario):
        return redir
    membro = db.get(MembroOrgao, membro_id)
    if membro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Membro não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=membro.orgao.cpl_id)
    membro.ativo = False
    membro.motivo_remocao = motivo
    if membro.data_fim is None:
        membro.data_fim = date.today()
    db.commit()
    db.refresh(membro)
    return templates.TemplateResponse(
        request, "restrito/governanca/fragments/membro_item.html", {"membro": membro}
    )


# --- Reuniões (RF-017) ------------------------------------------------------


@router.post("/orgaos/{orgao_id}/reunioes")
def convocar_reuniao(
    request: Request,
    orgao_id: uuid.UUID,
    titulo: str = Form(...),
    data_hora: datetime = Form(...),
    local: str | None = Form(None),
    pauta: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    orgao = db.get(OrgaoGovernanca, orgao_id)
    if orgao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Órgão de governança não encontrado.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=orgao.cpl_id)
    reuniao = Reuniao(
        orgao_id=orgao_id,
        titulo=titulo,
        data_hora=data_hora,
        local=local or None,
        pauta=pauta or None,
        convocada_em=datetime.now(),
    )
    db.add(reuniao)
    db.commit()
    db.refresh(reuniao)
    reuniao = enviar_convocacao_email(db, reuniao)
    return templates.TemplateResponse(
        request, "restrito/governanca/fragments/reuniao_convocada.html", {"reuniao": reuniao}
    )


@router.get("/reunioes/{reuniao_id}")
def detalhe_reuniao(
    request: Request,
    reuniao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    reuniao = db.get(Reuniao, reuniao_id)
    if reuniao is None:
        return RedirectResponse("/painel/governanca", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=reuniao.orgao.cpl_id)
    membros = (
        db.query(MembroOrgao)
        .filter(MembroOrgao.orgao_id == reuniao.orgao_id, MembroOrgao.ativo.is_(True))
        .all()
    )
    presencas = db.query(Presenca).filter(Presenca.reuniao_id == reuniao_id).all()
    deliberacoes = db.query(Deliberacao).filter(Deliberacao.reuniao_id == reuniao_id).all()
    anexos = (
        db.query(Documento)
        .filter(Documento.reuniao_id == reuniao_id)
        .order_by(Documento.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/governanca/reuniao_detail.html",
        {
            "reuniao": reuniao,
            "membros": membros,
            "presencas": presencas,
            "deliberacoes": deliberacoes,
            "anexos": anexos,
            "categorias_documento": list(CategoriaDocumento),
            "confidencialidades_documento": list(ConfidencialidadeDocumento),
            "status_opcoes": list(StatusReuniao),
            "usuario": usuario,
            "pagina_ativa": "governanca",
        },
    )


@router.post("/reunioes/{reuniao_id}/presencas")
def registrar_presenca(
    request: Request,
    reuniao_id: uuid.UUID,
    pessoa_id: uuid.UUID = Form(...),
    presente: str = Form(...),
    justificativa_ausencia: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    reuniao = db.get(Reuniao, reuniao_id)
    if reuniao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reunião não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=reuniao.orgao.cpl_id)
    presenca = Presenca(
        reuniao_id=reuniao_id,
        pessoa_id=pessoa_id,
        presente=(presente == "sim"),
        justificativa_ausencia=justificativa_ausencia or None,
    )
    db.add(presenca)
    db.commit()
    db.refresh(presenca)
    return templates.TemplateResponse(
        request, "restrito/governanca/fragments/presenca_item.html", {"presenca": presenca}
    )


@router.post("/reunioes/{reuniao_id}/ata")
def encerrar_reuniao(
    request: Request,
    reuniao_id: uuid.UUID,
    status_reuniao: StatusReuniao = Form(..., alias="status"),
    ata: str | None = Form(None),
    quorum_atingido: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    reuniao = db.get(Reuniao, reuniao_id)
    if reuniao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reunião não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=reuniao.orgao.cpl_id)
    reuniao.status = status_reuniao
    reuniao.ata = ata or None
    reuniao.quorum_atingido = quorum_atingido == "sim"
    db.commit()
    db.refresh(reuniao)
    return templates.TemplateResponse(
        request,
        "restrito/governanca/fragments/reuniao_status.html",
        {"reuniao": reuniao, "status_opcoes": list(StatusReuniao)},
    )


# --- Deliberações (RF-018) --------------------------------------------------


@router.post("/reunioes/{reuniao_id}/deliberacoes")
def registrar_deliberacao(
    request: Request,
    reuniao_id: uuid.UUID,
    descricao: str = Form(...),
    quorum_necessario_percentual: str | None = Form(None),
    responsavel_id: str | None = Form(None),
    prazo_execucao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    reuniao = db.get(Reuniao, reuniao_id)
    if reuniao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reunião não encontrada.")
    verificar_participacao_orgao(db, usuario, reuniao.orgao_id, reuniao.orgao.cpl_id)
    deliberacao = Deliberacao(
        reuniao_id=reuniao_id,
        descricao=descricao,
        quorum_necessario_percentual=_opt_float(quorum_necessario_percentual),
        responsavel_id=_opt_uuid(responsavel_id),
        prazo_execucao=_opt_date(prazo_execucao),
    )
    db.add(deliberacao)
    db.commit()
    db.refresh(deliberacao)
    return templates.TemplateResponse(
        request, "restrito/governanca/fragments/deliberacao_item.html", {"deliberacao": deliberacao}
    )


@router.get("/deliberacoes/{deliberacao_id}")
def detalhe_deliberacao(
    request: Request,
    deliberacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    deliberacao = db.get(Deliberacao, deliberacao_id)
    if deliberacao is None:
        return RedirectResponse("/painel/governanca", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=deliberacao.reuniao.orgao.cpl_id)
    membros = (
        db.query(MembroOrgao)
        .filter(MembroOrgao.orgao_id == deliberacao.reuniao.orgao_id, MembroOrgao.ativo.is_(True))
        .all()
    )
    votos = db.query(VotoRegistro).filter(VotoRegistro.deliberacao_id == deliberacao_id).all()
    tarefas = db.query(TarefaGovernanca).filter(TarefaGovernanca.deliberacao_id == deliberacao_id).all()
    return templates.TemplateResponse(
        request,
        "restrito/governanca/deliberacao_detail.html",
        {
            "deliberacao": deliberacao,
            "membros": membros,
            "votos": votos,
            "tarefas": tarefas,
            "resultado_opcoes": list(ResultadoDeliberacao),
            "voto_opcoes": list(TipoVoto),
            "status_opcoes": list(StatusTarefa),
            "usuario": usuario,
            "pagina_ativa": "governanca",
        },
    )


@router.post("/deliberacoes/{deliberacao_id}/votos")
def registrar_voto(
    request: Request,
    deliberacao_id: uuid.UUID,
    pessoa_id: uuid.UUID = Form(...),
    voto: TipoVoto = Form(...),
    motivo_impedimento: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    deliberacao = db.get(Deliberacao, deliberacao_id)
    if deliberacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deliberação não encontrada.")
    verificar_participacao_orgao(db, usuario, deliberacao.reuniao.orgao_id, deliberacao.reuniao.orgao.cpl_id)
    registro = VotoRegistro(
        deliberacao_id=deliberacao_id,
        pessoa_id=pessoa_id,
        voto=voto,
        motivo_impedimento=motivo_impedimento or None,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return templates.TemplateResponse(
        request, "restrito/governanca/fragments/voto_item.html", {"voto": registro}
    )


@router.post("/deliberacoes/{deliberacao_id}/resultado")
def concluir_deliberacao(
    request: Request,
    deliberacao_id: uuid.UUID,
    resultado: ResultadoDeliberacao = Form(...),
    evidencia_execucao: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    deliberacao = db.get(Deliberacao, deliberacao_id)
    if deliberacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deliberação não encontrada.")
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=deliberacao.reuniao.orgao.cpl_id)
    deliberacao.resultado = resultado
    deliberacao.evidencia_execucao = evidencia_execucao or None
    db.commit()
    db.refresh(deliberacao)
    return templates.TemplateResponse(
        request,
        "restrito/governanca/fragments/deliberacao_resultado.html",
        {"deliberacao": deliberacao, "resultado_opcoes": list(ResultadoDeliberacao)},
    )


# --- Tarefas / planos de ação (RF-019) --------------------------------------


@router.post("/deliberacoes/{deliberacao_id}/tarefas")
def criar_tarefa(
    request: Request,
    deliberacao_id: uuid.UUID,
    titulo: str = Form(...),
    descricao: str | None = Form(None),
    responsavel_id: str | None = Form(None),
    prazo: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    deliberacao = db.get(Deliberacao, deliberacao_id)
    if deliberacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deliberação não encontrada.")
    verificar_participacao_orgao(db, usuario, deliberacao.reuniao.orgao_id, deliberacao.reuniao.orgao.cpl_id)
    tarefa = TarefaGovernanca(
        cpl_id=deliberacao.reuniao.orgao.cpl_id,
        deliberacao_id=deliberacao_id,
        titulo=titulo,
        descricao=descricao or None,
        responsavel_id=_opt_uuid(responsavel_id),
        prazo=_opt_date(prazo),
    )
    db.add(tarefa)
    db.commit()
    db.refresh(tarefa)
    return templates.TemplateResponse(
        request,
        "restrito/governanca/fragments/tarefa_item.html",
        {"tarefa": tarefa, "status_opcoes": list(StatusTarefa)},
    )


@router.get("/cpls/{cpl_id}/tarefas")
def listar_tarefas(
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
    tarefas = db.query(TarefaGovernanca).filter(TarefaGovernanca.cpl_id == cpl_id).all()
    return templates.TemplateResponse(
        request,
        "restrito/governanca/tarefas.html",
        {
            "cpl": cpl,
            "tarefas": tarefas,
            "status_opcoes": list(StatusTarefa),
            "usuario": usuario,
            "pagina_ativa": "governanca",
        },
    )


@router.patch("/tarefas/{tarefa_id}/status")
def atualizar_status_tarefa(
    request: Request,
    tarefa_id: uuid.UUID,
    status_tarefa: StatusTarefa = Form(..., alias="status"),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    tarefa = db.get(TarefaGovernanca, tarefa_id)
    if tarefa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarefa não encontrada.")
    e_responsavel = usuario.pessoa_id is not None and usuario.pessoa_id == tarefa.responsavel_id
    if not e_responsavel:
        verificar_papel(db, usuario, PAPEIS_TAREFA_EXECUCAO, cpl_id=tarefa.cpl_id)
    tarefa.status = status_tarefa
    db.commit()
    db.refresh(tarefa)
    return templates.TemplateResponse(
        request,
        "restrito/governanca/fragments/tarefa_item.html",
        {"tarefa": tarefa, "status_opcoes": list(StatusTarefa)},
    )
