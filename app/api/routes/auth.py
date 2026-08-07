from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.enums import AcaoAuditoria
from app.models.usuario import Usuario
from app.schemas.usuario import (
    EsqueciSenhaCreate,
    MensagemRead,
    MFAConfirmarCreate,
    MFAConfirmarRead,
    MFADesativarCreate,
    MFAIniciarRead,
    RedefinirSenhaCreate,
    Token,
    UsuarioCreate,
    UsuarioRead,
)
from app.services.auditoria import registrar_evento
from app.services.mfa import (
    confirmar_ativacao_mfa,
    desativar_mfa,
    iniciar_ativacao_mfa,
    verificar_codigo_backup,
    verificar_codigo_totp,
)
from app.services.recuperacao_senha import redefinir_senha, solicitar_recuperacao_senha

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
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    mfa_code: str | None = Form(None),
    db: Session = Depends(get_db),
) -> Token:
    """RF-004: autenticação por e-mail (enviado no campo username) e senha.

    Login por API é um passo só — se o usuário tem MFA ativado, o código
    TOTP (ou um código de backup) precisa vir junto no campo `mfa_code`
    do mesmo request, diferente do login web (dois passos, ver
    `app/web/routes_restrito.py`) porque um cliente de API já é capaz de
    gerar o código na hora, sem precisar de uma tela intermediária."""

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
    if usuario.mfa_enabled:
        codigo_ok = verificar_codigo_totp(usuario, mfa_code or "") or verificar_codigo_backup(
            db, usuario, mfa_code or ""
        )
        if not codigo_ok:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Código MFA ausente ou inválido.")

    access_token = create_access_token(subject=str(usuario.id))
    registrar_evento(
        db, usuario_id=usuario.id, acao=AcaoAuditoria.LOGIN_SUCESSO, entidade_tipo="Usuario", entidade_id=usuario.id
    )
    db.commit()
    return Token(access_token=access_token)


@router.get("/me", response_model=UsuarioRead)
def me(usuario_atual: Usuario = Depends(get_current_user)) -> Usuario:
    return usuario_atual


# --- Recuperação de senha (RF-004) -------------------------------------------


@router.post("/esqueci-senha", response_model=MensagemRead)
def esqueci_senha(dados: EsqueciSenhaCreate, db: Session = Depends(get_db)) -> dict:
    """Sempre responde a mesma mensagem genérica, exista o e-mail ou não
    — não revela se uma conta existe (proteção contra enumeração)."""

    solicitar_recuperacao_senha(db, dados.email)
    return {"mensagem": "Se o e-mail existir, um link de redefinição foi enviado."}


@router.post("/redefinir-senha", response_model=MensagemRead)
def redefinir_senha_rota(dados: RedefinirSenhaCreate, db: Session = Depends(get_db)) -> dict:
    if not redefinir_senha(db, dados.token, dados.nova_senha):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link inválido, expirado ou já utilizado.")
    return {"mensagem": "Senha redefinida com sucesso."}


# --- MFA (RF-004) -------------------------------------------------------------


@router.post("/mfa/iniciar-ativacao", response_model=MFAIniciarRead)
def mfa_iniciar_ativacao(
    db: Session = Depends(get_db), usuario_atual: Usuario = Depends(get_current_user)
) -> dict:
    """Gera um novo segredo TOTP (substitui um anterior não confirmado,
    se houver) — só passa a valer no login depois de
    `POST /mfa/confirmar-ativacao` com um código válido."""

    segredo, qr_base64 = iniciar_ativacao_mfa(db, usuario_atual)
    return {"segredo": segredo, "qr_code_base64": qr_base64}


@router.post("/mfa/confirmar-ativacao", response_model=MFAConfirmarRead)
def mfa_confirmar_ativacao(
    dados: MFAConfirmarCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> dict:
    codigos = confirmar_ativacao_mfa(db, usuario_atual, dados.codigo)
    if codigos is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Código inválido.")
    return {"codigos_backup": codigos}


@router.post("/mfa/desativar", response_model=MensagemRead)
def mfa_desativar(
    dados: MFADesativarCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> dict:
    if not verify_password(dados.password, usuario_atual.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Senha incorreta.")
    desativar_mfa(db, usuario_atual)
    return {"mensagem": "MFA desativado."}
