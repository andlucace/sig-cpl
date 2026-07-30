from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.enums import AcaoAuditoria
from app.models.usuario import Usuario
from app.schemas.usuario import Token, UsuarioCreate, UsuarioRead
from app.services.auditoria import registrar_evento

router = APIRouter(prefix="/auth", tags=["Identidade e acesso"])


@router.post("/registrar", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def registrar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)) -> Usuario:
    """RF-004: cria uma conta de acesso. Em produção este endpoint deve ser
    restrito a administradores/entidade gestora — aberto aqui apenas para
    viabilizar o bootstrap do ambiente de desenvolvimento."""

    if db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "E-mail já cadastrado.")

    usuario = Usuario(email=dados.email, hashed_password=hash_password(dados.password))
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    """RF-004: autenticação por e-mail (enviado no campo username) e senha."""

    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    if not usuario or not verify_password(form_data.password, usuario.hashed_password):
        registrar_evento(
            db,
            usuario_id=None,
            acao=AcaoAuditoria.LOGIN_FALHA,
            entidade_tipo="Usuario",
            descricao=f"Tentativa de login falhou para e-mail {form_data.username!r}.",
        )
        db.commit()
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not usuario.ativo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário inativo.")

    access_token = create_access_token(subject=str(usuario.id))
    registrar_evento(
        db, usuario_id=usuario.id, acao=AcaoAuditoria.LOGIN_SUCESSO, entidade_tipo="Usuario", entidade_id=usuario.id
    )
    db.commit()
    return Token(access_token=access_token)


@router.get("/me", response_model=UsuarioRead)
def me(usuario_atual: Usuario = Depends(get_current_user)) -> Usuario:
    return usuario_atual
