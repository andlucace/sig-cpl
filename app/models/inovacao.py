import uuid

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import StatusMatchInovacao


class MatchInovacao(TimestampedBase):
    """RF-052/F09: pareamento entre uma demanda de inovação de uma
    empresa e uma entidade candidata a suprir a competência buscada
    (universidade, ICT, fornecedor, ambiente SPAI). Reaproveita
    `DemandaProjeto` (RF-031) em vez de criar uma "demanda de inovação"
    paralela — `origem_tipo=EMPRESA` já é exatamente "demanda das
    empresas" citada pelo requisito, e o fluxo F09 do modelo conceitual
    (demanda → busca de competência → matchmaking → projeto de P&D)
    termina no mesmo lugar que RF-031/032 (`Projeto`, via o endpoint de
    conversão que já existe). "Competência" reaproveita `OfertaEntidade`
    (RF-010) — o documento de requisitos já não distingue "competência"
    de "produto/serviço/tecnologia" (ver seção 10, modelo conceitual).

    Curadoria humana, não algoritmo: RN-016 (decisões de priorização não
    podem ser tomadas só por algoritmo) — o sistema ajuda a buscar
    candidatos (filtro por tipo/texto em
    `app/services/inovacao.py::buscar_competencias`), mas quem sugere e
    decide o status de cada match é sempre uma pessoa."""

    __tablename__ = "matches_inovacao"
    __table_args__ = (UniqueConstraint("demanda_id", "entidade_id", name="uq_match_demanda_entidade"),)

    demanda_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("demandas_projeto.id"), nullable=False
    )
    entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entidades.id"), nullable=False)
    oferta_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ofertas_entidade.id"), nullable=True
    )
    status: Mapped[StatusMatchInovacao] = mapped_column(default=StatusMatchInovacao.SUGERIDO, nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text)
    sugerido_por_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    demanda: Mapped["DemandaProjeto"] = relationship()
    entidade: Mapped["Entidade"] = relationship()
    oferta: Mapped["OfertaEntidade | None"] = relationship()
    sugerido_por: Mapped["Usuario"] = relationship()
