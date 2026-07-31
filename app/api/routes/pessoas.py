import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_GESTAO, PAPEIS_GOVERNANCA_LEITURA, cpl_ids_visiveis, verificar_papel
from app.db.session import get_db
from app.models.entidade import EntidadeCPL
from app.models.governanca import MembroOrgao, OrgaoGovernanca
from app.models.pessoa import Pessoa, PessoaVinculo
from app.models.usuario import Usuario
from app.schemas.pessoa import PessoaCreate, PessoaRead

router = APIRouter(prefix="/pessoas", tags=["Cadastro e cadeia"])


def _cpl_ids_da_pessoa(db: Session, pessoa_id: uuid.UUID) -> set[uuid.UUID]:
    """Uma pessoa "pertence" a uma CPL por três caminhos possíveis — vínculo
    direto (`PessoaVinculo.cpl_id`), vínculo via entidade
    (`PessoaVinculo.entidade_id` → `EntidadeCPL`) ou participação em
    governança (`MembroOrgao` → `OrgaoGovernanca.cpl_id`). Qualquer um conta."""

    ids: set[uuid.UUID] = set()
    ids.update(
        row[0]
        for row in db.query(PessoaVinculo.cpl_id)
        .filter(PessoaVinculo.pessoa_id == pessoa_id, PessoaVinculo.cpl_id.is_not(None))
        .all()
    )
    ids.update(
        row[0]
        for row in db.query(EntidadeCPL.cpl_id)
        .join(PessoaVinculo, PessoaVinculo.entidade_id == EntidadeCPL.entidade_id)
        .filter(PessoaVinculo.pessoa_id == pessoa_id, EntidadeCPL.ativo.is_(True))
        .all()
    )
    ids.update(
        row[0]
        for row in db.query(OrgaoGovernanca.cpl_id)
        .join(MembroOrgao, MembroOrgao.orgao_id == OrgaoGovernanca.id)
        .filter(MembroOrgao.pessoa_id == pessoa_id, MembroOrgao.ativo.is_(True))
        .all()
    )
    return ids


def _pessoa_ids_visiveis(db: Session, cpl_ids: set[uuid.UUID]) -> set[uuid.UUID]:
    """Mesma ideia de `_cpl_ids_da_pessoa`, mas na direção inversa — usada
    para filtrar a listagem sem N+1 (uma query por caminho, não por pessoa)."""

    ids: set[uuid.UUID] = set()
    ids.update(
        row[0] for row in db.query(PessoaVinculo.pessoa_id).filter(PessoaVinculo.cpl_id.in_(cpl_ids)).all()
    )
    ids.update(
        row[0]
        for row in db.query(PessoaVinculo.pessoa_id)
        .join(EntidadeCPL, EntidadeCPL.entidade_id == PessoaVinculo.entidade_id)
        .filter(EntidadeCPL.cpl_id.in_(cpl_ids), EntidadeCPL.ativo.is_(True))
        .all()
    )
    ids.update(
        row[0]
        for row in db.query(MembroOrgao.pessoa_id)
        .join(OrgaoGovernanca, OrgaoGovernanca.id == MembroOrgao.orgao_id)
        .filter(OrgaoGovernanca.cpl_id.in_(cpl_ids), MembroOrgao.ativo.is_(True))
        .all()
    )
    return ids


@router.post("", response_model=PessoaRead, status_code=status.HTTP_201_CREATED)
def criar_pessoa(
    dados: PessoaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Pessoa:
    """RF-007: cadastra pessoa física — representante, contato ou membro,
    que poderá ser vinculada a entidades, CPLs e órgãos de governança.

    Nota de escopo do RBAC: assim como Entidade, criar uma Pessoa continua
    sem escopo de CPL de propósito — o registro pode não ter nenhum
    vínculo ainda. Leitura (`GET`, abaixo) é que é restrita às CPLs onde a
    pessoa está de fato vinculada (por `PessoaVinculo`, entidade ou
    participação em órgão de governança)."""

    verificar_papel(db, usuario_atual, PAPEIS_GESTAO)

    pessoa = Pessoa(**dados.model_dump())
    db.add(pessoa)
    db.commit()
    db.refresh(pessoa)
    return pessoa


@router.get("", response_model=list[PessoaRead])
def listar_pessoas(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Pessoa]:
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA)
    query = db.query(Pessoa)
    ids_visiveis = cpl_ids_visiveis(db, usuario_atual)
    if ids_visiveis is not None:
        pessoa_ids = _pessoa_ids_visiveis(db, ids_visiveis)
        query = query.filter(Pessoa.id.in_(pessoa_ids))
    return query.order_by(Pessoa.nome).all()


@router.get("/{pessoa_id}", response_model=PessoaRead)
def obter_pessoa(
    pessoa_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Pessoa:
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA)
    pessoa = db.get(Pessoa, pessoa_id)
    if pessoa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pessoa não encontrada.")
    ids_visiveis = cpl_ids_visiveis(db, usuario_atual)
    if ids_visiveis is not None and not (_cpl_ids_da_pessoa(db, pessoa_id) & ids_visiveis):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem acesso a esta pessoa.")
    return pessoa
