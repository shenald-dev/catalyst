"""Structured logging integration for Catalyst.

Provides `setup_json_logging()` to configure either structlog (if available)
or standard logging with JSON formatting. Intended to be called once at
application startup.
"""

import logging
import sys
import json
import datetime
from typing import Any, Dict


def _json_formatter(record: logging.LogRecord) -> str:
    """Custom JSON formatter for standard logging."""
    log_object = {
        "timestamp": datetime.datetime.utcfromtimestamp(record.created).isoformat() + "Z",
        "level": record.levelname,
        "logger": record.name,
        "message": record.getMessage(),
    }
    if record.exc_info:
        log_object["exception"] = logging.Formatter().formatException(record.exc_info)
    if record.stack_info:
        log_object["stack"] = record.stack_info
    # Include extra fields
    for key, value in record.__dict__.items():
        if key not in ("name", "msg", "args", "created", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "message", "pathname", "process", "processName", "relativeCreated", "thread", "threadName", "exc_info", "exc_text", "stack_info"):
            log_object[key] = value
    return json.dumps(log_object)


class JSONFormatter(logging.Formatter):
    """Logging formatter that outputs JSON."""
    def format(self, record):
        return _json_formatter(record)


def setup_json_logging(level: int = logging.INFO) -> None:
    """
    Configure logging to output JSON lines to stdout.

    If structlog is installed, configure it to produce JSON output and
    also route standard logging through structlog.

    If structlog is not available, configure a standard logging.StreamHandler
    with a custom JSON formatter.

    Args:
        level: Logging level (default: INFO).
    """
    try:
        import structlog
        # Configure structlog for JSON output
        structlog.configure(
            processors=[
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        # Also configure standard logging to use structlog
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=level,
        )
        structlog.stdlib.merge_logger_params(logging.getLogger())
    except ImportError:
        # Fallback to standard logging with custom JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(JSONFormatter())
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        # Remove existing handlers to avoid duplicates
        root_logger.handlers = [handler]
