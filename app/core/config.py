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


@lru_cache
def get_settings() -> Settings:
    return Settings()
