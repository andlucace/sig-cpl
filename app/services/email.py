"""RF-004: envio de e-mail via SMTP genérico — usado pela recuperação de
senha. Configuração inteira via variáveis de ambiente (`SMTP_*` em
`app/core/config.py`), sem nenhum provedor específico embutido no
código: qualquer serviço que fale SMTP padrão funciona (Gmail com senha
de app, Amazon SES, Mailgun, um SMTP do próprio domínio etc.).

`smtp_host` ausente é o sinal de "e-mail não configurado ainda" — nesse
caso `enviar_email` levanta `RuntimeError` em vez de falhar silenciosamente,
pra deixar claro em desenvolvimento que a configuração falta, sem
derrubar o fluxo de quem chama (`solicitar_recuperacao_senha` decide o
que fazer com esse erro)."""

import smtplib
from email.mime.text import MIMEText

from app.core.config import get_settings


def enviar_email(destinatario: str, assunto: str, corpo_texto: str) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        raise RuntimeError(
            "SMTP não configurado (SMTP_HOST ausente) — defina as variáveis SMTP_* para enviar e-mail."
        )

    mensagem = MIMEText(corpo_texto, "plain", "utf-8")
    mensagem["Subject"] = assunto
    mensagem["From"] = settings.smtp_from
    mensagem["To"] = destinatario

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as servidor:
        if settings.smtp_use_tls:
            servidor.starttls()
        if settings.smtp_user and settings.smtp_password:
            servidor.login(settings.smtp_user, settings.smtp_password)
        servidor.send_message(mensagem)
