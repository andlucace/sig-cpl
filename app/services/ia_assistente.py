"""RF-057: apoio de IA para síntese, verificação de consistência e
sugestão de lacunas sobre os indicadores agregados de uma CPL — sempre
com revisão humana obrigatória, exatamente como o requisito exige. O
resultado nunca é persistido nem aplicado a nada automaticamente: é só
apresentado como sugestão de texto na tela de indicadores, pra quem já
tem papel de gestão ler e decidir o que fazer com ele.

Este requisito era declaradamente "evolução futura" no documento
original porque depende de uma decisão de negócio (qual provedor de IA,
custo por chamada) que só o usuário podia tomar — mesma natureza da
pendência de assinatura eletrônica do RF-054. Provedor escolhido:
Anthropic (Claude). Sem `ANTHROPIC_API_KEY` configurada, `ia_disponivel()`
retorna `False` e `gerar_assistente_ia()` levanta `IAIndisponivel` — mesmo
padrão de degradação graciosa já usado pro SMTP (RF-004): a ausência da
credencial não impede o resto do sistema de funcionar, só desativa esta
funcionalidade até a chave existir.

O contexto enviado ao modelo é uma curadoria manual dos mesmos agregados
já usados no dashboard de indicadores (RF-045) — nunca a lista de
objetos (`avaliacoes`, `projetos`) nem qualquer dado de pessoa, mesmo
cuidado de anonimização já estabelecido no portal público (RF-055)."""

import json
from collections import Counter
from datetime import date
from decimal import Decimal
from enum import Enum

import anthropic

from app.core.config import get_settings


class IAIndisponivel(Exception):
    pass


def ia_disponivel() -> bool:
    return bool(get_settings().anthropic_api_key)


def _serializavel(valor):
    if isinstance(valor, Enum):
        return valor.value
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, Counter):
        return {str(chave): quantidade for chave, quantidade in valor.items()}
    if isinstance(valor, dict):
        return {str(chave): _serializavel(item) for chave, item in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_serializavel(item) for item in valor]
    return valor


def _contexto_cpl(
    cpl, cadastral: dict, governanca: dict, planejamento: dict, projetos_resumo: dict, maturidade: dict
) -> dict:
    """Curadoria manual dos campos escalares/agregados já existentes nos
    dashboards (RF-045) — só o que já é seguro o bastante pro portal
    público (RF-055), nunca lista de objetos nem dado de pessoa."""

    return {
        "cpl": {
            "nome": cpl.nome,
            "sigla": cpl.sigla,
            "setor": cpl.setor,
            "municipio": cpl.municipio,
            "uf": cpl.uf,
            "nivel_maturidade": cpl.nivel_maturidade.value if cpl.nivel_maturidade else None,
        },
        "cadastral": _serializavel(cadastral),
        "governanca": _serializavel(governanca),
        "planejamento": _serializavel(planejamento),
        "projetos": {
            "total_projetos": projetos_resumo["total_projetos"],
            "por_estagio": _serializavel(projetos_resumo["por_estagio"]),
            "por_prioridade": _serializavel(projetos_resumo["por_prioridade"]),
            "total_previsto": float(projetos_resumo["total_previsto"]),
            "total_desembolsado": float(projetos_resumo["total_desembolsado"]),
            "total_etapas": projetos_resumo["total_etapas"],
            "etapas_concluidas": projetos_resumo["etapas_concluidas"],
            "riscos_ativos": projetos_resumo["riscos_ativos"],
        },
        "maturidade": {
            "nivel_maturidade_atual": (
                maturidade["nivel_maturidade_atual"].value if maturidade["nivel_maturidade_atual"] else None
            ),
            "dias_para_vencer": maturidade["dias_para_vencer"],
            # `lacunas_avaliacao_vigente` é uma lista de `AvaliacaoCriterio`
            # (objeto ORM, não serializável em JSON) — mesmo texto que o
            # dashboard já renderiza em `cpl_dashboard.html`.
            "lacunas_avaliacao_vigente": [
                f"{nota.criterio.nome}: nota {nota.nota} (corte: {nota.criterio.nota_corte})"
                for nota in maturidade["lacunas_avaliacao_vigente"]
            ],
        },
    }


