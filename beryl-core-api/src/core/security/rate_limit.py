"""Redis-backed rate limiting primitives."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from threading import Lock

from src.config.settings import settings
from src.infrastructure.testing_stubs import DummyRateLimiter, build_redis_client
from src.observability.logging.logger import logger


class RedisRateLimiter:
    def __init__(self) -> None:
        self.max_requests = settings.rate_limit_requests
        self.window_seconds = settings.rate_limit_window_seconds
        self._redis = build_redis_client(url=settings.redis_url, decode_responses=True)
        self._fallback = defaultdict(list)
        self._lock = Lock()

    def allow(self, subject: str) -> tuple[bool, int]:
        now = int(time.time())
        bucket = now // self.window_seconds
        redis_key = f"rate_limit:{subject}:{bucket}"

        if self._redis is not None:
            try:
                count = self._redis.incr(redis_key)
                if count == 1:
                    self._redis.expire(redis_key, self.window_seconds)
                remaining = max(0, self.max_requests - int(count))
                return int(count) <= self.max_requests, remaining
            except Exception as exc:
                logger.warning(f"event=rate_limit_redis_error reason={str(exc)}")

        with self._lock:
            entries = self._fallback[subject]
            self._fallback[subject] = [ts for ts in entries if now - ts < self.window_seconds]
            if len(self._fallback[subject]) >= self.max_requests:
                return False, 0
            self._fallback[subject].append(now)
            remaining = max(0, self.max_requests - len(self._fallback[subject]))
            return True, remaining


def _create_rate_limiter():
    if os.getenv("TESTING") == "1":
        return DummyRateLimiter(max_requests=settings.rate_limit_requests)
    return RedisRateLimiter()


redis_rate_limiter = _create_rate_limiter()
