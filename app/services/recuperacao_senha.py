"""RF-004: recuperação de senha por e-mail — token de uso único e curta
validade. `solicitar_recuperacao_senha` é deliberadamente silenciosa
sobre a existência do e-mail (não revela se uma conta existe ou não —
proteção padrão contra enumeração de contas), então a rota que a chama
sempre responde com a mesma mensagem genérica, exista o e-mail ou não."""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.usuario import TokenRecuperacaoSenha, Usuario
from app.services.email import enviar_email


def solicitar_recuperacao_senha(db: Session, email: str) -> None:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None or not usuario.ativo:
        return

    settings = get_settings()
    token = secrets.token_urlsafe(32)
    expira_em = datetime.now(UTC) + timedelta(
        minutes=settings.password_reset_token_expire_minutes
    )
    db.add(TokenRecuperacaoSenha(usuario_id=usuario.id, token=token, expira_em=expira_em))
    db.commit()

    link = f"{settings.app_base_url}/redefinir-senha/{token}"
    enviar_email(
        usuario.email,
        "Redefinição de senha — SIG-CPL",
        "Foi solicitada a redefinição da sua senha no SIG-CPL.\n\n"
        f"Abra o link abaixo para definir uma nova senha (válido por "
        f"{settings.password_reset_token_expire_minutes} minutos, uso único):\n{link}\n\n"
        "Se você não pediu isso, ignore este e-mail — sua senha continua a mesma.",
    )


def redefinir_senha(db: Session, token: str, nova_senha: str) -> bool:
    """Retorna False (sem detalhar o motivo — token inválido, expirado ou
    já usado tratados igual) se a redefinição não pôde ser feita."""

    registro = db.query(TokenRecuperacaoSenha).filter(TokenRecuperacaoSenha.token == token).first()
    agora = datetime.now(UTC)
    if registro is None or registro.usado_em is not None or registro.expira_em < agora:
        return False

    registro.usuario.hashed_password = hash_password(nova_senha)
    registro.usado_em = agora
    db.commit()
    return True
