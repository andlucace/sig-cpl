"""F01: regras de negócio da solicitação de adesão — validação de
formato na criação (reaproveita `app/services/validadores.py`, RF-014,
mesmo padrão já usado nos outros pontos de escrita — campanha/planilha/
API — pra nunca ficar divergente entre eles) e a transição
pendente→aprovada/rejeitada, que é o que efetivamente cria ou reaproveita
a `Entidade` e os vínculos (RN-003, RF-009), sempre disparada por uma
decisão humana (RN-016)."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.models.adesao import SolicitacaoAdesao
from app.models.entidade import Entidade, EntidadeCPL, EntidadeElo
from app.models.enums import Papel, StatusSolicitacaoAdesao
from app.models.pessoa import Pessoa, PessoaVinculo
from app.schemas.adesao import SolicitacaoAdesaoCreate
from app.services.validadores import cnpj_valido, cpf_valido, normalizar_cnpj, normalizar_cpf, uf_valida


class SolicitacaoInvalida(Exception):
    pass


def criar_solicitacao(db: Session, cpl_id: uuid.UUID, dados: SolicitacaoAdesaoCreate) -> SolicitacaoAdesao:
    if not dados.consentimento_lgpd:
        raise SolicitacaoInvalida("É necessário consentir com o tratamento de dados para solicitar adesão.")
    if dados.cnpj and not cnpj_valido(dados.cnpj):
        raise SolicitacaoInvalida("CNPJ inválido.")
    if dados.cpf and not cpf_valido(dados.cpf):
        raise SolicitacaoInvalida("CPF inválido.")
    if dados.uf and not uf_valida(dados.uf):
        raise SolicitacaoInvalida("UF inválida.")

    solicitacao = SolicitacaoAdesao(
        cpl_id=cpl_id,
        tipo=dados.tipo,
        razao_social=dados.razao_social,
        cnpj=normalizar_cnpj(dados.cnpj) if dados.cnpj else None,
        cpf=normalizar_cpf(dados.cpf) if dados.cpf else None,
        municipio=dados.municipio,
        uf=dados.uf.upper() if dados.uf else None,
        elo_pretendido=dados.elo_pretendido,
        mensagem=dados.mensagem,
        contato_nome=dados.contato_nome,
        contato_email=dados.contato_email,
        contato_telefone=dados.contato_telefone,
        consentimento_lgpd=True,
        consentimento_em=datetime.now(UTC),
    )
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)
    return solicitacao


def _encontrar_ou_criar_entidade(db: Session, solicitacao: SolicitacaoAdesao) -> Entidade:
    entidade = None
    if solicitacao.cnpj:
        entidade = db.query(Entidade).filter(Entidade.cnpj == solicitacao.cnpj).first()
    elif solicitacao.cpf:
        entidade = db.query(Entidade).filter(Entidade.cpf == solicitacao.cpf).first()
    if entidade is not None:
        return entidade

    entidade = Entidade(
        tipo=solicitacao.tipo,
        razao_social=solicitacao.razao_social,
        cnpj=solicitacao.cnpj,
        cpf=solicitacao.cpf,
        municipio=solicitacao.municipio,
        uf=solicitacao.uf,
    )
    db.add(entidade)
    db.flush()
    return entidade


def _vincular_entidade_e_elo(db: Session, solicitacao: SolicitacaoAdesao, entidade: Entidade) -> None:
    vinculo = (
        db.query(EntidadeCPL)
        .filter(EntidadeCPL.cpl_id == solicitacao.cpl_id, EntidadeCPL.entidade_id == entidade.id)
        .first()
    )
    if vinculo is None:
        db.add(EntidadeCPL(cpl_id=solicitacao.cpl_id, entidade_id=entidade.id, data_vinculo=date.today()))
    elif not vinculo.ativo:
        vinculo.ativo = True

    elo = (
        db.query(EntidadeElo)
        .filter(
            EntidadeElo.cpl_id == solicitacao.cpl_id,
            EntidadeElo.entidade_id == entidade.id,
            EntidadeElo.elo == solicitacao.elo_pretendido,
        )
        .first()
    )
    if elo is None:
        db.add(EntidadeElo(cpl_id=solicitacao.cpl_id, entidade_id=entidade.id, elo=solicitacao.elo_pretendido))
    elif not elo.ativo:
        elo.ativo = True


def _vincular_pessoa_contato(db: Session, solicitacao: SolicitacaoAdesao, entidade: Entidade) -> None:
    """Registra quem preencheu o pedido como `PessoaVinculo` da entidade
    nesta CPL (papel `EMPRESA_MEMBRO` — vínculo organizacional, não
    concede login nenhum: criar `Usuario` continua sendo uma ação
    separada de quem administra). Idempotente por e-mail — reaproveita a
    `Pessoa` se ela já existir."""

    pessoa = db.query(Pessoa).filter(Pessoa.email == solicitacao.contato_email).first()
    if pessoa is None:
        pessoa = Pessoa(
            nome=solicitacao.contato_nome,
            email=solicitacao.contato_email,
            telefone=solicitacao.contato_telefone,
        )
        db.add(pessoa)
        db.flush()

    ja_vinculada = (
        db.query(PessoaVinculo)
        .filter(
            PessoaVinculo.pessoa_id == pessoa.id,
            PessoaVinculo.entidade_id == entidade.id,
            PessoaVinculo.cpl_id == solicitacao.cpl_id,
        )
        .first()
    )
    if ja_vinculada is None:
        db.add(
            PessoaVinculo(
                pessoa_id=pessoa.id,
                entidade_id=entidade.id,
                cpl_id=solicitacao.cpl_id,
                papel=Papel.EMPRESA_MEMBRO,
                cargo="Solicitante de adesão",
                data_inicio=date.today(),
            )
        )


def aprovar_solicitacao(
    db: Session, solicitacao: SolicitacaoAdesao, analisado_por_id: uuid.UUID, parecer: str | None
) -> SolicitacaoAdesao:
    if solicitacao.status != StatusSolicitacaoAdesao.PENDENTE:
        raise SolicitacaoInvalida("Esta solicitação já foi analisada.")

    entidade = _encontrar_ou_criar_entidade(db, solicitacao)
    _vincular_entidade_e_elo(db, solicitacao, entidade)
    _vincular_pessoa_contato(db, solicitacao, entidade)

    solicitacao.status = StatusSolicitacaoAdesao.APROVADA
    solicitacao.parecer = parecer
    solicitacao.analisado_por_id = analisado_por_id
    solicitacao.data_analise = date.today()
    solicitacao.entidade_id = entidade.id
    db.commit()
    db.refresh(solicitacao)
    return solicitacao


def rejeitar_solicitacao(
    db: Session, solicitacao: SolicitacaoAdesao, analisado_por_id: uuid.UUID, parecer: str | None
) -> SolicitacaoAdesao:
    if solicitacao.status != StatusSolicitacaoAdesao.PENDENTE:
        raise SolicitacaoInvalida("Esta solicitação já foi analisada.")

    solicitacao.status = StatusSolicitacaoAdesao.REJEITADA
    solicitacao.parecer = parecer
    solicitacao.analisado_por_id = analisado_por_id
    solicitacao.data_analise = date.today()
    db.commit()
    db.refresh(solicitacao)
    return solicitacao
