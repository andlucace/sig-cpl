"""RF-052/F09: busca de competências pra matchmaking — dado o texto livre
de uma demanda, procura entidades candidatas (universidade, ICT,
prestador/fornecedor, ambiente de inovação) cujo nome ou alguma oferta
(RF-010) combine com o termo buscado. Curadoria continua humana (RN-016):
esta função só reduz a lista pra alguém escolher, nunca decide um match
sozinha."""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.entidade import Entidade, OfertaEntidade
from app.models.enums import TipoEntidade

TIPOS_COMPETENCIA_PADRAO = [
    TipoEntidade.UNIVERSIDADE,
    TipoEntidade.ICT,
    TipoEntidade.PRESTADOR,
    TipoEntidade.AMBIENTE_INOVACAO,
]
"""RF-052 cita "universidades, ICTs, fornecedores, startups e ambientes
SPAI" — "fornecedor" mapeia pra `PRESTADOR` e "ambiente SPAI" pra
`AMBIENTE_INOVACAO`; "startup" não tem tipo próprio no cadastro (vira
`EMPRESA`), por isso não é um filtro padrão, mas nada impede escolher
`EMPRESA` explicitamente na busca."""


def buscar_competencias(
    db: Session,
    termo: str | None = None,
    tipos: list[TipoEntidade] | None = None,
) -> list[Entidade]:
    tipos_filtro = tipos if tipos else TIPOS_COMPETENCIA_PADRAO
    query = db.query(Entidade).filter(Entidade.tipo.in_(tipos_filtro))
    if termo:
        coringa = f"%{termo}%"
        query = query.filter(
            or_(
                Entidade.razao_social.ilike(coringa),
                Entidade.nome_fantasia.ilike(coringa),
                Entidade.id.in_(
                    db.query(OfertaEntidade.entidade_id).filter(
                        or_(OfertaEntidade.nome.ilike(coringa), OfertaEntidade.descricao.ilike(coringa))
                    )
                ),
            )
        )
    return query.order_by(Entidade.razao_social).all()
