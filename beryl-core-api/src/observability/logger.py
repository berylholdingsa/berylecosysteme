"""Backward-compatible logger facade with structured JSON output."""

from __future__ import annotations

import logging
import sys

from src.config.settings import settings
from src.observability.logging.logger import StructuredJSONFormatter


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("beryl-core-api")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(StructuredJSONFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = _build_logger()

