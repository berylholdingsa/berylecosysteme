"""
Structured Logging System for Beryl Core API.

Provides JSON-formatted logging with correlation tracking, domain separation,
and enterprise-grade observability features.
"""

import json
import logging
import sys
import threading
from datetime import datetime, UTC
from typing import Any, Dict, Optional
from contextvars import ContextVar

from src.config.settings import settings

# Import correlation context from correlation module
from .correlation import correlation_id, request_id, user_id, domain


class StructuredJSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging with correlation tracking.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with correlation data."""
        # Get correlation context
        corr_id = correlation_id.get()
        req_id = request_id.get()
        usr_id = user_id.get()
        dom = domain.get()

        # Build structured log entry
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": "beryl-core-api",
            "domain": dom or "unknown",
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": corr_id,
            "request_id": req_id,
            "user_id": usr_id,
            "thread_id": threading.get_ident(),
            "thread_name": threading.current_thread().name,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class BerylLogger:
    """
    Main logger class with domain-specific logging capabilities.
    """

    def __init__(self):
        self._setup_logger()

    def _setup_logger(self):
        """Setup the main logger with JSON formatting."""
        self.logger = logging.getLogger("beryl-core-api")
        self.logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Add JSON handler
        json_handler = logging.StreamHandler(sys.stderr)
        json_handler.setFormatter(StructuredJSONFormatter())
        self.logger.addHandler(json_handler)

        # Prevent duplicate logs
        self.logger.propagate = False

    def _log_with_context(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log with additional context fields."""
        extra_fields = extra or {}
        self.logger.log(level, message, extra={"extra_fields": extra_fields})

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, message, kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        extra_fields = kwargs or {}
        self.logger.error(
            message,
            exc_info=True,
            extra={"extra_fields": extra_fields},
        )

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, kwargs)

    def log_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Log HTTP request with performance metrics."""
        level = logging.INFO if status_code < 400 else logging.WARNING
        self._log_with_context(
            level,
            f"HTTP {method} {path} - {status_code}",
            {
                "http_method": method,
                "http_path": path,
                "http_status": status_code,
                "duration_ms": duration_ms,
                "request_type": "http"
            }
        )

    def log_event_published(self, event_type: str, event_id: str):
        """Log event publication."""
        self._log_with_context(
            logging.INFO,
            f"Event published: {event_type}",
            {
                "event_type": event_type,
                "event_id": event_id,
                "operation": "event_publish"
            }
        )

    def log_event_consumed(self, event_type: str, event_id: str, consumer: str):
        """Log event consumption."""
        self._log_with_context(
            logging.INFO,
            f"Event consumed: {event_type} by {consumer}",
            {
                "event_type": event_type,
                "event_id": event_id,
                "consumer": consumer,
                "operation": "event_consume"
            }
        )

    def log_adapter_call(self, adapter: str, method: str, success: bool, duration_ms: float):
        """Log adapter call with performance."""
        level = logging.INFO if success else logging.ERROR
        self._log_with_context(
            level,
            f"Adapter call: {adapter}.{method}",
            {
                "adapter": adapter,
                "method": method,
                "success": success,
                "duration_ms": duration_ms,
                "operation": "adapter_call"
            }
        )


# Global logger instance
logger = BerylLogger()
