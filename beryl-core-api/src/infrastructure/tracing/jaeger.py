"""Jaeger tracing bootstrap helpers."""

from __future__ import annotations

from src.config.settings import settings


def jaeger_otlp_endpoint() -> str:
    if settings.jaeger_endpoint:
        return settings.jaeger_endpoint
    return f"http://{settings.jaeger_host}:{settings.jaeger_port}/v1/traces"
