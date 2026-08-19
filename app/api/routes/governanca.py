import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import (
    PAPEIS_GESTAO,
    PAPEIS_GOVERNANCA_LEITURA,
    PAPEIS_GOVERNANCA_PARTICIPACAO,
    PAPEIS_IMPEDIMENTO_LEITURA,
    PAPEIS_TAREFA_EXECUCAO,
    verificar_papel,
    verificar_participacao_orgao,
)
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.documento import Documento
from app.models.enums import CategoriaDocumento, ConfidencialidadeDocumento
from app.models.governanca import (
    DeclaracaoImpedimento,
    Deliberacao,
    MembroOrgao,
    OrgaoGovernanca,
    Presenca,
    Reuniao,
    TarefaGovernanca,
    VotoRegistro,
)
from app.models.usuario import Usuario
from app.schemas.documento import DocumentoRead
from app.schemas.governanca import (
    DeclaracaoImpedimentoCreate,
    DeclaracaoImpedimentoRead,
    DeliberacaoCreate,
    DeliberacaoRead,
    DeliberacaoResultadoUpdate,
    MembroOrgaoCreate,
    MembroOrgaoRead,
    MembroOrgaoRemocaoCreate,
    OrgaoGovernancaCreate,
    OrgaoGovernancaRead,
    PresencaCreate,
    PresencaRead,
    ReuniaoAtaUpdate,
    ReuniaoCreate,
    ReuniaoRead,
    TarefaGovernancaCreate,
    TarefaGovernancaRead,
    TarefaStatusUpdate,
    VotoCreate,
    VotoRead,
)
from app.services.armazenamento import salvar_arquivo
from app.services.geracao_documentos import gerar_pdf_relatorio_comissao
from app.services.governanca import enviar_convocacao_email
from app.services.indicadores import resumo_orgao

router = APIRouter(prefix="/governanca", tags=["Governança"])


def _get_cpl_or_404(db: Session, cpl_id: uuid.UUID) -> CPL:
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    return cpl


def _get_orgao_or_404(db: Session, orgao_id: uuid.UUID) -> OrgaoGovernanca:
    orgao = db.get(OrgaoGovernanca, orgao_id)
    if orgao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Órgão de governança não encontrado.")
    return orgao


def _get_reuniao_or_404(db: Session, reuniao_id: uuid.UUID) -> Reuniao:
    reuniao = db.get(Reuniao, reuniao_id)
    if reuniao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reunião não encontrada.")
    return reuniao


def _get_deliberacao_or_404(db: Session, deliberacao_id: uuid.UUID) -> Deliberacao:
    deliberacao = db.get(Deliberacao, deliberacao_id)
    if deliberacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deliberação não encontrada.")
    return deliberacao


# --- Órgãos (RF-015/RF-016) ---------------------------------------------


@router.post(
    "/cpls/{cpl_id}/orgaos", response_model=OrgaoGovernancaRead, status_code=status.HTTP_201_CREATED
)
def criar_orgao(
    cpl_id: uuid.UUID,
    dados: OrgaoGovernancaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> OrgaoGovernanca:
    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)
    orgao = OrgaoGovernanca(cpl_id=cpl_id, **dados.model_dump())
    db.add(orgao)
    db.commit()
    db.refresh(orgao)
    return orgao


