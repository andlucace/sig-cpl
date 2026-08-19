import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Sequence, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedBase
from app.models.enums import CategoriaDocumento, ConfidencialidadeDocumento, TipoAprovacaoDocumento

# Registrada na mesma `MetaData` do resto do app — `Base.metadata.
# create_all()`/`drop_all()` (usado pelos testes, que não rodam as
# migrações do Alembic) cria/derruba esta sequência sozinho, na ordem
# certa (antes da tabela `documentos`, que depende dela no
# `server_default` de `codigo` abaixo). Em produção, a migração
# `776412f023c7` cria a mesma sequência via SQL explícito.
sequencia_codigo_documento = Sequence("documentos_codigo_seq", metadata=Base.metadata)


class Documento(TimestampedBase):
    """RF-042: repositório de documentos com classificação, metadados,
    versão, validade, assinatura, aprovação e retenção.

    O arquivo em si fica em disco (`arquivo_path`, relativo a
    `settings.uploads_dir` — ver `app/services/armazenamento.py`), não em
    blob no banco. Funciona igual em dev (pasta local) e numa VPS (mesma
    pasta, só que num volume Docker persistente) — só muda o volume
    montado, não o código."""

    __tablename__ = "documentos"

    # Pedido explícito: código legível pra busca/referência — gerado pelo
    # próprio Postgres via `nextval()` (ver migração), não em Python, pra
    # não precisar tocar nos ~20 pontos do código que criam um `Documento`
    # (relatórios gerados automaticamente, atas, anexos de reunião/órgão
    # etc.) — qualquer INSERT novo já sai com código, de graça.
    codigo: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        server_default=text("'DOC-' || lpad(nextval('documentos_codigo_seq')::text, 6, '0')"),
    )
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
    requisitos: Mapped[list["AprovacaoDocumento"]] = relationship(back_populates="documento")


class AprovacaoDocumento(Base):
    """RF-042: uma aprovação ou assinatura específica exigida de uma
    pessoa para este documento — pedido explícito de "quantas e quais
    aprovações/assinaturas são necessárias", além do `aprovado`/`assinado`
    booleano acima (que continua valendo pra quem não precisa desse nível
    de detalhe — os dois convivem, um documento sem nenhum requisito
    cadastrado aqui simplesmente não mostra a contagem)."""

    __tablename__ = "aprovacoes_documento"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    documento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documentos.id"), nullable=False)
    pessoa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=False)
    tipo: Mapped[TipoAprovacaoDocumento] = mapped_column(nullable=False)
    concluido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    concluido_em: Mapped[date | None] = mapped_column(Date)

    documento: Mapped["Documento"] = relationship(back_populates="requisitos")
    pessoa: Mapped["Pessoa"] = relationship()
