"""RF-054: integração com dados cadastrais públicos — consulta de CNPJ
via BrasilAPI (https://brasilapi.com.br), pública, gratuita e sem
necessidade de credencial, "tecnicamente disponível" sem depender de
contrato nenhum — diferente de assinatura eletrônica, BI e "sistemas
institucionais" (os outros três citados pelo requisito), que dependem
de um provedor contratado específico e ficam documentados como
pendência de configuração, não de código (mesma natureza do SMTP do
RF-004, ver HANDOFF.md).

Sem dependência nova: usa `urllib.request` (biblioteca padrão) em vez de
adicionar `httpx`/`requests` só pra uma chamada HTTP simples — as rotas
que chamam esta função são síncronas (`def`, não `async def`), então o
FastAPI já roda numa threadpool, mesmo padrão de toda chamada bloqueante
já existente no projeto (psycopg síncrono, SMTP síncrono)."""

import json
import urllib.error
import urllib.request

BRASILAPI_CNPJ_URL = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"


class ConsultaCNPJIndisponivel(Exception):
    pass


def consultar_cnpj_publico(cnpj: str) -> dict:
    cnpj_limpo = "".join(c for c in cnpj if c.isdigit())
    if len(cnpj_limpo) != 14:
        raise ValueError("CNPJ deve ter 14 dígitos.")

    url = BRASILAPI_CNPJ_URL.format(cnpj=cnpj_limpo)
    # BrasilAPI devolve 403 pro User-Agent padrão do urllib (bloqueio
    # anti-bot genérico) — não é falta de autorização de verdade, só
    # precisa de um User-Agent identificável.
    requisicao = urllib.request.Request(url, headers={"User-Agent": "SIG-CPL/1.0 (contato via sistema)"})
    try:
        with urllib.request.urlopen(requisicao, timeout=10) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ConsultaCNPJIndisponivel("CNPJ não encontrado na base pública.") from exc
        raise ConsultaCNPJIndisponivel(f"Consulta pública indisponível (HTTP {exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ConsultaCNPJIndisponivel("Consulta pública indisponível no momento.") from exc

    endereco_partes = [
        dados.get("descricao_tipo_de_logradouro"),
        dados.get("logradouro"),
        dados.get("numero"),
        dados.get("bairro"),
    ]
    endereco = ", ".join(p for p in endereco_partes if p) or None

    return {
        "razao_social": dados.get("razao_social"),
        "nome_fantasia": dados.get("nome_fantasia") or None,
        "situacao_cadastral": dados.get("descricao_situacao_cadastral"),
        "data_situacao_cadastral": dados.get("data_situacao_cadastral"),
        "cnae": str(dados["cnae_fiscal"]) if dados.get("cnae_fiscal") is not None else None,
        "cnae_descricao": dados.get("cnae_fiscal_descricao"),
        "endereco": endereco,
        "municipio": dados.get("municipio"),
        "uf": dados.get("uf"),
        "telefone": dados.get("ddd_telefone_1") or None,
        "email": dados.get("email") or None,
    }
