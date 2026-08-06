import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedBase
from app.models.enums import Elo, TipoEntidade, TipoOferta

if TYPE_CHECKING:
    from app.models.cpl import CPL


class Entidade(TimestampedBase):
    """RF-006/RF-008: empresa, órgão, associação, universidade, ICT, startup,
    fornecedor ou ambiente de inovação. Uma entidade pode se vincular a mais
    de uma CPL (RN-003), tratada via EntidadeCPL."""

    __tablename__ = "entidades"

    tipo: Mapped[TipoEntidade] = mapped_column(nullable=False)
    razao_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nome_fantasia: Mapped[str | None] = mapped_column(String(255))

    cnpj: Mapped[str | None] = mapped_column(String(20), index=True)
    cpf: Mapped[str | None] = mapped_column(String(14), index=True)
    cnae: Mapped[str | None] = mapped_column(String(20))
    porte: Mapped[str | None] = mapped_column(String(50))

    municipio: Mapped[str | None] = mapped_column(String(255))
    uf: Mapped[str | None] = mapped_column(String(2))
    endereco: Mapped[str | None] = mapped_column(String(500))

    situacao_cadastral: Mapped[str | None] = mapped_column(String(100))
    # RF-010: dict de canais conhecidos (site/instagram/facebook/linkedin/
    # whatsapp) -> URL ou contato; chaves não fechadas em enum porque o
    # formulário só edita um conjunto pequeno e conhecido, mas o campo
    # aceita qualquer chave (ex.: escrita direta via API).
    canais_digitais: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    ofertas: Mapped[list["OfertaEntidade"]] = relationship(back_populates="entidade")


class EntidadeCPL(Base):
    """Associação N:N entre Entidade e CPL (RN-003), registrando o vínculo
    e permitindo que a mesma organização participe de múltiplas CPLs com
    permissões e dados tratados por vínculo."""

    __tablename__ = "entidade_cpl"
    __table_args__ = (UniqueConstraint("entidade_id", "cpl_id", name="uq_entidade_cpl"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entidades.id"))
    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"))
    data_vinculo: Mapped[date] = mapped_column(Date, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    entidade: Mapped["Entidade"] = relationship()
    cpl: Mapped["CPL"] = relationship()


class EntidadeElo(Base):
    """RF-009: classifica cada ator nos elos da cadeia, admitindo múltiplos
    elos por entidade dentro de uma mesma CPL."""

    __tablename__ = "entidade_elo"
    __table_args__ = (
        UniqueConstraint("entidade_id", "cpl_id", "elo", name="uq_entidade_cpl_elo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entidades.id"))
    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"))
    elo: Mapped[Elo] = mapped_column(nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class OfertaEntidade(TimestampedBase):
    """RF-010: produto, serviço ou tecnologia ofertado por uma entidade —
    junto com `EntidadeElo` (RF-009) e certificações/diferenciais
    competitivos (já modelados em `DiagnosticoCadastral`), fecha "elo e
    oferta" do modelo conceitual (seção 10 do documento de requisitos).
    Não escopado por CPL como `EntidadeElo` — o que uma entidade produz é
    uma característica dela, não algo que muda conforme a CPL em que
    está vinculada."""

    __tablename__ = "ofertas_entidade"

    entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entidades.id"), nullable=False)
    tipo: Mapped[TipoOferta] = mapped_column(nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    entidade: Mapped["Entidade"] = relationship(back_populates="ofertas")
