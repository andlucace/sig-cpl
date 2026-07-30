import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import existe_administrador, verificar_papel
from app.db.session import get_db
from app.models.enums import Papel
from app.models.usuario import Usuario, UsuarioPapel
from app.schemas.usuario_papel import UsuarioPapelCreate, UsuarioPapelRead

router = APIRouter(prefix="/usuarios", tags=["Identidade e acesso"])


@router.post(
    "/{usuario_id}/papeis", response_model=UsuarioPapelRead, status_code=status.HTTP_201_CREATED
)
def conceder_papel(
    usuario_id: uuid.UUID,
    dados: UsuarioPapelCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> UsuarioPapel:
    """RF-005: concede um papel a um usuário, opcionalmente escopado a uma
    CPL e/ou entidade. Enquanto não existir nenhum ADMINISTRADOR_PLATAFORMA
    no sistema, qualquer usuário autenticado pode se autoconceder esse
    papel — é a única forma de sair do zero sem uma rota de bootstrap
    separada; assim que o primeiro admin existir, essa exceção deixa de
    valer e passa a exigir um admin autenticado para conceder papéis."""

    if existe_administrador(db):
        verificar_papel(db, usuario_atual, {Papel.ADMINISTRADOR_PLATAFORMA})

    alvo = db.get(Usuario, usuario_id)
    if alvo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado.")

    papel = UsuarioPapel(usuario_id=usuario_id, **dados.model_dump())
    db.add(papel)
    db.commit()
    db.refresh(papel)
    return papel


@router.get("/{usuario_id}/papeis", response_model=list[UsuarioPapelRead])
def listar_papeis(
    usuario_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[UsuarioPapel]:
    if usuario_atual.id != usuario_id:
        verificar_papel(db, usuario_atual, {Papel.ADMINISTRADOR_PLATAFORMA})
    return db.query(UsuarioPapel).filter(UsuarioPapel.usuario_id == usuario_id).all()


@router.delete("/papeis/{usuario_papel_id}", status_code=status.HTTP_204_NO_CONTENT)
def revogar_papel(
    usuario_papel_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> None:
    verificar_papel(db, usuario_atual, {Papel.ADMINISTRADOR_PLATAFORMA})
    papel = db.get(UsuarioPapel, usuario_papel_id)
    if papel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vínculo de papel não encontrado.")
    db.delete(papel)
    db.commit()
