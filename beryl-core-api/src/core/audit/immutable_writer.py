"""Append-only writer for immutable audit entries."""

from __future__ import annotations

from src.core.audit.audit_event import AuditEvent
from src.core.audit.repository import AuditRepository


class ImmutableAuditWriter:
    def __init__(self, repository: AuditRepository):
        self._repository = repository

    def write(self, session, event: AuditEvent):
        return self._repository.append(session=session, event=event)
