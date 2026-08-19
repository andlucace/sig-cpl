"""RF-017: envio automático de e-mail de convocação de reunião para
todos os membros ativos do órgão — pedido explícito. Mesmo padrão
resiliente já usado em `app/services/campanhas.py::enviar_convite_email`
(nunca bloqueia a ação principal se o SMTP falhar; registra o resultado
na própria linha, pra quem convocou conseguir ver depois se o e-mail
saiu de verdade)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.governanca import MembroOrgao, Reuniao
from app.services.email import enviar_email


def contatos_do_orgao(db: Session, orgao_id: uuid.UUID) -> list[str]:
    """E-mail de cada membro ativo do órgão, sem repetir endereço."""

    membros = (
        db.query(MembroOrgao).filter(MembroOrgao.orgao_id == orgao_id, MembroOrgao.ativo.is_(True)).all()
    )
    emails: list[str] = []
    for membro in membros:
        if membro.pessoa.email and membro.pessoa.email not in emails:
            emails.append(membro.pessoa.email)
    return emails


def enviar_convocacao_email(db: Session, reuniao: Reuniao) -> Reuniao:
    """Resolve os destinatários (membros ativos do órgão) e envia — grava
    o resultado na própria `reuniao`, sempre fazendo commit, nunca
    levanta exceção pra quem chama: um SMTP fora do ar não pode impedir a
    convocação, que já existe e vale independente do e-mail sair."""

    destinatarios = contatos_do_orgao(db, reuniao.orgao_id)
    if not destinatarios:
        db.commit()
        db.refresh(reuniao)
        return reuniao

    settings = get_settings()
    link = f"{settings.app_base_url}/painel/governanca/reunioes/{reuniao.id}"
    assunto = f"Convocação de reunião — {reuniao.titulo}"
    corpo = (
        f"Olá,\n\n"
        f'Você foi convocado(a) para a reunião "{reuniao.titulo}" do órgão '
        f'"{reuniao.orgao.nome}".\n\n'
        f"Data e hora: {reuniao.data_hora.strftime('%d/%m/%Y %H:%M')}\n"
        + (f"Local: {reuniao.local}\n" if reuniao.local else "")
        + (f"\nPauta:\n{reuniao.pauta}\n" if reuniao.pauta else "")
        + f"\nMais detalhes no sistema: {link}"
    )

    enviados: list[str] = []
    erro: str | None = None
    for destinatario in destinatarios:
        try:
            enviar_email(destinatario, assunto, corpo)
        except (RuntimeError, OSError) as exc:
            erro = str(exc)
            break
        enviados.append(destinatario)

    reuniao.email_convocacao_enviado = len(enviados) > 0
    reuniao.email_convocacao_enviado_em = datetime.now(UTC) if enviados else None
    reuniao.email_convocacao_destinatarios = enviados or None
    reuniao.email_convocacao_erro = erro
    db.commit()
    db.refresh(reuniao)
    return reuniao
