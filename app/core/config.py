from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SIG-CPL"
    environment: str = "development"
    debug: bool = True

    database_url: str = "postgresql+psycopg://sigcpl:sigcpl@localhost:5432/sigcpl"

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    session_cookie_secure: bool = False

    uploads_dir: str = "uploads"
    """RF-042: pasta onde os arquivos do repositório de documentos ficam.
    Caminho relativo ao diretório de trabalho em dev; em produção, deve
    apontar para um volume persistente (ex.: volume Docker numa VPS) —
    o código não muda, só o que está montado nesse caminho."""

    app_base_url: str = "http://127.0.0.1:8000"
    """RF-004: base pra montar links absolutos em e-mail (o link de
    redefinição de senha precisa funcionar fora do navegador — dentro do
    app, links relativos bastam, mas num e-mail não há "app" pra
    resolvê-los). Em produção, `https://sigcpl.dedev.cloud`."""

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "SIG-CPL <no-reply@sigcpl.local>"
    smtp_use_tls: bool = True
    """RF-004: SMTP genérico — qualquer provedor que fale SMTP padrão
    funciona (Gmail com senha de app, SES, Mailgun, etc.), sem acoplar o
    código a um provedor específico. `smtp_host` ausente é o sinal de
    "e-mail não configurado ainda" (ver `app/services/email.py`)."""

    password_reset_token_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
