import enum


class NivelMaturidade(str, enum.Enum):
    """RN-004: quatro níveis parametrizáveis pelo Programa SP Produz."""

    AGLOMERADO_PRODUTIVO = "aglomerado_produtivo"
    CPL_EM_DESENVOLVIMENTO = "cpl_em_desenvolvimento"
    CPL_CONSOLIDADA = "cpl_consolidada"
    CPL_MADURA = "cpl_madura"


class TipoEntidade(str, enum.Enum):
    """RF-006: tipos de ator cadastráveis na cadeia e no ecossistema de apoio."""

    EMPRESA = "empresa"
    ORGAO_PUBLICO = "orgao_publico"
    UNIVERSIDADE = "universidade"
    ICT = "ict"
    ASSOCIACAO = "associacao"
    PRESTADOR = "prestador"
    AMBIENTE_INOVACAO = "ambiente_inovacao"


class Elo(str, enum.Enum):
    """RF-009: elos da cadeia produtiva; um ator pode ocupar múltiplos elos."""

    INSUMOS = "insumos"
    PRODUCAO = "producao"
    TRANSFORMACAO = "transformacao"
    COMERCIALIZACAO_DISTRIBUICAO = "comercializacao_distribuicao"
    APOIO_INSTITUCIONAL = "apoio_institucional"


class Papel(str, enum.Enum):
    """Seção 6: perfis de acesso e responsabilidades previstos no documento."""

    ADMINISTRADOR_PLATAFORMA = "administrador_plataforma"
    ENTIDADE_GESTORA = "entidade_gestora"
    DIRIGENTE_ENTIDADE_GESTORA = "dirigente_entidade_gestora"
    CONSELHO_COMITE = "conselho_comite"
    COMISSAO_TEMATICA = "comissao_tematica"
    EMPRESA_MEMBRO = "empresa_membro"
    INSTITUICAO_ENSINO_ICT_SPAI = "instituicao_ensino_ict_spai"
    ANALISTA_AVALIADOR = "analista_avaliador"
    GESTOR_PROJETO = "gestor_projeto"
    AUDITORIA_CONTROLE = "auditoria_controle"
    PUBLICO_EXTERNO = "publico_externo"


class TipoOrgao(str, enum.Enum):
    """RF-016: conselhos, câmaras, grupos e comissões temáticas da governança."""

    CONSELHO = "conselho"
    CAMARA = "camara"
    COMISSAO_TEMATICA = "comissao_tematica"
    GRUPO_TRABALHO = "grupo_trabalho"


class StatusReuniao(str, enum.Enum):
    """RF-017: ciclo de vida de uma reunião convocada."""

    AGENDADA = "agendada"
    REALIZADA = "realizada"
    CANCELADA = "cancelada"


class ResultadoDeliberacao(str, enum.Enum):
    """RF-018: resultado registrado para uma deliberação após votação/quórum."""

    PENDENTE = "pendente"
    APROVADA = "aprovada"
    REJEITADA = "rejeitada"
    ADIADA = "adiada"
    SEM_QUORUM = "sem_quorum"


class TipoVoto(str, enum.Enum):
    """RF-018/RF-020: registro de voto, incluindo impedimento por conflito de interesses."""

    A_FAVOR = "a_favor"
    CONTRA = "contra"
    ABSTENCAO = "abstencao"
    IMPEDIDO = "impedido"


class StatusTarefa(str, enum.Enum):
    """RF-019: status de tarefas e planos de ação decorrentes de decisões.
    Reaproveitado também pelo módulo de Planejamento Estratégico (RF-023)
    para o status de objetivos/metas/iniciativas — mesmo ciclo de vida."""

    PENDENTE = "pendente"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    ATRASADA = "atrasada"
    CANCELADA = "cancelada"


class StatusPlanejamento(str, enum.Enum):
    """RF-021: ciclo de vida do Planejamento Estratégico de Negócios (PEN)."""

    RASCUNHO = "rascunho"
    EM_ELABORACAO = "em_elaboracao"
    APROVADO = "aprovado"


class TipoDiagnostico(str, enum.Enum):
    """RF-022: categorias do diagnóstico (SWOT + achados complementares)."""

    FORCA = "forca"
    FRAQUEZA = "fraqueza"
    OPORTUNIDADE = "oportunidade"
    AMEACA = "ameaca"
    PROBLEMA_PRIORITARIO = "problema_prioritario"
    DEMANDA = "demanda"
    LACUNA_ELO = "lacuna_elo"


class PrazoObjetivo(str, enum.Enum):
    """RF-023: horizonte temporal do objetivo estratégico."""

    CURTO = "curto"
    MEDIO = "medio"
    LONGO = "longo"


class StatusLinhaImportacao(str, enum.Enum):
    """RF-013: resultado do processamento de cada linha de uma planilha
    importada — dá a "trilha de origem" exigida pelo requisito."""

    CRIADA = "criada"
    ATUALIZADA = "atualizada"
    ERRO = "erro"


