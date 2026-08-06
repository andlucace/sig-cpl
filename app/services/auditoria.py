import datetime
import decimal
import enum
import uuid

from sqlalchemy import event, insert, inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.audit_context import ip_atual, usuario_atual_id
from app.models.auditoria import RegistroAuditoria
from app.models.enums import AcaoAuditoria

# RN-014/RNF-002: nunca gravar segredos na trilha, mesmo que o modelo mude.
# "token" cobre qualquer credencial de uso único guardada em texto puro
# num campo com esse nome (ex.: `TokenRecuperacaoSenha.token`,
# `CampanhaConvite.token`) — redigido pelo nome do campo, não por modelo,
# então vale pra qualquer um novo que apareça sem precisar lembrar de
# atualizar esta lista.
_CAMPOS_REDIGIDOS = {"hashed_password", "mfa_secret", "mfa_backup_codes", "token"}

# Cadeias de navegação usadas para descobrir a CPL de um registro que não
# guarda cpl_id diretamente (ex.: um voto só chega à CPL via
# deliberação -> reunião -> órgão). Percorridas em ordem; a primeira que
# resolver sem erro/None é usada.
_CAMINHOS_CPL = (
    "orgao.cpl_id",
    "reuniao.orgao.cpl_id",
    "deliberacao.reuniao.orgao.cpl_id",
    "planejamento.cpl_id",
    "objetivo.planejamento.cpl_id",
    "campanha.cpl_id",
    "lote.cpl_id",
)


def _json_seguro(valor):
    if isinstance(valor, enum.Enum):
        return valor.value
    if isinstance(valor, uuid.UUID):
        return str(valor)
    if isinstance(valor, (datetime.datetime, datetime.date)):
        return valor.isoformat()
    if isinstance(valor, decimal.Decimal):
        return float(valor)
    return valor


def _resolver_cpl_id(obj) -> uuid.UUID | None:
    if hasattr(obj, "cpl_id"):
        valor = getattr(obj, "cpl_id", None)
        if valor is not None:
            return valor
    for caminho in _CAMINHOS_CPL:
        try:
            valor = obj
            for atributo in caminho.split("."):
                valor = getattr(valor, atributo)
                if valor is None:
                    break
            if valor is not None:
                return valor
        except AttributeError:
            continue
    return None


def _serializar_atual(obj) -> dict:
    mapper = sa_inspect(obj).mapper
    return {
        coluna.key: _json_seguro(getattr(obj, coluna.key))
        for coluna in mapper.columns
        if coluna.key not in _CAMPOS_REDIGIDOS
    }


def _diff_alteracoes(obj) -> tuple[dict, dict]:
    mapper = sa_inspect(obj).mapper
    estado = sa_inspect(obj)
    antes: dict = {}
    depois: dict = {}
    for coluna in mapper.columns:
        if coluna.key in _CAMPOS_REDIGIDOS:
            continue
        historico = estado.attrs[coluna.key].history
        if not historico.has_changes():
            continue
        valor_antigo = historico.deleted[0] if historico.deleted else None
        valor_novo = historico.added[0] if historico.added else getattr(obj, coluna.key)
        antes[coluna.key] = _json_seguro(valor_antigo)
        depois[coluna.key] = _json_seguro(valor_novo)
    return antes, depois


_CHAVE_PENDENTES_CRIACAO = "_pendentes_auditoria_criacao"


@event.listens_for(Session, "before_flush")
def _capturar_auditoria_antes(session: Session, flush_context, instances) -> None:
    """RF-056/RNF-003: gera trilha automaticamente para toda criação,
    alteração e exclusão de qualquer modelo mapeado, sem exigir chamada
    manual espalhada pelos ~30 endpoints do sistema.

    Criações são um caso especial: colunas com `default=` (ex.: `id`,
    `ativo`) só são preenchidas por SQLAlchemy durante a própria execução
    do INSERT, que acontece DEPOIS deste evento — serializar o objeto
    aqui capturaria `None` nesses campos. Por isso só resolvemos a CPL
    (que depende de FKs já setadas pelo chamador, não de defaults) e
    guardamos a referência ao objeto; a serialização completa e o
    registro em si ficam para `after_flush` (ver `_capturar_auditoria_depois`),
    quando os valores gerados já existem."""

    pendentes_criacao = [
        (obj, _resolver_cpl_id(obj))
        for obj in session.new
        if not isinstance(obj, RegistroAuditoria) and hasattr(obj, "id")
    ]
    session.info[_CHAVE_PENDENTES_CRIACAO] = (pendentes_criacao, usuario_atual_id.get(), ip_atual.get())

    usuario_id = usuario_atual_id.get()
    ip = ip_atual.get()
    novos_registros: list[RegistroAuditoria] = []

    for obj in session.dirty:
        if isinstance(obj, RegistroAuditoria) or not hasattr(obj, "id"):
            continue
        antes, depois = _diff_alteracoes(obj)
        if not antes:
            continue
        novos_registros.append(
            RegistroAuditoria(
                usuario_id=usuario_id,
                acao=AcaoAuditoria.ATUALIZACAO,
                entidade_tipo=type(obj).__name__,
                entidade_id=getattr(obj, "id", None),
                cpl_id=_resolver_cpl_id(obj),
                dados_anteriores=antes,
                dados_novos=depois,
                ip_address=ip,
            )
        )

    for obj in session.deleted:
        if isinstance(obj, RegistroAuditoria) or not hasattr(obj, "id"):
            continue
        novos_registros.append(
            RegistroAuditoria(
                usuario_id=usuario_id,
                acao=AcaoAuditoria.EXCLUSAO,
                entidade_tipo=type(obj).__name__,
                entidade_id=getattr(obj, "id", None),
                cpl_id=_resolver_cpl_id(obj),
                dados_anteriores=_serializar_atual(obj),
                ip_address=ip,
            )
        )

    for registro in novos_registros:
        session.add(registro)


