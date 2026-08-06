import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import COOKIE_NAME, MFA_PENDING_COOKIE_NAME, get_current_user_optional
from app.core.rbac import cpl_ids_visiveis
from app.core.security import create_access_token, decode_access_token, verify_password
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.enums import AcaoAuditoria, StatusReuniao, StatusTarefa
from app.models.governanca import MembroOrgao, OrgaoGovernanca, Reuniao, TarefaGovernanca
from app.models.usuario import Usuario
from app.services.auditoria import registrar_evento
from app.services.mfa import (
    confirmar_ativacao_mfa,
    desativar_mfa,
    iniciar_ativacao_mfa,
    verificar_codigo_backup,
    verificar_codigo_totp,
)
from app.services.recuperacao_senha import redefinir_senha, solicitar_recuperacao_senha
from app.web.templates import templates

router = APIRouter(tags=["Área restrita"])
settings = get_settings()

_MFA_PENDING_MINUTOS = 5


def _emitir_cookie_sessao(response: RedirectResponse, usuario: Usuario) -> None:
    token = create_access_token(subject=str(usuario.id))
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )


@router.get("/login")
def form_login(request: Request, usuario=Depends(get_current_user_optional)):
    if usuario:
        return RedirectResponse("/painel", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "restrito/login.html", {"erro": None})


