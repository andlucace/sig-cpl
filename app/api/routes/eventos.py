import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_EDITAL_GESTAO, PAPEIS_GESTAO, PAPEIS_GOVERNANCA_LEITURA, cpl_ids_visiveis, verificar_papel
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.evento import Evento, InscricaoEvento
from app.models.pessoa import Pessoa
from app.models.usuario import Usuario
from app.schemas.evento import (
    EventoCreate,
    EventoRead,
    EventoUpdate,
    InscricaoEventoAtualizar,
    InscricaoEventoCreate,
    InscricaoEventoRead,
)

router = APIRouter(prefix="/eventos", tags=["Eventos (RF-050)"])


def _get_evento_or_404(db: Session, evento_id: uuid.UUID) -> Evento:
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento não encontrado.")
    return evento


def _verificar_gestao_evento(db: Session, usuario: Usuario, cpl_id: uuid.UUID | None) -> None:
    """RF-050: mesmo raciocínio de `Edital` (RN-006) — evento aberto a
    todas as CPLs (`cpl_id=None`) é gerido pela plataforma
    (`PAPEIS_EDITAL_GESTAO`); evento local de uma CPL é gerido pela
    própria gestão dessa CPL (`PAPEIS_GESTAO`)."""

    if cpl_id is None:
        verificar_papel(db, usuario, PAPEIS_EDITAL_GESTAO, cpl_id=None)
    else:
        verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)


def _evento_visivel(db: Session, usuario: Usuario, evento: Evento) -> bool:
    if evento.cpl_id is None:
        return True
    ids = cpl_ids_visiveis(db, usuario)
    return ids is None or evento.cpl_id in ids


@router.post("", response_model=EventoRead, status_code=status.HTTP_201_CREATED)
def criar_evento(
    dados: EventoCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> Evento:
    if dados.cpl_id is not None and db.get(CPL, dados.cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    _verificar_gestao_evento(db, usuario_atual, dados.cpl_id)

    evento = Evento(**dados.model_dump(), criado_por_id=usuario_atual.id)
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


@router.get("", response_model=list[EventoRead])
def listar_eventos(
    db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> list[Evento]:
    ids = cpl_ids_visiveis(db, usuario_atual)
    query = db.query(Evento).order_by(Evento.data_inicio.desc())
    if ids is None:
        return query.all()
    return [e for e in query.all() if e.cpl_id is None or e.cpl_id in ids]


@router.get("/{evento_id}", response_model=EventoRead)
def obter_evento(
    evento_id: uuid.UUID, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> Evento:
    evento = _get_evento_or_404(db, evento_id)
    if not _evento_visivel(db, usuario_atual, evento):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem acesso a este evento.")
    return evento


@router.patch("/{evento_id}", response_model=EventoRead)
def atualizar_evento(
    evento_id: uuid.UUID,
    dados: EventoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Evento:
    evento = _get_evento_or_404(db, evento_id)
    _verificar_gestao_evento(db, usuario_atual, evento.cpl_id)

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(evento, campo, valor)
    db.commit()
    db.refresh(evento)
    return evento


@router.post(
    "/{evento_id}/inscricoes", response_model=InscricaoEventoRead, status_code=status.HTTP_201_CREATED
)
def inscrever_pessoa(
    evento_id: uuid.UUID,
    dados: InscricaoEventoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> InscricaoEvento:
    """RF-050: inscrição feita pela gestão da CPL (mesmo padrão de
    `MembroOrgao`/`Presenca` em Governança — quem tem papel de gestão
    inscreve pessoas já conhecidas do cadastro, não é autoatendimento;
    mesmo padrão também não exige que a `Pessoa` já tenha vínculo formal
    com a CPL — um evento pode ser justamente a porta de entrada de
    alguém ainda não vinculado). Se o evento é local de uma CPL
    (`evento.cpl_id` preenchido), só essa CPL pode inscrever gente nele."""

    evento = _get_evento_or_404(db, evento_id)
    cpl_id = dados.cpl_id or evento.cpl_id
    if cpl_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Informe a CPL responsável pela inscrição.")
    if evento.cpl_id is not None and cpl_id != evento.cpl_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este evento é restrito à CPL que o criou.")
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)

    pessoa = db.get(Pessoa, dados.pessoa_id)
    if pessoa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pessoa não encontrada.")

    ja_inscrita = (
        db.query(InscricaoEvento)
        .filter(InscricaoEvento.evento_id == evento_id, InscricaoEvento.pessoa_id == pessoa.id)
        .first()
    )
    if ja_inscrita is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta pessoa já está inscrita neste evento.")
    if evento.vagas is not None:
        total_inscritos = (
            db.query(InscricaoEvento).filter(InscricaoEvento.evento_id == evento_id).count()
        )
        if total_inscritos >= evento.vagas:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Não há mais vagas disponíveis neste evento.")

    inscricao = InscricaoEvento(evento_id=evento_id, pessoa_id=pessoa.id, cpl_id=cpl_id)
    db.add(inscricao)
    db.commit()
    db.refresh(inscricao)
    return inscricao


@router.get("/{evento_id}/inscricoes", response_model=list[InscricaoEventoRead])
def listar_inscricoes(
    evento_id: uuid.UUID, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> list[InscricaoEvento]:
    evento = _get_evento_or_404(db, evento_id)
    query = db.query(InscricaoEvento).filter(InscricaoEvento.evento_id == evento_id)
    if evento.cpl_id is not None:
        verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=evento.cpl_id)
        return query.all()

    ids = cpl_ids_visiveis(db, usuario_atual)
    if ids is None:
        return query.all()
    return query.filter(InscricaoEvento.cpl_id.in_(ids)).all()


@router.patch("/inscricoes/{inscricao_id}", response_model=InscricaoEventoRead)
def atualizar_inscricao(
    inscricao_id: uuid.UUID,
    dados: InscricaoEventoAtualizar,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> InscricaoEvento:
    """RF-050: marcar presença e registrar avaliação — mesma autoridade
    de quem inscreveu (gestão da CPL da inscrição)."""

    inscricao = db.get(InscricaoEvento, inscricao_id)
    if inscricao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inscrição não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=inscricao.cpl_id)

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(inscricao, campo, valor)
    db.commit()
    db.refresh(inscricao)
    return inscricao