@router.get("/cpls/{cpl_id}/orgaos", response_model=list[OrgaoGovernancaRead])
def listar_orgaos(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[OrgaoGovernanca]:
    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return db.query(OrgaoGovernanca).filter(OrgaoGovernanca.cpl_id == cpl_id).order_by(OrgaoGovernanca.nome).all()


@router.get("/orgaos/{orgao_id}", response_model=OrgaoGovernancaRead)
def obter_orgao(
    orgao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> OrgaoGovernanca:
    orgao = _get_orgao_or_404(db, orgao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=orgao.cpl_id)
    return orgao


# --- Membros / mandatos (RF-016) ----------------------------------------


@router.post(
    "/orgaos/{orgao_id}/membros", response_model=MembroOrgaoRead, status_code=status.HTTP_201_CREATED
)
def adicionar_membro(
    orgao_id: uuid.UUID,
    dados: MembroOrgaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> MembroOrgao:
    orgao = _get_orgao_or_404(db, orgao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=orgao.cpl_id)
    membro = MembroOrgao(orgao_id=orgao_id, **dados.model_dump())
    db.add(membro)
    db.commit()
    db.refresh(membro)
    return membro


@router.get("/orgaos/{orgao_id}/membros", response_model=list[MembroOrgaoRead])
def listar_membros(
    orgao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[MembroOrgao]:
    orgao = _get_orgao_or_404(db, orgao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=orgao.cpl_id)
    return db.query(MembroOrgao).filter(MembroOrgao.orgao_id == orgao_id).all()


@router.post("/membros/{membro_id}/remover", response_model=MembroOrgaoRead)
def remover_membro(
    membro_id: uuid.UUID,
    dados: MembroOrgaoRemocaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> MembroOrgao:
    """Exclusão de membro exige motivo — desativa (`ativo=False`) em vez
    de excluir a linha, preservando o histórico de mandato; a alteração
    (incluindo o motivo) já cai na trilha de auditoria automática."""

    membro = db.get(MembroOrgao, membro_id)
    if membro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Membro não encontrado.")
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=membro.orgao.cpl_id)
    membro.ativo = False
    membro.motivo_remocao = dados.motivo
    if membro.data_fim is None:
        membro.data_fim = date.today()
    db.commit()
    db.refresh(membro)
    return membro


# --- Reuniões (RF-017) ---------------------------------------------------


@router.post(
    "/orgaos/{orgao_id}/reunioes", response_model=ReuniaoRead, status_code=status.HTTP_201_CREATED
)
def convocar_reuniao(
    orgao_id: uuid.UUID,
    dados: ReuniaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Reuniao:
    orgao = _get_orgao_or_404(db, orgao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=orgao.cpl_id)
    reuniao = Reuniao(orgao_id=orgao_id, **dados.model_dump())
    db.add(reuniao)
    db.commit()
    db.refresh(reuniao)
    return enviar_convocacao_email(db, reuniao)


@router.get("/orgaos/{orgao_id}/reunioes", response_model=list[ReuniaoRead])
def listar_reunioes(
    orgao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Reuniao]:
    orgao = _get_orgao_or_404(db, orgao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=orgao.cpl_id)
    return db.query(Reuniao).filter(Reuniao.orgao_id == orgao_id).order_by(Reuniao.data_hora.desc()).all()


@router.get("/reunioes/{reuniao_id}", response_model=ReuniaoRead)
def obter_reuniao(
    reuniao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Reuniao:
    reuniao = _get_reuniao_or_404(db, reuniao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=reuniao.orgao.cpl_id)
    return reuniao


@router.patch("/reunioes/{reuniao_id}", response_model=ReuniaoRead)
def registrar_ata(
    reuniao_id: uuid.UUID,
    dados: ReuniaoAtaUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Reuniao:
    """RF-017: encerra a reunião com status final, ata e indicação de
    quórum atingido, após o registro de presenças e deliberações."""

    reuniao = _get_reuniao_or_404(db, reuniao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=reuniao.orgao.cpl_id)
    for campo, valor in dados.model_dump().items():
        setattr(reuniao, campo, valor)
    db.commit()
    db.refresh(reuniao)
    return reuniao


# --- Presença (RF-017) ----------------------------------------------------


@router.post(
    "/reunioes/{reuniao_id}/presencas", response_model=PresencaRead, status_code=status.HTTP_201_CREATED
)
def registrar_presenca(
    reuniao_id: uuid.UUID,
    dados: PresencaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Presenca:
    reuniao = _get_reuniao_or_404(db, reuniao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=reuniao.orgao.cpl_id)
    if db.query(Presenca).filter(
        Presenca.reuniao_id == reuniao_id, Presenca.pessoa_id == dados.pessoa_id
    ).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Presença já registrada para esta pessoa.")
    presenca = Presenca(reuniao_id=reuniao_id, **dados.model_dump())
    db.add(presenca)
    db.commit()
    db.refresh(presenca)
    return presenca


@router.get("/reunioes/{reuniao_id}/presencas", response_model=list[PresencaRead])
def listar_presencas(
    reuniao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Presenca]:
    reuniao = _get_reuniao_or_404(db, reuniao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=reuniao.orgao.cpl_id)
    return db.query(Presenca).filter(Presenca.reuniao_id == reuniao_id).all()


# --- Deliberações (RF-018) -------------------------------------------------


@router.post(
    "/reunioes/{reuniao_id}/deliberacoes",
    response_model=DeliberacaoRead,
    status_code=status.HTTP_201_CREATED,
)
def registrar_deliberacao(
    reuniao_id: uuid.UUID,
    dados: DeliberacaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Deliberacao:
    reuniao = _get_reuniao_or_404(db, reuniao_id)
    verificar_participacao_orgao(db, usuario_atual, reuniao.orgao_id, reuniao.orgao.cpl_id)
    deliberacao = Deliberacao(reuniao_id=reuniao_id, **dados.model_dump())
    db.add(deliberacao)
    db.commit()
    db.refresh(deliberacao)
    return deliberacao


@router.get("/reunioes/{reuniao_id}/deliberacoes", response_model=list[DeliberacaoRead])
def listar_deliberacoes(
    reuniao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Deliberacao]:
    reuniao = _get_reuniao_or_404(db, reuniao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=reuniao.orgao.cpl_id)
    return db.query(Deliberacao).filter(Deliberacao.reuniao_id == reuniao_id).all()


@router.patch("/deliberacoes/{deliberacao_id}", response_model=DeliberacaoRead)
def concluir_deliberacao(
    deliberacao_id: uuid.UUID,
    dados: DeliberacaoResultadoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Deliberacao:
    """RN-007: toda alteração de resultado fica registrada (created_at/
    updated_at) — nenhuma pontuação/decisão é alterada sem rastro.

    Concluir (aprovar/rejeitar) fica com quem pode aprovar/assinar
    (entidade gestora/dirigente/admin) — não com quem só vota."""

    deliberacao = _get_deliberacao_or_404(db, deliberacao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=deliberacao.reuniao.orgao.cpl_id)
    for campo, valor in dados.model_dump().items():
        setattr(deliberacao, campo, valor)
    db.commit()
    db.refresh(deliberacao)
    return deliberacao


# --- Votos (RF-018/RF-020) -------------------------------------------------


@router.post(
    "/deliberacoes/{deliberacao_id}/votos", response_model=VotoRead, status_code=status.HTTP_201_CREATED
)
def registrar_voto(
    deliberacao_id: uuid.UUID,
    dados: VotoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> VotoRegistro:
    deliberacao = _get_deliberacao_or_404(db, deliberacao_id)
    verificar_participacao_orgao(
        db, usuario_atual, deliberacao.reuniao.orgao_id, deliberacao.reuniao.orgao.cpl_id
    )
    if db.query(VotoRegistro).filter(
        VotoRegistro.deliberacao_id == deliberacao_id, VotoRegistro.pessoa_id == dados.pessoa_id
    ).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Voto já registrado para esta pessoa.")
    voto = VotoRegistro(deliberacao_id=deliberacao_id, **dados.model_dump())
    db.add(voto)
    db.commit()
    db.refresh(voto)
    return voto


@router.get("/deliberacoes/{deliberacao_id}/votos", response_model=list[VotoRead])
def listar_votos(
    deliberacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[VotoRegistro]:
    deliberacao = _get_deliberacao_or_404(db, deliberacao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=deliberacao.reuniao.orgao.cpl_id)
    return db.query(VotoRegistro).filter(VotoRegistro.deliberacao_id == deliberacao_id).all()


# --- Tarefas / planos de ação (RF-019) -------------------------------------


@router.post(
    "/deliberacoes/{deliberacao_id}/tarefas",
    response_model=TarefaGovernancaRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_tarefa_de_deliberacao(
    deliberacao_id: uuid.UUID,
    dados: TarefaGovernancaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> TarefaGovernanca:
    deliberacao = _get_deliberacao_or_404(db, deliberacao_id)
    cpl_id = deliberacao.reuniao.orgao.cpl_id
    verificar_participacao_orgao(db, usuario_atual, deliberacao.reuniao.orgao_id, cpl_id)
    tarefa = TarefaGovernanca(cpl_id=cpl_id, deliberacao_id=deliberacao_id, **dados.model_dump())
    db.add(tarefa)
    db.commit()
    db.refresh(tarefa)
    return tarefa


@router.get("/cpls/{cpl_id}/tarefas", response_model=list[TarefaGovernancaRead])
def listar_tarefas(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[TarefaGovernanca]:
    """RF-019: lista tarefas/planos de ação da CPL para acompanhamento de
    status — base para alertas de prazo (RF-049)."""

    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return db.query(TarefaGovernanca).filter(TarefaGovernanca.cpl_id == cpl_id).all()


@router.patch("/tarefas/{tarefa_id}", response_model=TarefaGovernancaRead)
def atualizar_status_tarefa(
    tarefa_id: uuid.UUID,
    dados: TarefaStatusUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> TarefaGovernanca:
    tarefa = db.get(TarefaGovernanca, tarefa_id)
    if tarefa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarefa não encontrada.")
    e_responsavel = usuario_atual.pessoa_id is not None and usuario_atual.pessoa_id == tarefa.responsavel_id
    if not e_responsavel:
        verificar_papel(db, usuario_atual, PAPEIS_TAREFA_EXECUCAO, cpl_id=tarefa.cpl_id)
    tarefa.status = dados.status
    db.commit()
    db.refresh(tarefa)
    return tarefa


# --- Declaração de impedimento (RF-020) ------------------------------------


@router.post(
    "/cpls/{cpl_id}/impedimentos",
    response_model=DeclaracaoImpedimentoRead,
    status_code=status.HTTP_201_CREATED,
)
def declarar_impedimento(
    cpl_id: uuid.UUID,
    dados: DeclaracaoImpedimentoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> DeclaracaoImpedimento:
    """RF-020: a declaração é opcionalmente ligada a um órgão/reunião
    (`orgao_id`/`reuniao_id` no corpo), mas não obrigatoriamente — por isso
    fica escopada só por CPL (`verificar_papel`), não por órgão específico
    como `verificar_participacao_orgao` faz para votos/deliberações."""

    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_PARTICIPACAO, cpl_id=cpl_id)
    declaracao = DeclaracaoImpedimento(cpl_id=cpl_id, **dados.model_dump())
    db.add(declaracao)
    db.commit()
    db.refresh(declaracao)
    return declaracao


@router.get("/cpls/{cpl_id}/impedimentos", response_model=list[DeclaracaoImpedimentoRead])
def listar_impedimentos(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[DeclaracaoImpedimento]:
    """RN-014: declarações de impedimento são dado sensível — leitura restrita
    (gestão + auditoria), diferente do resto da governança."""

    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_IMPEDIMENTO_LEITURA, cpl_id=cpl_id)
    return db.query(DeclaracaoImpedimento).filter(DeclaracaoImpedimento.cpl_id == cpl_id).all()


# --- Relatório de comissão (RF-048) -----------------------------------------


@router.post(
    "/orgaos/{orgao_id}/relatorio-comissao", response_model=DocumentoRead, status_code=status.HTTP_201_CREATED
)
def gerar_relatorio_comissao(
    orgao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Documento:
    """RF-048: relatório de comissão em PDF — escopado a um único órgão de
    governança, salvo no repositório de documentos igual ao padrão dos
    outros relatórios."""

    orgao = _get_orgao_or_404(db, orgao_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=orgao.cpl_id)

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
        criado_por_id=usuario_atual.id,
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento
