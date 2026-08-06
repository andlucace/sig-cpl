"""RNF-012: logs centralizados — uma linha JSON por evento em vez de
texto solto, pra ficar filtrável/agregável em qualquer coletor que leia
stdout do container (Docker já centraliza a coleta; isto só torna o
conteúdo estruturado, sem exigir um agente de log novo). Coexiste com o
access log padrão do uvicorn, que continua útil pra leitura humana
durante debug — não foi desligado."""

import json
import logging
import sys

_CAMPOS_EXTRAS = ("request_id", "usuario_id", "metodo", "rota", "status_code", "duracao_ms")


class _FormatadorJSON(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "nivel": record.levelname,
            "logger": record.name,
            "mensagem": record.getMessage(),
        }
        for campo in _CAMPOS_EXTRAS:
            valor = getattr(record, campo, None)
            if valor is not None:
                payload[campo] = valor
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configurar_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_FormatadorJSON())

    logger = logging.getLogger("sigcpl")
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]
    logger.propagate = False
