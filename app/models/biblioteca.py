import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import TipoRecursoBiblioteca


class RecursoBiblioteca(TimestampedBase):
    """RF-051: biblioteca de conhecimento — conteúdo compartilhado entre
    todas as CPLs (modelos, estudos, boas práticas, editais/oportunidades
    em destaque, conteúdo técnico), não o repositório de documentos
    operacionais de uma CPL específica (RF-042, `Documento`, sempre preso
    a um `cpl_id`). Um recurso pode ser um arquivo enviado (`arquivo_path`,
    reaproveitando o mesmo mecanismo de armazenamento de `Documento` — ver
    `app/services/armazenamento.py::salvar_arquivo_biblioteca`), um link
    externo (`url_externa`) ou só texto (`descricao`) — nenhum dos três é
    obrigatório sozinho, mas ao menos algum conteúdo (arquivo, link ou
    descrição) precisa existir, validado na camada de schema.

    `publicado` controla visibilidade: só quem administra a biblioteca
    (`PAPEIS_EDITAL_GESTAO`, mesma autoridade de `Edital` — conteúdo
    compartilhado gerido pela plataforma) vê rascunhos não publicados."""

    __tablename__ = "recursos_biblioteca"

    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoRecursoBiblioteca] = mapped_column(nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)

    arquivo_path: Mapped[str | None] = mapped_column(String(500))
    nome_arquivo_original: Mapped[str | None] = mapped_column(String(255))
    tipo_mime: Mapped[str | None] = mapped_column(String(100))
    tamanho_bytes: Mapped[int | None] = mapped_column(Integer)
    url_externa: Mapped[str | None] = mapped_column(String(500))

    publicado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_por_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    criado_por: Mapped["Usuario"] = relationship()