class CategoriaDocumento(str, enum.Enum):
    """RF-042: classificação do documento no repositório."""

    ATA = "ata"
    PLANO_TRABALHO = "plano_trabalho"
    DECLARACAO = "declaracao"
    COMPROVANTE = "comprovante"
    RELATORIO = "relatorio"
    OUTRO = "outro"


class ConfidencialidadeDocumento(str, enum.Enum):
    """RNF-002/RN-014: classificação de sigilo — controla quem pode ler o
    documento, além do papel de gestão que sempre pode."""

    PUBLICO = "publico"
    INTERNO = "interno"
    CONFIDENCIAL = "confidencial"


class AcaoAuditoria(str, enum.Enum):
    """RF-056/RNF-003: tipo de evento registrado na trilha de auditoria.
    CRIACAO/ATUALIZACAO/EXCLUSAO são capturados automaticamente por um
    listener de ORM (ver app/services/auditoria.py); os demais são
    eventos que não correspondem a uma escrita de linha rastreável pelo
    ORM e por isso são registrados explicitamente nos endpoints."""

    CRIACAO = "criacao"
    ATUALIZACAO = "atualizacao"
    EXCLUSAO = "exclusao"
    LOGIN_SUCESSO = "login_sucesso"
    LOGIN_FALHA = "login_falha"
    DOWNLOAD = "download"


class DimensaoMaturidade(str, enum.Enum):
    """Seção 10 (glossário do modelo conceitual): dimensões avaliadas por
    critério de maturidade — organização, governança, planejamento,
    dimensão (porte/escala), diversidade e impacto da CPL."""

    ORGANIZACAO = "organizacao"
    GOVERNANCA = "governanca"
    PLANEJAMENTO = "planejamento"
    DIMENSAO = "dimensao"
    DIVERSIDADE = "diversidade"
    IMPACTO = "impacto"


class StatusAvaliacao(str, enum.Enum):
    """RF-024/026: ciclo de vida de uma avaliação de maturidade de uma CPL
    contra um edital — separado do nível final decidido (RN-016: a decisão
    de nível é sempre humana, nunca automática ao concluir a avaliação)."""

    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"


class StatusRecurso(str, enum.Enum):
    """RF-027: status do recurso (contestação) contra o resultado de uma
    avaliação de maturidade."""

    PENDENTE = "pendente"
    DEFERIDO = "deferido"
    INDEFERIDO = "indeferido"


class StatusLoteImportacao(str, enum.Enum):
    """RF-013: ciclo de vida de um lote de importação de planilha — desde
    que o remapeamento manual de colunas existe, o upload não processa as
    linhas imediatamente; fica pendente até o usuário confirmar (ou
    ajustar) o mapeamento sugerido."""

    PENDENTE_MAPEAMENTO = "pendente_mapeamento"
    CONCLUIDO = "concluido"


class TipoNotificacao(str, enum.Enum):
    """RF-049: fontes de notificação automática — cada uma corresponde a
    um evento de prazo/pendência já modelado em outro módulo (nenhuma
    coleta de dado nova)."""

    REUNIAO_PROXIMA = "reuniao_proxima"
    TAREFA_PRAZO = "tarefa_prazo"
    DOCUMENTO_VALIDADE = "documento_validade"
    META_PRAZO = "meta_prazo"
    RECADASTRAMENTO_CPL = "recadastramento_cpl"


class OrigemDemanda(str, enum.Enum):
    """RF-031: de onde partiu a demanda coletiva/oportunidade de projeto —
    o requisito cita especificamente estas quatro fontes."""

    EMPRESA = "empresa"
    COMISSAO = "comissao"
    INSTITUICAO = "instituicao"
    EDITAL = "edital"


class StatusDemanda(str, enum.Enum):
    """RF-031: ciclo de vida de uma demanda até virar projeto (ou não)."""

    REGISTRADA = "registrada"
    EM_ANALISE = "em_analise"
    CONVERTIDA_EM_PROJETO = "convertida_em_projeto"
    REJEITADA = "rejeitada"


class EstagioProjeto(str, enum.Enum):
    """RF-032: estágio do projeto no portfólio. Ciclo de vida completo
    modelado de uma vez (evita migração nova quando RF-033 em diante
    forem construídos), mas esta primeira fatia do módulo só usa os
    estágios iniciais — não há ainda telas de execução/conclusão."""

    DEMANDA = "demanda"
    EM_ELABORACAO = "em_elaboracao"
    SUBMETIDO = "submetido"
    APROVADO = "aprovado"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDO = "concluido"
    REJEITADO = "rejeitado"
    CANCELADO = "cancelado"


class PrioridadeProjeto(str, enum.Enum):
    """RF-032: priorização do projeto no portfólio."""

    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
