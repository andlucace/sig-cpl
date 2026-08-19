import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedBase
from app.models.enums import ResultadoDeliberacao, StatusReuniao, StatusTarefa, TipoOrgao, TipoVoto


class OrgaoGovernanca(TimestampedBase):
    """RF-015/RF-016: conselho, câmara, comissão temática ou grupo de trabalho
    da estrutura de governança de uma CPL, com competências, quórum e
    periodicidade parametrizáveis sem alteração de código."""

    __tablename__ = "orgaos_governanca"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoOrgao] = mapped_column(nullable=False)
    competencias: Mapped[str | None] = mapped_column(Text)
    quorum_minimo_percentual: Mapped[float | None] = mapped_column(Float)
    periodicidade: Mapped[str | None] = mapped_column(String(100))
    estatuto_regimento_referencia: Mapped[str | None] = mapped_column(String(500))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    membros: Mapped[list["MembroOrgao"]] = relationship(back_populates="orgao")
    reunioes: Mapped[list["Reuniao"]] = relationship(back_populates="orgao")


class MembroOrgao(Base):
    """RF-016: composição do órgão — pessoa, função exercida e vigência
    do mandato (data_inicio/data_fim)."""

    __tablename__ = "membros_orgao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orgao_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgaos_governanca.id"))
    pessoa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pessoas.id"))
    funcao: Mapped[str] = mapped_column(String(150), nullable=False)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Pedido explícito: excluir um membro exige motivo (texto), preservado
    # aqui — a alteração de `ativo`/`motivo_remocao` já cai na trilha de
    # auditoria automática (app/services/auditoria.py), sem chamada manual.
    motivo_remocao: Mapped[str | None] = mapped_column(Text)

    orgao: Mapped["OrgaoGovernanca"] = relationship(back_populates="membros")
    pessoa: Mapped["Pessoa"] = relationship()


class Reuniao(TimestampedBase):
    """RF-017: agenda, convocação, pauta e registro de reuniões de um órgão."""

    __tablename__ = "reunioes"

    orgao_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgaos_governanca.id"))
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    local: Mapped[str | None] = mapped_column(String(255))
    pauta: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusReuniao] = mapped_column(default=StatusReuniao.AGENDADA, nullable=False)
    convocada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ata: Mapped[str | None] = mapped_column(Text)
    quorum_atingido: Mapped[bool | None] = mapped_column(Boolean)

    # Pedido explícito: e-mail de convocação para todos os membros do
    # órgão — mesmo padrão resiliente de `CampanhaConvite.email_*`
    # (app/services/campanhas.py): nunca bloqueia a convocação em si, só
    # registra o que aconteceu (ver app/services/governanca.py).
    email_convocacao_enviado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_convocacao_enviado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_convocacao_destinatarios: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    email_convocacao_erro: Mapped[str | None] = mapped_column(String(500), nullable=True)

    orgao: Mapped["OrgaoGovernanca"] = relationship(back_populates="reunioes")
    presencas: Mapped[list["Presenca"]] = relationship(back_populates="reuniao")
    deliberacoes: Mapped[list["Deliberacao"]] = relationship(back_populates="reuniao")


class Presenca(Base):
    """RF-017: registro de presença de cada membro convocado para a reunião."""

    __tablename__ = "presencas"
    __table_args__ = (UniqueConstraint("reuniao_id", "pessoa_id", name="uq_presenca_reuniao_pessoa"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reuniao_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("reunioes.id"))
    pessoa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pessoas.id"))
    presente: Mapped[bool] = mapped_column(Boolean, nullable=False)
    justificativa_ausencia: Mapped[str | None] = mapped_column(Text)

    reuniao: Mapped["Reuniao"] = relationship(back_populates="presencas")
    pessoa: Mapped["Pessoa"] = relationship()


class Deliberacao(TimestampedBase):
    """RF-018: deliberação tomada em reunião — quórum, resultado, responsável
    pela execução, prazo e evidência (RN-007: nenhuma decisão sem rastro)."""

    __tablename__ = "deliberacoes"

    reuniao_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("reunioes.id"))
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[ResultadoDeliberacao] = mapped_column(
        default=ResultadoDeliberacao.PENDENTE, nullable=False
    )
    quorum_necessario_percentual: Mapped[float | None] = mapped_column(Float)
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    prazo_execucao: Mapped[date | None] = mapped_column(Date)
    evidencia_execucao: Mapped[str | None] = mapped_column(Text)

    reuniao: Mapped["Reuniao"] = relationship(back_populates="deliberacoes")
    responsavel: Mapped["Pessoa | None"] = relationship()
    votos: Mapped[list["VotoRegistro"]] = relationship(back_populates="deliberacao")
    tarefas: Mapped[list["TarefaGovernanca"]] = relationship(back_populates="deliberacao")


class VotoRegistro(Base):
    """RF-018/RF-020: voto de cada membro numa deliberação; um voto
    'impedido' registra o motivo do conflito de interesses (RN: impedimentos
    não podem ser tomados sem registro de justificativa)."""

    __tablename__ = "votos"
    __table_args__ = (UniqueConstraint("deliberacao_id", "pessoa_id", name="uq_voto_deliberacao_pessoa"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deliberacao_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deliberacoes.id"))
    pessoa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pessoas.id"))
    voto: Mapped[TipoVoto] = mapped_column(nullable=False)
    motivo_impedimento: Mapped[str | None] = mapped_column(Text)

    deliberacao: Mapped["Deliberacao"] = relationship(back_populates="votos")
    pessoa: Mapped["Pessoa"] = relationship()


class TarefaGovernanca(TimestampedBase):
    """RF-019: tarefa/plano de ação decorrente de uma deliberação, com
    responsável, prazo e status para controle de execução."""

    __tablename__ = "tarefas_governanca"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    deliberacao_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deliberacoes.id"), nullable=True
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    prazo: Mapped[date | None] = mapped_column(Date)
    status: Mapped[StatusTarefa] = mapped_column(default=StatusTarefa.PENDENTE, nullable=False)

    deliberacao: Mapped["Deliberacao | None"] = relationship(back_populates="tarefas")
    responsavel: Mapped["Pessoa | None"] = relationship()


class DeclaracaoImpedimento(TimestampedBase):
    """RF-020: declaração de conflito de interesses/impedimento, associável a
    um órgão e/ou reunião específicos — independente de já existir um voto."""

    __tablename__ = "declaracoes_impedimento"

    pessoa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=False)
    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    orgao_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orgaos_governanca.id"), nullable=True
    )
    reuniao_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reunioes.id"), nullable=True
    )
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    data_declaracao: Mapped[date] = mapped_column(Date, nullable=False)

    pessoa: Mapped["Pessoa"] = relationship()
