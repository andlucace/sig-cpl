"""RF-049: notificações automáticas de prazos e pendências — reunião
próxima, tarefa com prazo vencendo, documento perdendo validade, meta
com prazo vencendo e reconhecimento de CPL vencendo. Não introduz
nenhuma coleta de dado nova: cada fonte já existe em outro módulo, esta
camada só varre o que já está no banco e materializa uma `Notificacao`
por (usuário, tipo, entidade) — no máximo uma vez cada (ver `_notificar`).

Não há agendador/worker neste stack (sem Celery/cron) — `gerar_notificacoes()`
é chamada sob demanda, sempre que a tela/endpoint de notificações é
acessado (ver `app/web/routes_notificacoes.py`), então a lista nunca fica
muito desatualizada sem precisar de infraestrutura nova."""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.documento import Documento
from app.models.enums import Papel, StatusReuniao, StatusTarefa, TipoNotificacao
from app.models.governanca import MembroOrgao, Reuniao, TarefaGovernanca
from app.models.notificacao import Notificacao
from app.models.planejamento import MetaEstrategica, ObjetivoEstrategico, PlanejamentoEstrategico
from app.models.usuario import Usuario, UsuarioPapel
from app.services.maturidade import cpls_com_vencimento_proximo

JANELA_PADRAO_DIAS = 7


def _notificar(
    db: Session,
    *,
    usuario_id: uuid.UUID,
    tipo: TipoNotificacao,
    entidade_tipo: str,
    entidade_id: uuid.UUID,
    titulo: str,
    mensagem: str | None,
    cpl_id: uuid.UUID | None,
) -> bool:
    """Cria a notificação se ainda não existe uma igual (mesmo usuário +
    tipo + entidade) — garante no máximo um aviso por evento, em vez de
    reavisar a cada chamada de `gerar_notificacoes()`. Devolve True se
    criou."""

    ja_existe = (
        db.query(Notificacao)
        .filter(
            Notificacao.usuario_id == usuario_id,
            Notificacao.tipo == tipo,
            Notificacao.entidade_id == entidade_id,
        )
        .first()
    )
    if ja_existe:
        return False
    db.add(
        Notificacao(
            usuario_id=usuario_id,
            cpl_id=cpl_id,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
        )
    )
    return True


def _usuario_de_pessoa(db: Session, pessoa_id: uuid.UUID | None) -> Usuario | None:
    if pessoa_id is None:
        return None
    return db.query(Usuario).filter(Usuario.pessoa_id == pessoa_id, Usuario.ativo.is_(True)).first()


def _gerar_reunioes_proximas(db: Session, limite: datetime) -> int:
    agora = datetime.now(UTC)
    reunioes = (
        db.query(Reuniao)
        .filter(
            Reuniao.status == StatusReuniao.AGENDADA,
            Reuniao.data_hora >= agora,
            Reuniao.data_hora <= limite,
        )
        .all()
    )
    criadas = 0
    for reuniao in reunioes:
        orgao = reuniao.orgao
        membros = (
            db.query(MembroOrgao)
            .filter(
                MembroOrgao.orgao_id == orgao.id,
                MembroOrgao.ativo.is_(True),
            )
            .all()
        )
        for membro in membros:
            usuario = _usuario_de_pessoa(db, membro.pessoa_id)
            if usuario is None:
                continue
            if _notificar(
                db,
                usuario_id=usuario.id,
                tipo=TipoNotificacao.REUNIAO_PROXIMA,
                entidade_tipo="Reuniao",
                entidade_id=reuniao.id,
                titulo=f"Reunião próxima: {reuniao.titulo}",
                mensagem=f"{orgao.nome} — {reuniao.data_hora.strftime('%d/%m/%Y %H:%M')}",
                cpl_id=orgao.cpl_id,
            ):
                criadas += 1
    return criadas


def _gerar_tarefas_com_prazo(db: Session, limite: date) -> int:
    tarefas = (
        db.query(TarefaGovernanca)
        .filter(
            TarefaGovernanca.status.notin_([StatusTarefa.CONCLUIDA, StatusTarefa.CANCELADA]),
            TarefaGovernanca.prazo.is_not(None),
            TarefaGovernanca.prazo <= limite,
            TarefaGovernanca.responsavel_id.is_not(None),
        )
        .all()
    )
    criadas = 0
    for tarefa in tarefas:
        usuario = _usuario_de_pessoa(db, tarefa.responsavel_id)
        if usuario is None:
            continue
        vencida = tarefa.prazo < date.today()
        if _notificar(
            db,
            usuario_id=usuario.id,
            tipo=TipoNotificacao.TAREFA_PRAZO,
            entidade_tipo="TarefaGovernanca",
            entidade_id=tarefa.id,
            titulo=f"Tarefa {'vencida' if vencida else 'com prazo próximo'}: {tarefa.titulo}",
            mensagem=f"Prazo: {tarefa.prazo.strftime('%d/%m/%Y')}",
            cpl_id=tarefa.cpl_id,
        ):
            criadas += 1
    return criadas


