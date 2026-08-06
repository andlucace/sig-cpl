"""RF-042: armazenamento em disco dos arquivos do repositório de
documentos. Caminho base configurável via `settings.uploads_dir` — em dev
é uma pasta local (`uploads/`), em produção deve ser um volume persistente
(ex.: volume Docker numa VPS); o código é o mesmo nos dois casos.
"""

import uuid
from pathlib import Path

from app.core.config import get_settings


def _base_dir() -> Path:
    caminho = Path(get_settings().uploads_dir)
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho


def salvar_arquivo(cpl_id: uuid.UUID, nome_original: str, conteudo: bytes) -> str:
    """Salva o conteúdo em disco e devolve o caminho relativo (o que fica
    gravado em `Documento.arquivo_path`) — nunca o nome original puro, para
    evitar colisão e path traversal."""

    extensao = Path(nome_original).suffix
    nome_seguro = f"{uuid.uuid4()}{extensao}"
    subpasta = _base_dir() / str(cpl_id)
    subpasta.mkdir(parents=True, exist_ok=True)
    destino = subpasta / nome_seguro
    destino.write_bytes(conteudo)
    return str(Path(str(cpl_id)) / nome_seguro)


def salvar_arquivo_biblioteca(nome_original: str, conteudo: bytes) -> str:
    """RF-051: mesma lógica de `salvar_arquivo`, mas para conteúdo da
    biblioteca de conhecimento — compartilhado entre todas as CPLs, não
    preso a uma (`RecursoBiblioteca` não tem `cpl_id`), então usa uma
    subpasta fixa em vez de uma por CPL."""

    extensao = Path(nome_original).suffix
    nome_seguro = f"{uuid.uuid4()}{extensao}"
    subpasta = _base_dir() / "_biblioteca"
    subpasta.mkdir(parents=True, exist_ok=True)
    destino = subpasta / nome_seguro
    destino.write_bytes(conteudo)
    return str(Path("_biblioteca") / nome_seguro)


def caminho_absoluto(arquivo_path: str) -> Path:
    return _base_dir() / arquivo_path


def remover_arquivo(arquivo_path: str) -> None:
    caminho = caminho_absoluto(arquivo_path)
    caminho.unlink(missing_ok=True)
