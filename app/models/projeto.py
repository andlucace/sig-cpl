import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import (
    EstagioProjeto,
    ImpactoRisco,
    OrigemDemanda,
    PrioridadeProjeto,
    ProbabilidadeRisco,
    StatusDemanda,
    StatusRisco,
    StatusTarefa,
    TipoMeta,
)


class DemandaProjeto(TimestampedBase):
    """RF-031: demanda coletiva ou oportunidade de projeto, registrada
    antes de virar um `Projeto` formal — guarda de onde veio (empresa,
    comissão, instituição ou edital de fomento). `origem_id` é uma
    referência solta (sem FK de banco), mesmo padrão de
    `RegistroAuditoria.entidade_id` — a origem pode apontar pra tabelas
    diferentes conforme `origem_tipo`, então não dá pra usar uma única
    FK rígida."""

    __tablename__ = "demandas_projeto"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    origem_tipo: Mapped[OrigemDemanda] = mapped_column(nullable=False)
    origem_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    origem_detalhe: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[StatusDemanda] = mapped_column(default=StatusDemanda.REGISTRADA, nullable=False)
    registrado_por_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    projeto: Mapped["Projeto | None"] = relationship(back_populates="demanda_origem", uselist=False)


class Projeto(TimestampedBase):
    """RF-032: projeto no portfólio de uma CPL — prioridade, estágio,
    eixo do Programa SP Produz e vínculo ao planejamento estratégico.
    RF-033 (informações básicas do plano de trabalho — introdução,
    objeto, objetivos, justificativa, impactos), o campo de impactos
    socioambientais do RF-034 e continuidade/escalabilidade do RF-035
    moram nos mesmos campos da tabela, sem uma entidade
    `PlanoDeTrabalho` separada — é 1:1 com o projeto, não haveria ganho
    em separar. Aquisições e cronograma físico-financeiro (resto do
    RF-035), financeiro (RF-036 a RF-038) e execução (RF-039/040) ficam
    para as próximas fatias deste módulo.

    `eixo_sp_produz` é texto livre, não um enum fechado — o documento de
    requisitos não define a lista de eixos do programa."""

    __tablename__ = "projetos"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)
    demanda_origem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("demandas_projeto.id"), unique=True, nullable=True
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    eixo_sp_produz: Mapped[str | None] = mapped_column(String(150))
    estagio: Mapped[EstagioProjeto] = mapped_column(default=EstagioProjeto.DEMANDA, nullable=False)
    prioridade: Mapped[PrioridadeProjeto] = mapped_column(default=PrioridadeProjeto.MEDIA, nullable=False)
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    objetivo_estrategico_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("objetivos_estrategicos.id"), nullable=True
    )
    # RF-033: informações básicas do plano de trabalho.
    introducao: Mapped[str | None] = mapped_column(Text)
    objeto: Mapped[str | None] = mapped_column(Text)
    objetivos: Mapped[str | None] = mapped_column(Text)
    justificativa: Mapped[str | None] = mapped_column(Text)
    impactos: Mapped[str | None] = mapped_column(Text)
    # RF-034: impactos socioambientais — distinto do "impactos" geral do
    # RF-033 (que é sobre efeitos/resultados esperados do projeto como um
    # todo); este é especificamente sobre impacto socioambiental, um
    # conceito próprio em avaliação de projetos públicos no Brasil.
    impactos_socioambientais: Mapped[str | None] = mapped_column(Text)
    # RF-035: continuidade (o que garante que o projeto siga existindo
    # depois do apoio inicial) e escalabilidade (potencial de crescer/
    # replicar) — narrativos, mesmo padrão dos campos do RF-033.
    continuidade: Mapped[str | None] = mapped_column(Text)
    escalabilidade: Mapped[str | None] = mapped_column(Text)

    demanda_origem: Mapped["DemandaProjeto | None"] = relationship(back_populates="projeto")
    responsavel: Mapped["Pessoa | None"] = relationship()
    objetivo_estrategico: Mapped["ObjetivoEstrategico | None"] = relationship()
    etapas: Mapped[list["EtapaProjeto"]] = relationship(
        back_populates="projeto", order_by="EtapaProjeto.ordem"
    )
    metas: Mapped[list["MetaProjeto"]] = relationship(back_populates="projeto")
    indicadores: Mapped[list["IndicadorProjeto"]] = relationship(back_populates="projeto")
    riscos: Mapped[list["RiscoProjeto"]] = relationship(back_populates="projeto")
    equipe: Mapped[list["EquipeProjeto"]] = relationship(back_populates="projeto")
    origens_recurso: Mapped[list["OrigemRecursoProjeto"]] = relationship(back_populates="projeto")


