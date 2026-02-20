"""Idempotency guard for Kafka publish/consume deduplication."""

from __future__ import annotations

import time
from collections import OrderedDict
from threading import Lock

from src.config.settings import settings
from src.infrastructure.testing_stubs import build_redis_client


class IdempotencyGuard:
    def __init__(self) -> None:
        self.ttl_seconds = 24 * 60 * 60
        self._redis = build_redis_client(settings.redis_url, decode_responses=True)
        self._memory = OrderedDict()
        self._lock = Lock()

    def claim(self, key: str) -> bool:
        now = int(time.time())
        if self._redis is not None:
            try:
                return bool(self._redis.set(f"kafka-idem:{key}", str(now), nx=True, ex=self.ttl_seconds))
            except Exception:
                pass

        with self._lock:
            self._cleanup(now)
            if key in self._memory:
                return False
            self._memory[key] = now
            return True

    def _cleanup(self, now: int) -> None:
        cutoff = now - self.ttl_seconds
        expired = [key for key, ts in self._memory.items() if ts < cutoff]
        for key in expired:
            self._memory.pop(key, None)


idempotency_guard = IdempotencyGuard()
