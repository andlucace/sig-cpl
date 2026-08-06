"""RF-004: MFA por TOTP (RFC 6238) — "opção de MFA para perfis críticos"
é implementado como um recurso que qualquer usuário pode ativar (não uma
obrigação amarrada a um papel específico; o requisito não define uma
lista fechada de "perfis críticos" nem pede bloqueio de quem não ativa),
mas o card de configuração recomenda explicitamente a ativação para
administrador da plataforma/entidade gestora/dirigente.

Fluxo em dois passos, mesmo raciocínio do remapeamento de importação
(RF-013) — nunca ativar direto: `iniciar_ativacao_mfa` gera e já salva o
segredo (`usuario.mfa_secret`), mas só `confirmar_ativacao_mfa` (com um
código válido gerado a partir dele) liga `mfa_enabled`. Isso prova que o
usuário realmente cadastrou o segredo certo no autenticador antes do
login passar a exigi-lo — sem essa etapa, um segredo mal escaneado
trancaria o próprio usuário pra fora da conta."""

import base64
import io
import secrets

import pyotp
import qrcode
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.usuario import Usuario

_QUANTIDADE_CODIGOS_BACKUP = 8


def _gerar_qr_base64(uri: str) -> str:
    imagem = qrcode.make(uri)
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def iniciar_ativacao_mfa(db: Session, usuario: Usuario) -> tuple[str, str]:
    """Retorna (segredo em base32, pra digitação manual; QR code em PNG
    base64, pra escaneamento). `mfa_enabled` continua False até a
    confirmação."""

    segredo = pyotp.random_base32()
    usuario.mfa_secret = segredo
    db.commit()

    uri = pyotp.totp.TOTP(segredo).provisioning_uri(name=usuario.email, issuer_name="SIG-CPL")
    return segredo, _gerar_qr_base64(uri)


def verificar_codigo_totp(usuario: Usuario, codigo: str) -> bool:
    if not usuario.mfa_secret or not codigo:
        return False
    return pyotp.totp.TOTP(usuario.mfa_secret).verify(codigo, valid_window=1)


def confirmar_ativacao_mfa(db: Session, usuario: Usuario, codigo: str) -> list[str] | None:
    """Retorna os códigos de backup em texto puro (só existem neste
    retorno — o banco guarda só o hash de cada um, mesmo padrão de
    `hashed_password`) ou None se o código não bateu."""

    if not verificar_codigo_totp(usuario, codigo):
        return None

    codigos = [secrets.token_hex(4) for _ in range(_QUANTIDADE_CODIGOS_BACKUP)]
    usuario.mfa_enabled = True
    usuario.mfa_backup_codes = [hash_password(c) for c in codigos]
    db.commit()
    return codigos


def verificar_codigo_backup(db: Session, usuario: Usuario, codigo: str) -> bool:
    """Cada código de backup só funciona uma vez — consumido (removido
    da lista) assim que usado com sucesso."""

    if not usuario.mfa_backup_codes or not codigo:
        return False
    for hash_armazenado in usuario.mfa_backup_codes:
        if verify_password(codigo, hash_armazenado):
            usuario.mfa_backup_codes = [h for h in usuario.mfa_backup_codes if h != hash_armazenado]
            db.commit()
            return True
    return False


def desativar_mfa(db: Session, usuario: Usuario) -> None:
    usuario.mfa_enabled = False
    usuario.mfa_secret = None
    usuario.mfa_backup_codes = None
    db.commit()
