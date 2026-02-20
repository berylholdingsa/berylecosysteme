"""Lightweight stubs for infrastructure that should stay offline under TESTING mode."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Dict, Iterator, List

from src.config.settings import settings


class InMemoryRedis:
    def __init__(self) -> None:
        self._values: Dict[str, Any] = {}
        self._expirations: Dict[str, float] = {}
        self._lock = Lock()

    def _cleanup(self) -> None:
        now = time.time()
        expired = [key for key, expiry in self._expirations.items() if expiry <= now]
        for key in expired:
            self._values.pop(key, None)
            self._expirations.pop(key, None)

    def ping(self) -> bool:
        return True

    def set(self, name: str, value: Any, nx: bool = False, ex: int | None = None) -> bool:
        with self._lock:
            self._cleanup()
            if nx and name in self._values:
                return False
            self._values[name] = value
            if ex is not None:
                self._expirations[name] = time.time() + ex
            else:
                self._expirations.pop(name, None)
            return True

    def incr(self, name: str) -> int:
        with self._lock:
            self._cleanup()
            value = int(self._values.get(name, 0)) + 1
            self._values[name] = value
            return value

    def expire(self, name: str, seconds: int) -> bool:
        with self._lock:
            if name not in self._values:
                return False
            self._expirations[name] = time.time() + seconds
            return True

    def get(self, name: str) -> Any:
        with self._lock:
            self._cleanup()
            return self._values.get(name)


class DummyRateLimiter:
    def __init__(self, max_requests: int = settings.rate_limit_requests) -> None:
        self.max_requests = max_requests

    def allow(self, subject: str) -> tuple[bool, int]:
        return True, self.max_requests


class DummyNonceStore:
    def __init__(self, ttl_seconds: int = settings.nonce_ttl_seconds) -> None:
        self.ttl_seconds = ttl_seconds
        self._entries: Dict[str, float] = {}
        self._lock = Lock()

    def validate(self, *, nonce: str, unix_timestamp: int, subject: str) -> bool:
        now = time.time()
        cutoff = now - self.ttl_seconds
        with self._lock:
            expired = [key for key, expiry in self._entries.items() if expiry < cutoff]
            for key in expired:
                self._entries.pop(key, None)
            key = f"nonce:{subject}:{nonce}"
            if key in self._entries:
                return False
            self._entries[key] = now
            return True


@dataclass(frozen=True, slots=True)
class DummyAOQDecision:
    allowed: bool = True
    score: float = 90.0
    threshold: float = 60.0
    decision: str = "APPROVE"
    rationale: str = "testing-mode"


class DummyAOQClient:
    def evaluate(self, *_, **__) -> DummyAOQDecision:
        return DummyAOQDecision()


class InMemoryKafkaProducer:
    def __init__(self) -> None:
        self.published: List[Dict[str, Any]] = []

    def send(self, topic: str, key: bytes | None = None, value: bytes | None = None) -> "InMemoryFuture":
        self.published.append({"topic": topic, "key": key.decode("utf-8") if key else None, "value": value})
        return InMemoryFuture()


class InMemoryFuture:
    def get(self, timeout: float | None = None) -> None:
        return None


class InMemoryKafkaConsumer:
    def __init__(self) -> None:
        self._records: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def poll(self, timeout_ms: int | None = None, max_records: int | None = None) -> Dict[Any, List[Any]]:
        snapshot = dict(self._records)
        self._records.clear()
        return snapshot

    def add_record(self, topic: str, partition: int, record: Any) -> None:
        self._records.setdefault(topic, []).append(record)


def build_redis_client(url: str, decode_responses: bool = True) -> InMemoryRedis | Any:
    if os.getenv("TESTING") == "1":
        return InMemoryRedis()
    try:
        import redis as redis_module
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        return None
    try:
        client = redis_module.Redis.from_url(url, decode_responses=decode_responses)
        client.ping()
        return client
    except Exception:
        return None


def get_inmemory_kafka_producer() -> InMemoryKafkaProducer:
    return InMemoryKafkaProducer()


def get_inmemory_kafka_consumer() -> InMemoryKafkaConsumer:
    return InMemoryKafkaConsumer()
