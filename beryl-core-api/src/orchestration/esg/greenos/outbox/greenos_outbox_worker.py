"""Dedicated worker process for GreenOS transactional outbox relay."""

from __future__ import annotations

import asyncio

from src.config.settings import settings
from src.observability.logging.logger import logger
from src.orchestration.esg.greenos.outbox.relay_service import OutboxRelayService


class GreenOSOutboxWorker:
    """Background worker that continuously relays pending GreenOS outbox events."""

    def __init__(
        self,
        *,
        relay: OutboxRelayService | None = None,
        poll_interval_seconds: float | None = None,
        batch_size: int | None = None,
    ) -> None:
        self._relay = relay or OutboxRelayService(max_retry_count=settings.greenos_outbox_max_retry_count)
        self._poll_interval_seconds = poll_interval_seconds or settings.greenos_outbox_poll_interval_seconds
        self._batch_size = batch_size or settings.greenos_outbox_batch_size
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop(), name="greenos-outbox-worker")
        logger.info(
            "event=greenos_outbox_worker_started",
            poll_interval_seconds=self._poll_interval_seconds,
            batch_size=self._batch_size,
        )

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        await self._task
        self._task = None
        logger.info("event=greenos_outbox_worker_stopped")

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self._relay.run_once(limit=self._batch_size)
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                logger.error("event=greenos_outbox_worker_loop_error", reason=str(exc))
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._poll_interval_seconds)
            except TimeoutError:
                continue


async def run_worker_forever() -> None:
    """Entrypoint for standalone worker process execution."""
    worker = GreenOSOutboxWorker()
    await worker.start()
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("event=greenos_outbox_worker_keyboard_interrupt")
    finally:
        await worker.stop()


def main() -> None:
    asyncio.run(run_worker_forever())


if __name__ == "__main__":
    main()