def _gerar_documentos_com_validade(db: Session, limite: date) -> int:
    documentos = (
        db.query(Documento)
        .filter(Documento.data_validade.is_not(None), Documento.data_validade <= limite)
        .all()
    )
    criadas = 0
    for documento in documentos:
        vencido = documento.data_validade < date.today()
        if _notificar(
            db,
            usuario_id=documento.criado_por_id,
            tipo=TipoNotificacao.DOCUMENTO_VALIDADE,
            entidade_tipo="Documento",
            entidade_id=documento.id,
            titulo=f"Documento {'vencido' if vencido else 'perdendo validade'}: {documento.titulo}",
            mensagem=f"Validade: {documento.data_validade.strftime('%d/%m/%Y')}",
            cpl_id=documento.cpl_id,
        ):
            criadas += 1
    return criadas


def _gerar_metas_com_prazo(db: Session, limite: date) -> int:
    metas = (
        db.query(MetaEstrategica)
        .join(ObjetivoEstrategico, MetaEstrategica.objetivo_id == ObjetivoEstrategico.id)
        .join(PlanejamentoEstrategico, ObjetivoEstrategico.planejamento_id == PlanejamentoEstrategico.id)
        .filter(
            MetaEstrategica.status.notin_([StatusTarefa.CONCLUIDA, StatusTarefa.CANCELADA]),
            MetaEstrategica.prazo.is_not(None),
            MetaEstrategica.prazo <= limite,
            MetaEstrategica.responsavel_id.is_not(None),
        )
        .add_columns(PlanejamentoEstrategico.cpl_id)
        .all()
    )
    criadas = 0
    for meta, cpl_id in metas:
        usuario = _usuario_de_pessoa(db, meta.responsavel_id)
        if usuario is None:
            continue
        vencida = meta.prazo < date.today()
        if _notificar(
            db,
            usuario_id=usuario.id,
            tipo=TipoNotificacao.META_PRAZO,
            entidade_tipo="MetaEstrategica",
            entidade_id=meta.id,
            titulo=f"Meta {'vencida' if vencida else 'com prazo próximo'}: {meta.descricao[:100]}",
            mensagem=f"Prazo: {meta.prazo.strftime('%d/%m/%Y')}",
            cpl_id=cpl_id,
        ):
            criadas += 1
    return criadas


def _gerar_recadastramentos_proximos(db: Session) -> int:
    """RF-028/RN-005: usa a mesma janela de 90 dias já estabelecida em
    `cpls_com_vencimento_proximo` (recadastramento bienal, alerta com
    bem mais antecedência que os outros tipos) — não a janela curta de
    `janela_dias` usada pelos outros 4 tipos de notificação, que é
    pensada para prazos operacionais de poucos dias."""

    cpls = cpls_com_vencimento_proximo(db)
    if not cpls:
        return 0
    admins = (
        db.query(Usuario)
        .join(UsuarioPapel, UsuarioPapel.usuario_id == Usuario.id)
        .filter(UsuarioPapel.papel == Papel.ADMINISTRADOR_PLATAFORMA, Usuario.ativo.is_(True))
        .all()
    )
    criadas = 0
    for cpl in cpls:
        vencido = cpl.data_validade_reconhecimento < date.today()
        for admin in admins:
            if _notificar(
                db,
                usuario_id=admin.id,
                tipo=TipoNotificacao.RECADASTRAMENTO_CPL,
                entidade_tipo="CPL",
                entidade_id=cpl.id,
                titulo=f"Recadastramento {'vencido' if vencido else 'próximo'}: {cpl.nome}",
                mensagem=f"Validade do reconhecimento: {cpl.data_validade_reconhecimento.strftime('%d/%m/%Y')}",
                cpl_id=cpl.id,
            ):
                criadas += 1
    return criadas


def gerar_notificacoes(db: Session, janela_dias: int = JANELA_PADRAO_DIAS) -> int:
    """Varre as 5 fontes de RF-049 e materializa notificações novas.
    Idempotente (ver `_notificar`) — chamar de novo não duplica avisos já
    gerados. Devolve quantas notificações novas foram criadas."""

    limite_data = date.today() + timedelta(days=janela_dias)
    limite_datahora = datetime.now(UTC) + timedelta(days=janela_dias)

    total = 0
    total += _gerar_reunioes_proximas(db, limite_datahora)
    total += _gerar_tarefas_com_prazo(db, limite_data)
    total += _gerar_documentos_com_validade(db, limite_data)
    total += _gerar_metas_com_prazo(db, limite_data)
    total += _gerar_recadastramentos_proximos(db)
    db.commit()
    return total


def listar_notificacoes(db: Session, usuario_id: uuid.UUID, somente_nao_lidas: bool = False) -> list[Notificacao]:
    query = db.query(Notificacao).filter(Notificacao.usuario_id == usuario_id)
    if somente_nao_lidas:
        query = query.filter(Notificacao.lida.is_(False))
    return query.order_by(Notificacao.created_at.desc()).all()


def contar_nao_lidas(db: Session, usuario_id: uuid.UUID) -> int:
    return db.query(Notificacao).filter(Notificacao.usuario_id == usuario_id, Notificacao.lida.is_(False)).count()


def marcar_como_lida(db: Session, notificacao: Notificacao) -> None:
    notificacao.lida = True
    notificacao.lida_em = datetime.now(UTC)
    db.commit()


def marcar_todas_como_lidas(db: Session, usuario_id: uuid.UUID) -> int:
    agora = datetime.now(UTC)
    atualizadas = (
        db.query(Notificacao)
        .filter(Notificacao.usuario_id == usuario_id, Notificacao.lida.is_(False))
        .update({"lida": True, "lida_em": agora})
    )
    db.commit()
    return atualizadas
