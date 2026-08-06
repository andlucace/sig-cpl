"""RNF-012: as três pernas de observabilidade que faltavam além do
`/api/saude` trivial que já existia — rastreamento de falhas, métricas
de requisição e alerta por limiar. Sem infraestrutura externa nova
(sem Prometheus/Grafana/Sentry): falhas ficam persistidas no próprio
Postgres (`RegistroFalha`, mesmo padrão "log que só acumula" de
`RegistroAuditoria`/`Notificacao`); métricas de requisição ficam em
memória do processo (contadores que reiniciam a cada deploy — aceitável
pra "desde o último deploy", não uma série histórica); alerta é
melhor-esforço por e-mail (reaproveita `app/services/email.py`, RF-004),
nunca derruba a requisição que disparou o limiar se o SMTP ainda não
estiver configurado."""

import time
import traceback
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from threading import Lock

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import Papel
from app.models.observabilidade import RegistroFalha
from app.models.usuario import Usuario, UsuarioPapel
from app.services.email import enviar_email

_INICIO = time.monotonic()
_LOCK = Lock()
_CONTAGEM_STATUS: Counter = Counter()
_TOTAL_REQUISICOES = 0
_SOMA_DURACAO_MS = 0.0
_ULTIMO_ALERTA_EM: datetime | None = None


def registrar_requisicao(status_code: int, duracao_ms: float) -> None:
    global _TOTAL_REQUISICOES, _SOMA_DURACAO_MS
    classe = f"{status_code // 100}xx"
    with _LOCK:
        _CONTAGEM_STATUS[classe] += 1
        _TOTAL_REQUISICOES += 1
        _SOMA_DURACAO_MS += duracao_ms


def metricas_requisicoes() -> dict:
    with _LOCK:
        total = _TOTAL_REQUISICOES
        media = (_SOMA_DURACAO_MS / total) if total else 0.0
        return {
            "uptime_segundos": round(time.monotonic() - _INICIO),
            "total_requisicoes": total,
            "por_status": dict(_CONTAGEM_STATUS),
            "latencia_media_ms": round(media, 1),
        }


def verificar_banco(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def registrar_falha(
    db: Session,
    *,
    metodo: str,
    rota: str,
    excecao: BaseException,
    status_code: int = 500,
    usuario_id: uuid.UUID | None = None,
    request_id: str | None = None,
) -> RegistroFalha:
    registro = RegistroFalha(
        metodo=metodo,
        rota=rota,
        tipo_excecao=type(excecao).__name__,
        mensagem=str(excecao)[:2000],
        traceback_resumo="".join(
            traceback.format_exception(type(excecao), excecao, excecao.__traceback__)
        )[-4000:],
        status_code=status_code,
        usuario_id=usuario_id,
        request_id=request_id,
    )
    db.add(registro)
    db.commit()
    return registro


def falhas_recentes(db: Session, minutos: int = 15, limite: int = 50) -> list[RegistroFalha]:
    desde = datetime.now(timezone.utc) - timedelta(minutes=minutos)
    return (
        db.query(RegistroFalha)
        .filter(RegistroFalha.created_at >= desde)
        .order_by(RegistroFalha.created_at.desc())
        .limit(limite)
        .all()
    )


def verificar_e_alertar(db: Session) -> int:
    """Conta falhas na janela configurada e, se cruzar o limiar, tenta
    notificar os administradores — no máximo uma vez por janela, pra não
    disparar um e-mail a cada requisição que continuar falhando em
    seguida. Retorna a contagem, usada pelo painel de saúde pra decidir
    se mostra o banner de alerta (independente do e-mail ter saído ou
    não — o banner não depende de SMTP estar configurado)."""

    global _ULTIMO_ALERTA_EM
    settings = get_settings()
    recentes = falhas_recentes(db, minutos=settings.observabilidade_alerta_janela_minutos, limite=1000)
    contagem = len(recentes)
    if contagem < settings.observabilidade_alerta_limiar_falhas:
        return contagem

    agora = datetime.now(timezone.utc)
    janela = timedelta(minutes=settings.observabilidade_alerta_janela_minutos)
    if _ULTIMO_ALERTA_EM is not None and agora - _ULTIMO_ALERTA_EM < janela:
        return contagem
    _ULTIMO_ALERTA_EM = agora

    admin_ids = {
        v.usuario_id
        for v in db.query(UsuarioPapel).filter(UsuarioPapel.papel == Papel.ADMINISTRADOR_PLATAFORMA).all()
    }
    admins = db.query(Usuario).filter(Usuario.id.in_(admin_ids)).all() if admin_ids else []
    assunto = f"[SIG-CPL] Alerta: {contagem} falhas nos últimos {settings.observabilidade_alerta_janela_minutos} min"
    corpo = (
        f"O sistema registrou {contagem} falhas não tratadas nos últimos "
        f"{settings.observabilidade_alerta_janela_minutos} minutos (limiar: "
        f"{settings.observabilidade_alerta_limiar_falhas}). Verifique o painel de saúde em "
        f"{settings.app_base_url}/painel/administracao/saude."
    )
    for admin in admins:
        try:
            enviar_email(admin.email, assunto, corpo)
        except Exception:
            pass  # melhor esforço — SMTP pode não estar configurado ainda (ver RF-004)

    return contagem
