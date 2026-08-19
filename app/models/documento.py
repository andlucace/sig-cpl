import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import CategoriaDocumento, ConfidencialidadeDocumento


class Documento(TimestampedBase):
    """RF-042: repositório de documentos com classificação, metadados,
    versão, validade, assinatura, aprovação e retenção.

    O arquivo em si fica em disco (`arquivo_path`, relativo a
    `settings.uploads_dir` — ver `app/services/armazenamento.py`), não em
    blob no banco. Funciona igual em dev (pasta local) e numa VPS (mesma
    pasta, só que num volume Docker persistente) — só muda o volume
    montado, não o código."""

    __tablename__ = "documentos"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria: Mapped[CategoriaDocumento] = mapped_column(nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    confidencialidade: Mapped[ConfidencialidadeDocumento] = mapped_column(
        default=ConfidencialidadeDocumento.INTERNO, nullable=False
    )

    arquivo_path: Mapped[str] = mapped_column(String(500), nullable=False)
    nome_arquivo_original: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_mime: Mapped[str | None] = mapped_column(String(100))
    tamanho_bytes: Mapped[int | None] = mapped_column(Integer)

    versao: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    documento_anterior_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id"), nullable=True
    )

    data_validade: Mapped[date | None] = mapped_column(Date)
    assinado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    aprovado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    aprovado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    data_aprovacao: Mapped[date | None] = mapped_column(Date)
    data_retencao_ate: Mapped[date | None] = mapped_column(Date)

    criado_por_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    reuniao_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reunioes.id"), nullable=True
    )
    # Pedido explícito: documento de posse do órgão/conselho/comissão —
    # mesmo padrão de `reuniao_id` (upload dedicado, mas continua no
    # mesmo repositório de Documentos, RF-042, já filtrado por `cpl_id`
    # na listagem geral — sem tabela nova).
    orgao_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orgaos_governanca.id"), nullable=True
    )

    aprovado_por: Mapped["Pessoa | None"] = relationship()
    reuniao: Mapped["Reuniao | None"] = relationship()
    orgao: Mapped["OrgaoGovernanca | None"] = relationship()
