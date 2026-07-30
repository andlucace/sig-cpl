from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import COOKIE_NAME, get_current_user_optional
from app.core.rbac import cpl_ids_visiveis
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.enums import AcaoAuditoria, StatusReuniao, StatusTarefa
from app.models.governanca import MembroOrgao, OrgaoGovernanca, Reuniao, TarefaGovernanca
from app.models.usuario import Usuario
from app.services.auditoria import registrar_evento
from app.web.templates import templates

router = APIRouter(tags=["Área restrita"])
settings = get_settings()


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
    token = create_access_token(subject=str(usuario.id))
    registrar_evento(
        db, usuario_id=usuario.id, acao=AcaoAuditoria.LOGIN_SUCESSO, entidade_tipo="Usuario", entidade_id=usuario.id
    )
    db.commit()
    response = RedirectResponse("/painel", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(COOKIE_NAME)
    return response


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