_PROMPT_SISTEMA = """Você é um assistente de apoio à gestão de Cadeias Produtivas Locais \
(CPLs) do Programa SP Produz, do governo do Estado de São Paulo.

Analise os dados agregados fornecidos pelo usuário e responda ESTRITAMENTE em \
JSON, sem nenhum texto fora do JSON, neste formato exato:
{"sintese": "um parágrafo em português", \
"verificacao_consistencia": ["item 1", "item 2"], \
"lacunas_sugeridas": ["item 1", "item 2"]}

"sintese": resume o estado atual da CPL em linguagem clara para um gestor público.
"verificacao_consistencia": aponta possíveis contradições ou sinais de atenção nos \
números fornecidos (ex.: nível de maturidade alto mas poucos órgãos ativos). Lista \
vazia se nada chamar atenção.
"lacunas_sugeridas": lacunas ou próximos passos que os dados não cobrem, além das já \
listadas em "maturidade.lacunas_avaliacao_vigente" (não repita essas).

Nunca invente números que não estejam nos dados fornecidos. Suas sugestões são um \
rascunho para revisão humana — nunca uma decisão automática."""


def _sem_cerca_markdown(texto: str) -> str:
    """Modelos frequentemente envolvem JSON em cerca de código markdown
    (```json ... ```) mesmo quando instruídos a não fazer isso — remove
    a cerca se presente, sem exigir que o modelo acerte o formato exato
    toda vez."""

    texto = texto.strip()
    if texto.startswith("```"):
        texto = texto.removeprefix("```json").removeprefix("```").strip()
        texto = texto.removesuffix("```").strip()
    return texto


def gerar_assistente_ia(
    cpl, cadastral: dict, governanca: dict, planejamento: dict, projetos_resumo: dict, maturidade: dict
) -> dict:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise IAIndisponivel("Assistente de IA não configurado (ANTHROPIC_API_KEY ausente).")

    contexto = _contexto_cpl(cpl, cadastral, governanca, planejamento, projetos_resumo, maturidade)
    try:
        cliente = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        resposta = cliente.messages.create(
            model=settings.anthropic_model,
            max_tokens=1500,
            system=_PROMPT_SISTEMA,
            messages=[{"role": "user", "content": json.dumps(contexto, ensure_ascii=False)}],
            # Síntese/JSON estruturado não precisa de raciocínio estendido —
            # desligar evita que o modelo gaste o orçamento de tokens todo
            # "pensando" e não sobre nada pro texto de resposta em si
            # (foi exatamente isso que quebrou em produção antes deste ajuste).
            thinking={"type": "disabled"},
        )
        # `resposta.content[0]` nem sempre é o bloco de texto — modelos com
        # extended thinking habilitado antepõem um `ThinkingBlock` (sem
        # atributo `.text`) antes do `TextBlock` de verdade.
        bloco_texto = next((bloco for bloco in resposta.content if bloco.type == "text"), None)
        if bloco_texto is None:
            raise IAIndisponivel("Assistente de IA não retornou texto.")
        texto = bloco_texto.text
    except anthropic.APIError as exc:
        # Mensagem curta de propósito — `str(exc)` inclui o corpo bruto da
        # resposta da API (pode conter detalhe técnico irrelevante pra quem
        # só quer saber que a função está indisponível agora).
        raise IAIndisponivel("Assistente de IA indisponível no momento.") from exc

    try:
        resultado = json.loads(_sem_cerca_markdown(texto))
    except json.JSONDecodeError as exc:
        raise IAIndisponivel("Assistente de IA retornou uma resposta em formato inesperado.") from exc

    return {
        "sintese": resultado.get("sintese", ""),
        "verificacao_consistencia": resultado.get("verificacao_consistencia", []),
        "lacunas_sugeridas": resultado.get("lacunas_sugeridas", []),
    }
