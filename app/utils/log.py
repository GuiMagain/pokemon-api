import json
import logging
import os
import socket
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "pokemon-api",
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class LogstashTCPHandler(logging.Handler):
    """Envia cada log como uma linha JSON para o Logstash (entrada TCP)."""

    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self.address = (host, port)
        self._sock: socket.socket | None = None
        self.setFormatter(JsonFormatter())

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self._sock is None:
                self._sock = socket.create_connection(self.address, timeout=2)
            self._sock.sendall((self.format(record) + "\n").encode("utf-8"))
        except OSError:
            self._sock = None  # tenta reconectar na próxima mensagem


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)

    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(JsonFormatter())
    root.addHandler(stdout)

    host = os.getenv("LOGSTASH_HOST")
    if host:
        port = int(os.getenv("LOGSTASH_PORT", "5000"))
        root.addHandler(LogstashTCPHandler(host, port))
