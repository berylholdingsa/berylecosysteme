"""Fintech domain event consumers (cross-domain listeners)."""

from src.events.base.event import DomainEvent, DomainEventType
from src.events.base.event_handler import EventHandler
from src.observability.logger import logger
from typing import Set


class TransactionCompletedConsumer(EventHandler):
    """Consumes TransactionCompleted events from Fintech."""
    
    # Track processed events for idempotency
    _processed: Set[str] = set()
    handled_events: list = []
    
    def can_handle(self, event: DomainEvent) -> bool:
        return event.event_type == DomainEventType.TRANSACTION_COMPLETED
    
    async def handle(self, event: DomainEvent) -> None:
        # Idempotency check
        if event.event_id in self._processed:
            logger.debug(f"Skipping already processed event: {event.event_id}")
            return
        
        try:
            logger.info(f"TransactionCompletedConsumer: Processing {event.event_id}")
            
            # Example: Update user balance, send notification, etc.
            transaction_id = event.payload.get("transaction_id")
            user_id = event.payload.get("user_id")
            amount = event.payload.get("amount")
            
            # TODO: Implement business logic
            # - Update user account
            # - Send email notification
            # - Log transaction
            
            self._processed.add(event.event_id)
            self.handled_events.append(event)
            logger.info(f"✓ Transaction {transaction_id} processed for user {user_id}")
            
        except Exception as e:
            logger.error(f"TransactionCompletedConsumer error: {str(e)}")
            # Don't re-raise - errors don't block the system


class PaymentFailedConsumer(EventHandler):
    """Consumes PaymentFailed events from Fintech."""
    
    _processed: Set[str] = set()
    
    def can_handle(self, event: DomainEvent) -> bool:
        return event.event_type == DomainEventType.PAYMENT_FAILED
    
    async def handle(self, event: DomainEvent) -> None:
        if event.event_id in self._processed:
            return
        
        try:
            logger.warning(f"PaymentFailedConsumer: Processing {event.event_id}")
            
            payment_id = event.payload.get("payment_id")
            reason = event.payload.get("reason")
            
            # TODO: Send alert, retry logic, etc.
            
            self._processed.add(event.event_id)
        except Exception as e:
            logger.error(f"PaymentFailedConsumer error: {str(e)}")
