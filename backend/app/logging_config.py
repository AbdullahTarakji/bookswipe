"""Structured JSON logging configuration with sensitive field redaction."""

import logging
import re

from pythonjsonlogger import jsonlogger

from app.config import settings

SENSITIVE_FIELDS = {"password", "token", "access_token", "refresh_token", "secret", "email", "authorization"}
_REDACT_PATTERN = re.compile(
    r'("(?:' + "|".join(SENSITIVE_FIELDS) + r')":\s*")(.*?)(")',
    re.IGNORECASE,
)


class SensitiveFilter(logging.Filter):
    """Redact sensitive key values from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for field in SENSITIVE_FIELDS:
            if field in msg.lower():
                record.msg = _REDACT_PATTERN.sub(r'\1***REDACTED***\3', str(record.msg))
                break
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that adds standard fields to every log line."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        # Extra fields injected by middleware
        for key in ("request_id", "user_id", "endpoint", "duration_ms", "status_code"):
            val = getattr(record, key, None)
            if val is not None:
                log_record[key] = val


def setup_logging() -> None:
    """Configure root logger with structured JSON output and sensitive-field redaction."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(CustomJsonFormatter("%(asctime)s %(level)s %(name)s %(message)s"))
    handler.addFilter(SensitiveFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
