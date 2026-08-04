import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import Papel
from app.models.governanca import MembroOrgao
from app.models.usuario import Usuario, UsuarioPapel

# RF-005: controle de acesso por papéis, escopado a CPL/entidade. Os grupos
# abaixo traduzem as responsabilidades da seção 6 do documento em conjuntos
# de papéis usados nos endpoints — é uma simplificação deliberada (o
# documento descreve responsabilidades, não uma matriz CRUD estrita), então
# revise antes de considerar definitiva.

PAPEIS_GESTAO = {
    Papel.ADMINISTRADOR_PLATAFORMA,
    Papel.ENTIDADE_GESTORA,
    Papel.DIRIGENTE_ENTIDADE_GESTORA,
}
"""Ações administrativas: criar/configurar CPL, cadastro, órgãos, convocar
reuniões, registrar presença, encerrar com ata, concluir deliberações."""

PAPEIS_GOVERNANCA_LEITURA = PAPEIS_GESTAO | {
    Papel.CONSELHO_COMITE,
    Papel.COMISSAO_TEMATICA,
    Papel.AUDITORIA_CONTROLE,
}
"""Quem pode ler órgãos/reuniões/deliberações/votos/tarefas de uma CPL.
Deliberadamente não inclui EMPRESA_MEMBRO nem INSTITUICAO_ENSINO_ICT_SPAI —
governança fica visível só a quem participa dela ou audita."""

PAPEIS_GOVERNANCA_PARTICIPACAO = PAPEIS_GESTAO | {Papel.CONSELHO_COMITE}
"""Quem pode deliberar e votar (além de quem organiza/administra)."""

PAPEIS_TAREFA_EXECUCAO = PAPEIS_GESTAO | {Papel.COMISSAO_TEMATICA, Papel.GESTOR_PROJETO}
"""Quem pode atualizar status de tarefas — além do responsável pessoal
pela tarefa específica, tratado à parte nos endpoints (não é papel, é
vínculo direto Usuario.pessoa_id == tarefa.responsavel_id)."""

PAPEIS_IMPEDIMENTO_LEITURA = PAPEIS_GESTAO | {Papel.AUDITORIA_CONTROLE}
"""Declarações de impedimento são dado sensível (RN-014) — leitura mais
restrita que o resto da governança; conselho/comissão não veem por padrão."""

PAPEIS_EDITAL_GESTAO = {Papel.ADMINISTRADOR_PLATAFORMA}
"""RF-024/RN-006 e RF-029: edital de maturidade e edital de fomento (dois
conceitos distintos que compartilham o nome, ver `EditalFomento`) são
configuração compartilhada do Programa SP Produz, não algo que cada CPL
cria pra si — só administrador da plataforma gerencia (chamado com
cpl_id=None, já que não há CPL nenhuma envolvida em criar/editar um
edital). RF-030 reaproveita o mesmo grupo pra decidir recursos/
contrarrazões/diligências, mesmo raciocínio do RF-027 (`RecursoAvaliacao`):
decisão é de quem administra o edital, autoridade diferente de quem gere
o projeto que solicitou."""

PAPEIS_AVALIACAO_EXECUCAO = PAPEIS_GESTAO | {Papel.ANALISTA_AVALIADOR}
"""RF-024/025: quem conduz uma avaliação de maturidade — lança nota e
evidência por critério. Concluir a avaliação (calcula nível sugerido) usa
o mesmo grupo; **decidir** o nível final que atualiza `CPL.nivel_maturidade`
é sempre `PAPEIS_GESTAO` (RN-016: decisão humana e mais restrita que
"quem avalia")."""

PAPEIS_PROJETO_LEITURA = PAPEIS_GOVERNANCA_LEITURA | {Papel.GESTOR_PROJETO}
"""RF-031/032: quem pode ler demandas e portfólio de projetos de uma
CPL — mesmo público de PAPEIS_GOVERNANCA_LEITURA, mais o papel
GESTOR_PROJETO (que não participa de órgãos de governança, mas gere
projetos)."""

