"""Replay protection based on nonce + timestamp validation."""

from __future__ import annotations

import os
import time
from collections import OrderedDict
from threading import Lock

from src.config.settings import settings
from src.infrastructure.testing_stubs import DummyNonceStore, build_redis_client
from src.observability.logging.logger import logger


class NonceReplayProtector:
    """Validates nonce uniqueness in a bounded time window."""

    def __init__(self) -> None:
        self.nonce_ttl_seconds = settings.nonce_ttl_seconds
        self.max_skew_seconds = settings.nonce_max_skew_seconds
        self._memory_fallback: OrderedDict[str, float] = OrderedDict()
        self._lock = Lock()
        self._redis = build_redis_client(url=settings.redis_url, decode_responses=True)

    def validate(self, *, nonce: str, unix_timestamp: int, subject: str) -> bool:
        now = int(time.time())
        if abs(now - int(unix_timestamp)) > self.max_skew_seconds:
            return False

        key = f"nonce:{subject}:{nonce}"
        if self._redis is not None:
            try:
                created = self._redis.set(key, str(now), nx=True, ex=self.nonce_ttl_seconds)
                return bool(created)
            except Exception as exc:
                logger.warning(f"event=nonce_redis_write_failed reason={str(exc)}")

        with self._lock:
            self._evict_stale(now)
            if key in self._memory_fallback:
                return False
            self._memory_fallback[key] = float(now)
            return True

    def _evict_stale(self, now: int) -> None:
        stale_before = now - self.nonce_ttl_seconds
        stale_keys = [key for key, created_at in self._memory_fallback.items() if created_at < stale_before]
        for key in stale_keys:
            self._memory_fallback.pop(key, None)


def _create_nonce_protector():
    if os.getenv("TESTING") == "1":
        return DummyNonceStore(ttl_seconds=settings.nonce_ttl_seconds)
    return NonceReplayProtector()


nonce_replay_protector = _create_nonce_protector()
