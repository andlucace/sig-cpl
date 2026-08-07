"""F01 (fluxo de autoatendimento do modelo conceitual, seção 11):
"Convite/solicitação → cadastro → consentimento → validação → vínculo à
CPL → classificação de elo → ativação" — o único passo desse fluxo que
faltava era o autoatendimento em si; hoje toda `Entidade` é cadastrada e
vinculada direto por quem já tem papel de gestão (RF-006/008), sem porta
de entrada pra quem está de fora.

`SolicitacaoAdesao` é o registro desse pedido — nunca cria `Entidade`/
`EntidadeCPL`/`EntidadeElo` no momento da submissão, só na aprovação (ver
`app/services/adesao.py::aprovar_solicitacao`); fica `PENDENTE` até uma
pessoa com papel de gestão decidir, mesmo raciocínio de decisão sempre
humana já usado em `MatchInovacao`/`ItemHabilitacaoJuridica` (RN-016).

"Convite" (a outra metade do "Convite/solicitação" do requisito) não
ganhou infraestrutura própria (token, e-mail) nesta fatia — a gestão de
uma CPL simplesmente compartilha a URL pública do formulário
(`/cpls/{id}/solicitar-adesao`, linkada a partir do portal de
transparência, RF-055) com quem quiser convidar; é o mesmo formulário,
só descoberto por um canal diferente. Um convite com token dedicado
(como o de `CampanhaConvite`, RF-012) só faria sentido pra rastrear quem
foi convidado especificamente, o que este requisito não pede."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import Elo, StatusSolicitacaoAdesao, TipoEntidade

if TYPE_CHECKING:
    from app.models.cpl import CPL
    from app.models.entidade import Entidade
    from app.models.usuario import Usuario


class SolicitacaoAdesao(TimestampedBase):
    __tablename__ = "solicitacoes_adesao"

    cpl_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cpls.id"), nullable=False)

    # cadastro
    tipo: Mapped[TipoEntidade] = mapped_column(nullable=False)
    razao_social: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(20))
    cpf: Mapped[str | None] = mapped_column(String(14))
    municipio: Mapped[str | None] = mapped_column(String(255))
    uf: Mapped[str | None] = mapped_column(String(2))
    elo_pretendido: Mapped[Elo] = mapped_column(nullable=False)
    mensagem: Mapped[str | None] = mapped_column(Text)

    # contato — pessoa que preencheu o pedido; não necessariamente terá
    # login (criar Usuario continua sendo uma ação separada, de quem
    # administra, não algo que o autoatendimento faz sozinho)
    contato_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    contato_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contato_telefone: Mapped[str | None] = mapped_column(String(50))

    # consentimento (LGPD) — obrigatório pra a solicitação existir;
    # `consentimento_em` fica congelado no momento da submissão mesmo
    # que a análise demore, é a prova de quando o consentimento foi dado
    consentimento_lgpd: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consentimento_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # validação
    status: Mapped[StatusSolicitacaoAdesao] = mapped_column(
        default=StatusSolicitacaoAdesao.PENDENTE, nullable=False
    )
    parecer: Mapped[str | None] = mapped_column(Text)
    analisado_por_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    data_analise: Mapped[date | None] = mapped_column(Date)

    # ativação — só preenchido na aprovação (Entidade criada ou
    # reaproveitada por CNPJ/CPF já existente)
    entidade_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("entidades.id"))

    cpl: Mapped["CPL"] = relationship()
    entidade: Mapped["Entidade | None"] = relationship()
    analisado_por: Mapped["Usuario | None"] = relationship()
