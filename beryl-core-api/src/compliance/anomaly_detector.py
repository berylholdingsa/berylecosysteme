"""Simple anomaly detector for transactional behavior baselines."""

from __future__ import annotations

from collections import defaultdict, deque
from statistics import mean, pstdev


class AnomalyDetector:
    def __init__(self, baseline_size: int = 50) -> None:
        self.baseline_size = baseline_size
        self._history = defaultdict(lambda: deque(maxlen=self.baseline_size))

    def evaluate(self, actor_id: str, amount: float) -> bool:
        history = self._history[actor_id]
        if len(history) < 5:
            history.append(amount)
            return False

        avg = mean(history)
        deviation = pstdev(history) or 1.0
        z_score = abs((amount - avg) / deviation)
        history.append(amount)
        return z_score >= 3.0


anomaly_detector = AnomalyDetector()