class EtapaProjeto(TimestampedBase):
    """RF-034: etapa (com atividades) do plano de trabalho — cronograma
    previsto (`data_inicio`/`data_fim`) e status de execução. "Etapas" e
    "atividades" do requisito são tratadas como o mesmo nível — uma
    linha por etapa/atividade, sem hierarquia de dois níveis — mesma
    simplificação já usada em `TarefaGovernanca` (sem sub-tarefas)."""

    __tablename__ = "etapas_projeto"

    projeto_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projetos.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    ordem: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_inicio: Mapped[date | None] = mapped_column(Date)
    data_fim: Mapped[date | None] = mapped_column(Date)
    status: Mapped[StatusTarefa] = mapped_column(default=StatusTarefa.PENDENTE, nullable=False)

    projeto: Mapped["Projeto"] = relationship(back_populates="etapas")


class MetaProjeto(TimestampedBase):
    """RF-034: meta quantitativa ou qualitativa do plano de trabalho, com
    o resultado alcançado registrado no mesmo lugar (`valor_alcancado`)
    — não é uma série histórica como `IndicadorValorHistorico`, só o
    valor mais recente, suficiente pro escopo desta fatia."""

    __tablename__ = "metas_projeto"

    projeto_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projetos.id"), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[TipoMeta] = mapped_column(nullable=False)
    valor_alvo: Mapped[str | None] = mapped_column(String(255))
    valor_alcancado: Mapped[str | None] = mapped_column(String(255))
    prazo: Mapped[date | None] = mapped_column(Date)
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    status: Mapped[StatusTarefa] = mapped_column(default=StatusTarefa.PENDENTE, nullable=False)

    projeto: Mapped["Projeto"] = relationship(back_populates="metas")
    responsavel: Mapped["Pessoa | None"] = relationship()


class IndicadorProjeto(TimestampedBase):
    """RF-034: indicador de acompanhamento do projeto — versão mais
    simples que `IndicadorEstrategico` (RF-044), sem série histórica
    própria (só o valor mais recente); se isso vier a ser necessário,
    seguir o mesmo padrão de `IndicadorValorHistorico`."""

    __tablename__ = "indicadores_projeto"

    projeto_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projetos.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade_medida: Mapped[str | None] = mapped_column(String(100))
    meta_valor: Mapped[str | None] = mapped_column(String(255))
    valor_atual: Mapped[str | None] = mapped_column(String(255))
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )

    projeto: Mapped["Projeto"] = relationship(back_populates="indicadores")
    responsavel: Mapped["Pessoa | None"] = relationship()


class RiscoProjeto(TimestampedBase):
    """RF-034/040: risco identificado do projeto — probabilidade, impacto
    e resposta planejada (mitigação). Campos já cobrem o que o RF-040
    (Execução, ainda não construído) pede a mais detalhe; quando esse
    módulo for construído, a extensão natural é reaproveitar este
    modelo (ex.: ligar evidência de mitigação ao repositório de
    Documentos, como `AvaliacaoCriterio.evidencia_documento_id` já faz),
    não duplicar."""

    __tablename__ = "riscos_projeto"

    projeto_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projetos.id"), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    probabilidade: Mapped[ProbabilidadeRisco] = mapped_column(nullable=False)
    impacto: Mapped[ImpactoRisco] = mapped_column(nullable=False)
    resposta: Mapped[str | None] = mapped_column(Text)
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=True
    )
    status: Mapped[StatusRisco] = mapped_column(default=StatusRisco.ATIVO, nullable=False)

    projeto: Mapped["Projeto"] = relationship(back_populates="riscos")
    responsavel: Mapped["Pessoa | None"] = relationship()


class EquipeProjeto(TimestampedBase):
    """RF-035: composição da equipe do projeto — pessoa, função exercida
    e vigência, mesmo padrão de `MembroOrgao` (RF-016). `funcao` é texto
    livre, não um enum fechado — funções variam demais entre projetos
    (coordenador técnico, responsável financeiro etc.) pra caber numa
    lista fixa, mesmo raciocínio de `eixo_sp_produz`."""

    __tablename__ = "equipe_projeto"

    projeto_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projetos.id"), nullable=False)
    pessoa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pessoas.id"), nullable=False)
    funcao: Mapped[str] = mapped_column(String(150), nullable=False)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    projeto: Mapped["Projeto"] = relationship(back_populates="equipe")
    pessoa: Mapped["Pessoa"] = relationship()


class OrigemRecursoProjeto(TimestampedBase):
    """RF-035: origem dos recursos do projeto — fonte (recursos próprios,
    edital, parceria etc., texto livre pelo mesmo motivo de
    `eixo_sp_produz`: o documento não define uma lista fechada), valor
    previsto e se exige contrapartida. Primeiro campo monetário do
    sistema — `Numeric(14, 2)`, diferente do `valor_alvo` textual de
    `MetaProjeto` (que também aceita metas não-numéricas como "30
    empresas"), porque aqui é sempre dinheiro de verdade."""

    __tablename__ = "origens_recurso_projeto"

    projeto_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projetos.id"), nullable=False)
    fonte: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    contrapartida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)

    projeto: Mapped["Projeto"] = relationship(back_populates="origens_recurso")
