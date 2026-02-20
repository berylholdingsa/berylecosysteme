"""Velocity checks for anti-fraud controls."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from src.config.settings import settings
from src.infrastructure.testing_stubs import build_redis_client


class VelocityChecker:
    def __init__(self) -> None:
        self.window_seconds = 60
        self.max_transactions_per_window = 20
        self._redis = build_redis_client(settings.redis_url, decode_responses=True)
        self._memory = defaultdict(list)
        self._lock = Lock()

    def is_velocity_exceeded(self, actor_id: str) -> bool:
        now = int(time.time())
        bucket = now // self.window_seconds
        key = f"velocity:{actor_id}:{bucket}"

        if self._redis is not None:
            try:
                count = self._redis.incr(key)
                if count == 1:
                    self._redis.expire(key, self.window_seconds)
                return int(count) > self.max_transactions_per_window
            except Exception:
                pass

        with self._lock:
            entries = self._memory[actor_id]
            self._memory[actor_id] = [ts for ts in entries if now - ts < self.window_seconds]
            self._memory[actor_id].append(now)
            return len(self._memory[actor_id]) > self.max_transactions_per_window


velocity_checker = VelocityChecker()
