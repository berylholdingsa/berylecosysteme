"""SecretProvider interface and shared cache behavior."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from threading import Lock
import time
from typing import Any


class SecretProviderError(RuntimeError):
    """Base class for runtime secret provider failures."""


class SecretMissingError(SecretProviderError):
    """Raised when a requested secret does not exist."""


class SecretInvalidError(SecretProviderError):
    """Raised when secret content is malformed."""


@dataclass(frozen=True)
class _CacheEntry:
    value: Any
    expires_at: float


class SecretProvider(ABC):
    """Abstract runtime secret provider with optional in-memory TTL cache."""

    provider_name = "unknown"

    def __init__(self, *, cache_ttl_seconds: float = 0.0) -> None:
        self._cache_ttl_seconds = max(float(cache_ttl_seconds), 0.0)
        self._cache: dict[str, _CacheEntry] = {}
        self._cache_lock = Lock()

    @property
    def cache_ttl_seconds(self) -> float:
        return self._cache_ttl_seconds

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()

    def get_secret(self, name: str) -> str:
        cache_key = f"secret:{name}"
        cached = self._cache_get(cache_key)
        if isinstance(cached, str) and cached:
            return cached

        value = self._get_secret(name=name)
        if not isinstance(value, str):
            raise SecretInvalidError(f"Secret '{name}' returned non-string value")
        normalized = value.strip()
        if not normalized:
            raise SecretMissingError(f"Secret '{name}' is missing")
        self._cache_set(cache_key, normalized)
        return normalized

    def get_json(self, name: str) -> dict[str, Any]:
        cache_key = f"json:{name}"
        cached = self._cache_get(cache_key)
        if isinstance(cached, dict):
            return dict(cached)

        raw = self.get_secret(name=name)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SecretInvalidError(f"Secret '{name}' must contain valid JSON object") from exc

        if not isinstance(parsed, dict):
            raise SecretInvalidError(f"Secret '{name}' must contain a JSON object")

        normalized = {str(key): value for key, value in parsed.items()}
        self._cache_set(cache_key, normalized)
        return dict(normalized)

    @abstractmethod
    def _get_secret(self, *, name: str) -> str:
        """Return one secret value or raise SecretProviderError."""

    def _cache_get(self, key: str) -> Any | None:
        if self._cache_ttl_seconds <= 0:
            return None
        now = time.monotonic()
        with self._cache_lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                self._cache.pop(key, None)
                return None
            return entry.value

    def _cache_set(self, key: str, value: Any) -> None:
        if self._cache_ttl_seconds <= 0:
            return
        with self._cache_lock:
            self._cache[key] = _CacheEntry(
                value=value,
                expires_at=time.monotonic() + self._cache_ttl_seconds,
            )