PAPEIS_PROJETO_GESTAO = PAPEIS_GESTAO | {Papel.GESTOR_PROJETO}
"""RF-031/032: quem pode registrar demanda, converter em projeto e
atualizar o portfólio (estágio, prioridade, eixo, responsável, vínculo
ao planejamento) — mesmo padrão de PAPEIS_TAREFA_EXECUCAO."""


def papeis_do_usuario(db: Session, usuario: Usuario) -> list[UsuarioPapel]:
    return db.query(UsuarioPapel).filter(UsuarioPapel.usuario_id == usuario.id).all()


def existe_administrador(db: Session) -> bool:
    return (
        db.query(UsuarioPapel).filter(UsuarioPapel.papel == Papel.ADMINISTRADOR_PLATAFORMA).first()
        is not None
    )


def cpl_ids_visiveis(db: Session, usuario: Usuario) -> set[uuid.UUID] | None:
    """Retorna o conjunto de `cpl_id` que o usuário pode enxergar (qualquer
    papel em PAPEIS_GOVERNANCA_LEITURA), ou None se ele for administrador
    da plataforma — nesse caso, todas as CPLs são visíveis."""

    vinculos = papeis_do_usuario(db, usuario)
    if any(v.papel == Papel.ADMINISTRADOR_PLATAFORMA for v in vinculos):
        return None
    return {v.cpl_id for v in vinculos if v.papel in PAPEIS_GOVERNANCA_LEITURA and v.cpl_id is not None}


def verificar_papel(
    db: Session,
    usuario: Usuario,
    papeis_permitidos: set[Papel],
    cpl_id: uuid.UUID | None = None,
) -> None:
    """Levanta 403 se o usuário não tiver nenhum papel permitido.

    Quando `cpl_id` é informado, um `UsuarioPapel` só conta se for global
    (seu `cpl_id` é nulo — caso de ADMINISTRADOR_PLATAFORMA) ou se bater
    com o `cpl_id` do recurso acessado. Quando `cpl_id` é None, qualquer
    `UsuarioPapel` com o papel exigido conta — usado para recursos que
    ainda não carregam uma CPL própria no modelo atual (Entidade, Pessoa).
    """

    for vinculo in papeis_do_usuario(db, usuario):
        if vinculo.papel not in papeis_permitidos:
            continue
        if cpl_id is None or vinculo.cpl_id is None or vinculo.cpl_id == cpl_id:
            return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem papel autorizado para esta ação.")


def usuario_e_membro_orgao(db: Session, usuario: Usuario, orgao_id: uuid.UUID) -> bool:
    if usuario.pessoa_id is None:
        return False
    return (
        db.query(MembroOrgao)
        .filter(
            MembroOrgao.orgao_id == orgao_id,
            MembroOrgao.pessoa_id == usuario.pessoa_id,
            MembroOrgao.ativo.is_(True),
        )
        .first()
        is not None
    )


def verificar_participacao_orgao(
    db: Session, usuario: Usuario, orgao_id: uuid.UUID, cpl_id: uuid.UUID
) -> None:
    """RF-005 menciona escopo por "comissão" — até aqui, `PAPEIS_GOVERNANCA_
    PARTICIPACAO` só escopava por CPL: um `CONSELHO_COMITE` de uma CPL podia
    votar/deliberar em QUALQUER órgão dessa CPL, não só no(s) que integra de
    fato. Aqui, quem tem papel de gestão continua podendo agir em qualquer
    órgão da CPL (é administrativo); `CONSELHO_COMITE` (ou qualquer papel
    fora de `PAPEIS_GESTAO`) só passa se for `MembroOrgao` ativo do órgão
    específico — `MembroOrgao` já existia desde a Governança, só não estava
    ligado ao RBAC ainda."""

    if usuario_e_membro_orgao(db, usuario, orgao_id):
        return
    verificar_papel(db, usuario, PAPEIS_GESTAO, cpl_id=cpl_id)
