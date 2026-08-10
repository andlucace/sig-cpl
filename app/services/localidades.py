"""Estados e municípios do Brasil pro formulário de CPL — Setor,
Município e UF viram listbox (Estado antes de Município, município
filtrado pelo estado escolhido). Fonte pública, gratuita, sem
credencial: API de Localidades do IBGE
(https://servicodados.ibge.gov.br/api/docs/localidades), mesmo
raciocínio "tecnicamente disponível sem contrato" já usado pra CNPJ
(RF-054, BrasilAPI) e geocodificação (RF-011, Nominatim).

Nada é persistido no banco — só cache em memória do processo
(`functools.lru_cache`), válido até o próximo deploy/restart. 27 UFs e
~5.570 municípios cabem folgado em memória (algumas centenas de KB no
total); criar tabela(s) pra isso seria peso desnecessário pra um dado
que já é público, estável e servido de graça. O próprio IBGE manda
`Cache-Control: max-age=2592000` (30 dias) nas respostas — cache em
memória pela vida do processo é bem mais conservador que isso.

**Gotcha real, diferente do de User-Agent já visto em BrasilAPI/
Nominatim**: o IBGE sempre devolve `Content-Encoding: gzip`, mesmo sem o
cliente pedir — `urllib.request` não descomprime automaticamente (só
`requests`/navegador fazem isso sozinhos), então ler a resposta crua
quebra com `UnicodeDecodeError` (byte inicial `\\x8b`, a assinatura
gzip). Descompactado manualmente com `gzip.decompress` antes do
`json.loads`.

UFs têm uma lista de reserva embutida (as 27 nunca mudam) pra não
travar o formulário de CPL inteiro se o IBGE cair; municípios não têm
reserva — se um estado falhar, o formulário só devolve lista vazia pra
aquele estado específico, sem quebrar o resto."""

import gzip
import json
import urllib.error
import urllib.request
from functools import lru_cache

IBGE_ESTADOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome"
IBGE_MUNICIPIOS_URL = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios?orderBy=nome"
)

_UFS_RESERVA = [
    ("AC", "Acre"), ("AL", "Alagoas"), ("AP", "Amapá"), ("AM", "Amazonas"),
    ("BA", "Bahia"), ("CE", "Ceará"), ("DF", "Distrito Federal"), ("ES", "Espírito Santo"),
    ("GO", "Goiás"), ("MA", "Maranhão"), ("MT", "Mato Grosso"), ("MS", "Mato Grosso do Sul"),
    ("MG", "Minas Gerais"), ("PA", "Pará"), ("PB", "Paraíba"), ("PR", "Paraná"),
    ("PE", "Pernambuco"), ("PI", "Piauí"), ("RJ", "Rio de Janeiro"), ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"), ("RO", "Rondônia"), ("RR", "Roraima"), ("SC", "Santa Catarina"),
    ("SP", "São Paulo"), ("SE", "Sergipe"), ("TO", "Tocantins"),
]  # fmt: skip


def _requisicao_json(url: str) -> list:
    requisicao = urllib.request.Request(url, headers={"User-Agent": "SIG-CPL/1.0 (contato via sistema)"})
    with urllib.request.urlopen(requisicao, timeout=10) as resposta:
        bruto = resposta.read()
        if resposta.headers.get("Content-Encoding") == "gzip":
            bruto = gzip.decompress(bruto)
        return json.loads(bruto.decode("utf-8"))


@lru_cache(maxsize=1)
def estados() -> list[tuple[str, str]]:
    """Lista de `(sigla, nome)` ordenada por nome — cacheada pra vida do
    processo, cai pra `_UFS_RESERVA` se o IBGE estiver indisponível."""

    try:
        dados = _requisicao_json(IBGE_ESTADOS_URL)
        return [(uf["sigla"], uf["nome"]) for uf in dados]
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
        return list(_UFS_RESERVA)


@lru_cache(maxsize=27)
def municipios_do_estado(uf: str) -> list[str]:
    """Nomes dos municípios de uma UF, ordenados — cacheado por UF pra
    vida do processo (só as 27 combinações possíveis existem)."""

    try:
        dados = _requisicao_json(IBGE_MUNICIPIOS_URL.format(uf=uf.upper()))
        return [municipio["nome"] for municipio in dados]
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
        return []
