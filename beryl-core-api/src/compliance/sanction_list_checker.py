"""Sanctions list abstraction for AML screening."""

from __future__ import annotations

import json
from pathlib import Path

from src.config.settings import settings


class SanctionListChecker:
    def __init__(self) -> None:
        self._path = Path(settings.sanctions_list_path)
        self._entries = self._load_entries()

    def _load_entries(self) -> set[str]:
        if not self._path.exists():
            return set()
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                values = payload.get("entities", [])
            else:
                values = payload
            return {str(value).strip().lower() for value in values if str(value).strip()}
        except Exception:
            return set()

    def is_sanctioned(self, actor_identifier: str) -> bool:
        return actor_identifier.strip().lower() in self._entries


sanction_list_checker = SanctionListChecker()