@router.post("/login")
def processar_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario or not verify_password(password, usuario.hashed_password) or not usuario.ativo:
        registrar_evento(
            db,
            usuario_id=None,
            acao=AcaoAuditoria.LOGIN_FALHA,
            entidade_tipo="Usuario",
            descricao=f"Tentativa de login falhou para e-mail {email!r}.",
        )
        db.commit()
        return templates.TemplateResponse(
            request,
            "restrito/login.html",
            {"erro": "E-mail ou senha inválidos."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if usuario.mfa_enabled:
        # RF-004: senha confere, mas login em 2 passos — cookie separado
        # (curta validade, claim `mfa_pending`) até o segundo fator ser
        # verificado em `/login/mfa`. Nunca aceito como sessão (ver
        # checagem em `get_current_user`).
        pending_token = create_access_token(
            subject=str(usuario.id),
            expires_delta=timedelta(minutes=_MFA_PENDING_MINUTOS),
            extra_claims={"mfa_pending": True},
        )
        response = RedirectResponse("/login/mfa", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            MFA_PENDING_COOKIE_NAME,
            pending_token,
            httponly=True,
            secure=settings.session_cookie_secure,
            samesite="lax",
            max_age=_MFA_PENDING_MINUTOS * 60,
        )
        return response

    registrar_evento(
        db, usuario_id=usuario.id, acao=AcaoAuditoria.LOGIN_SUCESSO, entidade_tipo="Usuario", entidade_id=usuario.id
    )
    db.commit()
    response = RedirectResponse("/painel", status_code=status.HTTP_303_SEE_OTHER)
    _emitir_cookie_sessao(response, usuario)
    return response


def _usuario_do_cookie_pendente(request: Request, db: Session) -> Usuario | None:
    token = request.cookies.get(MFA_PENDING_COOKIE_NAME)
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except JWTError:
        return None
    sub = payload.get("sub")
    if not payload.get("mfa_pending") or sub is None:
        return None
    return db.get(Usuario, uuid.UUID(sub))


@router.get("/login/mfa")
def form_login_mfa(request: Request, db: Session = Depends(get_db)):
    if _usuario_do_cookie_pendente(request, db) is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "restrito/login_mfa.html", {"erro": None})


@router.post("/login/mfa")
def processar_login_mfa(
    request: Request,
    codigo: str = Form(...),
    db: Session = Depends(get_db),
):
    usuario = _usuario_do_cookie_pendente(request, db)
    if usuario is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    if not (verificar_codigo_totp(usuario, codigo) or verificar_codigo_backup(db, usuario, codigo)):
        return templates.TemplateResponse(
            request,
            "restrito/login_mfa.html",
            {"erro": "Código inválido."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    registrar_evento(
        db, usuario_id=usuario.id, acao=AcaoAuditoria.LOGIN_SUCESSO, entidade_tipo="Usuario", entidade_id=usuario.id
    )
    db.commit()
    response = RedirectResponse("/painel", status_code=status.HTTP_303_SEE_OTHER)
    _emitir_cookie_sessao(response, usuario)
    response.delete_cookie(MFA_PENDING_COOKIE_NAME)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(COOKIE_NAME)
    return response


# --- Recuperação de senha (RF-004) -------------------------------------------


@router.get("/esqueci-senha")
def form_esqueci_senha(request: Request):
    return templates.TemplateResponse(request, "restrito/esqueci_senha.html", {"enviado": False})


@router.post("/esqueci-senha")
def processar_esqueci_senha(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    solicitar_recuperacao_senha(db, email)
    return templates.TemplateResponse(request, "restrito/esqueci_senha.html", {"enviado": True})


@router.get("/redefinir-senha/{token}")
def form_redefinir_senha(request: Request, token: str):
    return templates.TemplateResponse(
        request, "restrito/redefinir_senha.html", {"token": token, "erro": None}
    )


@router.post("/redefinir-senha/{token}")
def processar_redefinir_senha(
    request: Request,
    token: str,
    nova_senha: str = Form(...),
    confirmar_senha: str = Form(...),
    db: Session = Depends(get_db),
):
    if nova_senha != confirmar_senha:
        return templates.TemplateResponse(
            request,
            "restrito/redefinir_senha.html",
            {"token": token, "erro": "As senhas não coincidem."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not redefinir_senha(db, token, nova_senha):
        return templates.TemplateResponse(
            request,
            "restrito/redefinir_senha.html",
            {"token": token, "erro": "Link inválido, expirado ou já utilizado."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse("/login?senha_redefinida=1", status_code=status.HTTP_303_SEE_OTHER)


# --- Perfil / MFA (RF-004) ----------------------------------------------------


@router.get("/painel/perfil")
def perfil(request: Request, usuario=Depends(get_current_user_optional)):
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request,
        "restrito/perfil.html",
        {"usuario": usuario, "pagina_ativa": "perfil", "mfa_setup": None, "codigos_backup": None},
    )


@router.get("/painel/perfil/mfa/configurar")
def perfil_mfa_configurar(
    request: Request, db: Session = Depends(get_db), usuario=Depends(get_current_user_optional)
):
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    segredo, qr_base64 = iniciar_ativacao_mfa(db, usuario)
    return templates.TemplateResponse(
        request,
        "restrito/perfil.html",
        {
            "usuario": usuario,
            "pagina_ativa": "perfil",
            "mfa_setup": {"segredo": segredo, "qr_code_base64": qr_base64},
            "codigos_backup": None,
        },
    )


@router.post("/painel/perfil/mfa/confirmar")
def perfil_mfa_confirmar(
    request: Request,
    codigo: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    codigos = confirmar_ativacao_mfa(db, usuario, codigo)
    if codigos is None:
        return templates.TemplateResponse(
            request,
            "restrito/perfil.html",
            {
                "usuario": usuario,
                "pagina_ativa": "perfil",
                "mfa_setup": {"segredo": usuario.mfa_secret, "erro": "Código inválido."},
                "codigos_backup": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return templates.TemplateResponse(
        request,
        "restrito/perfil.html",
        {"usuario": usuario, "pagina_ativa": "perfil", "mfa_setup": None, "codigos_backup": codigos},
    )


@router.post("/painel/perfil/mfa/desativar")
def perfil_mfa_desativar(
    request: Request,
    password: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    if not verify_password(password, usuario.hashed_password):
        return templates.TemplateResponse(
            request,
            "restrito/perfil.html",
            {
                "usuario": usuario,
                "pagina_ativa": "perfil",
                "mfa_setup": None,
                "codigos_backup": None,
                "erro_desativar": "Senha incorreta.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    desativar_mfa(db, usuario)
    return RedirectResponse("/painel/perfil", status_code=status.HTTP_303_SEE_OTHER)


def _kpis_dashboard(db: Session, usuario: Usuario) -> dict:
    """Indicadores gerenciais básicos do painel (RF-045: painéis de
    governança), escopados às CPLs que o usuário pode enxergar (RBAC)."""

    ids_cpl = cpl_ids_visiveis(db, usuario)

    def escopo(query, coluna):
        return query if ids_cpl is None else query.filter(coluna.in_(ids_cpl))

    cpls = escopo(db.query(CPL), CPL.id).order_by(CPL.nome).all()

    total_orgaos = escopo(
        db.query(OrgaoGovernanca).filter(OrgaoGovernanca.ativo.is_(True)), OrgaoGovernanca.cpl_id
    ).count()

    reunioes_agendadas = escopo(
        db.query(Reuniao)
        .join(OrgaoGovernanca, Reuniao.orgao_id == OrgaoGovernanca.id)
        .filter(Reuniao.status == StatusReuniao.AGENDADA),
        OrgaoGovernanca.cpl_id,
    ).count()

    tarefas_q = escopo(db.query(TarefaGovernanca), TarefaGovernanca.cpl_id)
    tarefas_pendentes = tarefas_q.filter(
        TarefaGovernanca.status.in_([StatusTarefa.PENDENTE, StatusTarefa.EM_ANDAMENTO])
    ).count()
    tarefas_atrasadas = tarefas_q.filter(TarefaGovernanca.status == StatusTarefa.ATRASADA).count()

    membros_ativos = escopo(
        db.query(MembroOrgao)
        .join(OrgaoGovernanca, MembroOrgao.orgao_id == OrgaoGovernanca.id)
        .filter(MembroOrgao.ativo.is_(True)),
        OrgaoGovernanca.cpl_id,
    ).count()

    return {
        "cpls": cpls,
        "total_cpls": len(cpls),
        "total_orgaos": total_orgaos,
        "reunioes_agendadas": reunioes_agendadas,
        "tarefas_pendentes": tarefas_pendentes,
        "tarefas_atrasadas": tarefas_atrasadas,
        "membros_ativos": membros_ativos,
    }


@router.get("/painel")
def painel(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    contexto = {"usuario": usuario, "pagina_ativa": "painel", **_kpis_dashboard(db, usuario)}
    return templates.TemplateResponse(request, "restrito/dashboard.html", contexto)
