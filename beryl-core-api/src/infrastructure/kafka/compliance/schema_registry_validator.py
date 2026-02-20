"""Schema validation before Kafka publish/consume."""

from __future__ import annotations

import json
from pathlib import Path

from src.config.settings import settings


class SchemaValidationError(ValueError):
    """Raised when an event does not match the required schema."""


class SchemaRegistryValidator:
    def __init__(self, registry_path: str | None = None) -> None:
        path = registry_path or settings.kafka_schema_registry_path
        self._path = Path(path)
        self._registry = self._load_registry()

    def _load_registry(self) -> dict:
        if not self._path.exists():
            return {}
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise SchemaValidationError("Schema registry must be a JSON object")
        return payload

    def validate(self, *, topic: str, payload: dict) -> None:
        schema = self._registry.get(topic)
        if not schema:
            if topic.startswith("fintech."):
                raise SchemaValidationError(f"schema missing for topic {topic}")
            return

        required = schema.get("required", [])
        field_types = schema.get("field_types", {})

        for field in required:
            if field not in payload:
                raise SchemaValidationError(f"missing required field: {field}")

        for field, expected in field_types.items():
            if field not in payload:
                continue
            value = payload[field]
            if expected == "str" and not isinstance(value, str):
                raise SchemaValidationError(f"invalid type for {field}: expected str")
            if expected == "float" and not isinstance(value, (float, int)):
                raise SchemaValidationError(f"invalid type for {field}: expected float")
            if expected == "dict" and not isinstance(value, dict):
                raise SchemaValidationError(f"invalid type for {field}: expected dict")
            if expected == "int" and not isinstance(value, int):
                raise SchemaValidationError(f"invalid type for {field}: expected int")
