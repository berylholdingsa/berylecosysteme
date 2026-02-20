"""Transactional outbox and relay for reliable Kafka publishing."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from src.db.models.outbox import OutboxEventModel
from src.db.sqlalchemy import Base, get_engine, get_session_local
from src.events.bus.event_bus import get_event_bus
from src.observability.logging.logger import logger


class OutboxRelayService:
    def __init__(self) -> None:
        try:
            Base.metadata.create_all(
                bind=get_engine(),
                tables=[OutboxEventModel.__table__],
                checkfirst=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"event=outbox_bootstrap_skipped reason={str(exc)}")

    def stage_event(self, *, session, topic: str, event_key: str, payload: dict, signature: str) -> OutboxEventModel:
        row = OutboxEventModel(
            topic=topic,
            event_key=event_key,
            payload=payload,
            signature=signature,
            status="PENDING",
            attempts=0,
        )
        session.add(row)
        session.flush()
        return row

    async def publish_pending(self, *, limit: int = 100) -> dict[str, int]:
        published = 0
        failed = 0
        dlq = 0
        scanned = 0

        bus = await get_event_bus()
        with get_session_local()() as session:
            stmt = (
                select(OutboxEventModel)
                .where(OutboxEventModel.status.in_(["PENDING", "FAILED"]))
                .order_by(OutboxEventModel.created_at.asc())
                .limit(limit)
            )
            events = list(session.execute(stmt).scalars().all())

            for event in events:
                scanned += 1
                try:
                    payload = dict(event.payload)
                    payload["signature"] = event.signature
                    await bus.publish_raw(topic=event.topic, key=event.event_key, payload=payload)
                    event.status = "PUBLISHED"
                    event.published_at = datetime.now(timezone.utc)
                    event.last_error = None
                    event.attempts += 1
                    published += 1
                except Exception as exc:
                    event.attempts += 1
                    event.last_error = str(exc)
                    if ".dlq" in event.topic or any(
                        marker in str(exc).lower()
                        for marker in ("schema_validation", "unsigned financial", "invalid financial signature")
                    ):
                        event.status = "DLQ"
                        dlq += 1
                    else:
                        event.status = "FAILED"
                        failed += 1

            session.commit()

        return {
            "published": published,
            "failed": failed,
            "dlq": dlq,
            "scanned": scanned,
        }

    def dlq_count(self) -> int:
        with get_session_local()() as session:
            stmt = select(OutboxEventModel).where(OutboxEventModel.status == "DLQ")
            return len(list(session.execute(stmt).scalars().all()))


outbox_relay_service = OutboxRelayService()
