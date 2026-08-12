"""RF-012: envio automático do convite de campanha de atualização
cadastral — até aqui, `CampanhaConvite` só gerava um link/token pra a
gestão copiar e compartilhar manualmente (mesmo padrão do "convite" de
F01/adesão), mas nunca enviava e-mail nenhum, apesar da UI já usar um
ícone de envelope. Achado investigando um relato real de "empresa não
recebeu o e-mail da campanha" — o SMTP já está configurado em produção
(RF-004, recuperação de senha), só faltava alguém chamar `enviar_email`
neste fluxo.

Pra quem enviar: `Entidade` não tem e-mail próprio historicamente (só
`Pessoa.email`, via `PessoaVinculo`) — ganhou um campo `email` dedicado
"de comunicações" nesta mesma fatia. Os dois são somados como
destinatários (deduplicados): o e-mail da própria entidade, se
cadastrado, mais o e-mail de cada pessoa com vínculo vigente com ela
(`data_fim` nulo ou no futuro)."""

from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.cadastro_dinamico import CampanhaCadastral, CampanhaConvite
from app.models.entidade import Entidade
from app.models.pessoa import Pessoa, PessoaVinculo
from app.services.email import enviar_email


def contatos_da_entidade(db: Session, entidade: Entidade) -> list[str]:
    """E-mails pra quem uma comunicação sobre esta entidade deveria ir —
    o e-mail de comunicações dela, se cadastrado, mais o de cada pessoa
    com vínculo vigente, sem repetir endereço."""

    emails: list[str] = []
    if entidade.email:
        emails.append(entidade.email)

    hoje = date.today()
    vinculos = (
        db.query(PessoaVinculo)
        .join(Pessoa, Pessoa.id == PessoaVinculo.pessoa_id)
        .filter(
            PessoaVinculo.entidade_id == entidade.id,
            Pessoa.email.is_not(None),
            (PessoaVinculo.data_fim.is_(None)) | (PessoaVinculo.data_fim >= hoje),
        )
        .all()
    )
    for vinculo in vinculos:
        if vinculo.pessoa.email and vinculo.pessoa.email not in emails:
            emails.append(vinculo.pessoa.email)
    return emails


def enviar_convite_email(
    db: Session, campanha: CampanhaCadastral, convite: CampanhaConvite
) -> CampanhaConvite:
    """Resolve os destinatários e envia — grava o resultado no próprio
    `convite` (enviado ou não, pra quem, e o erro se algo falhou), sempre
    fazendo commit, nunca levanta exceção pra quem chama: um SMTP fora do
    ar não pode impedir a criação do convite, que continua útil pelo link
    copiável mesmo sem e-mail nenhum saindo."""

    destinatarios = contatos_da_entidade(db, convite.entidade)
    if not destinatarios:
        db.commit()
        db.refresh(convite)
        return convite

    settings = get_settings()
    link = f"{settings.app_base_url}/atualizacao/{convite.token}"
    assunto = f"Atualização cadastral — {campanha.titulo}"
    corpo = (
        f"Olá,\n\n"
        f'A gestão da cadeia produtiva local convida "{convite.entidade.razao_social}" a participar '
        f'da campanha "{campanha.titulo}".\n\n'
        "Preencha ou atualize os dados da sua empresa pelo link abaixo — não é necessário login, "
        f"leva poucos minutos:\n{link}\n\n"
        "Se os dados já estiverem atualizados, pode ignorar este e-mail."
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

    convite.email_enviado = len(enviados) > 0
    convite.email_enviado_em = datetime.now(UTC) if enviados else None
    convite.email_destinatarios = enviados or None
    convite.email_erro = erro
    db.commit()
    db.refresh(convite)
    return convite
