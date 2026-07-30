import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import Papel
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