@event.listens_for(Session, "after_flush")
def _capturar_auditoria_depois(session: Session, flush_context) -> None:
    """Segunda metade da captura de CRIACAO (ver `_capturar_auditoria_antes`):
    a essa altura o INSERT dos objetos novos já foi executado e seus
    campos com `default=` (id, ativo etc.) já estão populados no objeto
    Python. Inserimos via `session.execute` (Core, não `session.add`)
    porque adicionar novos objetos ORM dentro de `after_flush` não é
    suportado pelo SQLAlchemy."""

    pendentes = session.info.pop(_CHAVE_PENDENTES_CRIACAO, None)
    if not pendentes:
        return
    objetos, usuario_id, ip = pendentes
    linhas = [
        {
            "id": uuid.uuid4(),
            "usuario_id": usuario_id,
            "acao": AcaoAuditoria.CRIACAO,
            "entidade_tipo": type(obj).__name__,
            "entidade_id": getattr(obj, "id", None),
            "cpl_id": cpl_id,
            "dados_novos": _serializar_atual(obj),
            "ip_address": ip,
        }
        for obj, cpl_id in objetos
    ]
    if linhas:
        session.execute(insert(RegistroAuditoria.__table__), linhas)


LIMITE_PADRAO = 50
LIMITE_MAXIMO = 200


def consultar_registros(
    db: Session,
    *,
    cpl_id: uuid.UUID | None = None,
    somente_global: bool = False,
    acao: AcaoAuditoria | None = None,
    entidade_tipo: str | None = None,
    offset: int = 0,
    limite: int = LIMITE_PADRAO,
) -> tuple[list[RegistroAuditoria], int]:
    """RF-056: consulta paginada da trilha — usada tanto pela API quanto
    pela web, tanto na visão por-CPL quanto na visão global
    (`somente_global=True`, eventos sem CPL resolvível — login, criação de
    `Usuario`/`Pessoa`/`CPL` em si). Devolve `(registros da página, total
    de registros que batem com o filtro)`, pra dar pra montar "página X de
    Y" sem uma segunda ida ao banco."""

    query = db.query(RegistroAuditoria)
    if somente_global:
        query = query.filter(RegistroAuditoria.cpl_id.is_(None))
    elif cpl_id is not None:
        query = query.filter(RegistroAuditoria.cpl_id == cpl_id)
    if acao is not None:
        query = query.filter(RegistroAuditoria.acao == acao)
    if entidade_tipo:
        query = query.filter(RegistroAuditoria.entidade_tipo == entidade_tipo)

    total = query.count()
    registros = (
        query.order_by(RegistroAuditoria.created_at.desc())
        .offset(max(offset, 0))
        .limit(min(limite, LIMITE_MAXIMO))
        .all()
    )
    return registros, total


def registrar_evento(
    db: Session,
    *,
    usuario_id: uuid.UUID | None,
    acao: AcaoAuditoria,
    entidade_tipo: str,
    entidade_id: uuid.UUID | None = None,
    cpl_id: uuid.UUID | None = None,
    descricao: str | None = None,
) -> None:
    """Para eventos que RNF-003 exige rastrear (autenticação, download) mas
    que não correspondem a uma escrita de linha capturável pelo listener
    automático acima — por isso são registrados explicitamente."""

    db.add(
        RegistroAuditoria(
            usuario_id=usuario_id,
            acao=acao,
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            cpl_id=cpl_id,
            descricao=descricao,
            ip_address=ip_atual.get(),
        )
    )
