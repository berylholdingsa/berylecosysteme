"""
Correlation ID management for distributed tracing and request tracking.
"""

import uuid
from contextvars import ContextVar
from typing import Optional

# Context variables for correlation tracking
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
domain: ContextVar[Optional[str]] = ContextVar('domain', default=None)


class CorrelationManager:
    """
    Manages correlation IDs across the application lifecycle.
    """

    @staticmethod
    def generate_correlation_id() -> str:
        """Generate a new correlation ID."""
        return str(uuid.uuid4())

    @staticmethod
    def generate_request_id() -> str:
        """Generate a new request ID."""
        return f"req_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def set_correlation_id(corr_id: Optional[str] = None) -> str:
        """Set correlation ID in context. Generates one if not provided."""
        if corr_id is None:
            corr_id = CorrelationManager.generate_correlation_id()
        correlation_id.set(corr_id)
        return corr_id

    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Get current correlation ID from context."""
        return correlation_id.get()

    @staticmethod
    def set_request_id(req_id: Optional[str] = None) -> str:
        """Set request ID in context. Generates one if not provided."""
        if req_id is None:
            req_id = CorrelationManager.generate_request_id()
        request_id.set(req_id)
        return req_id

    @staticmethod
    def get_request_id() -> Optional[str]:
        """Get current request ID from context."""
        return request_id.get()

    @staticmethod
    def set_user_id(uid: Optional[str]):
        """Set user ID in context."""
        user_id.set(uid)

    @staticmethod
    def get_user_id() -> Optional[str]:
        """Get current user ID from context."""
        return user_id.get()

    @staticmethod
    def set_domain(dom: str):
        """Set current domain in context."""
        domain.set(dom)

    @staticmethod
    def get_domain() -> Optional[str]:
        """Get current domain from context."""
        return domain.get()

    @staticmethod
    def get_all_context() -> dict:
        """Get all correlation context as dict."""
        return {
            "correlation_id": correlation_id.get(),
            "request_id": request_id.get(),
            "user_id": user_id.get(),
            "domain": domain.get(),
        }

    @staticmethod
    def clear_context():
        """Clear all correlation context."""
        correlation_id.set(None)
        request_id.set(None)
        user_id.set(None)
        domain.set(None)


# Convenience functions
def get_correlation_id() -> Optional[str]:
    """Convenience function to get correlation ID."""
    return CorrelationManager.get_correlation_id()

def set_correlation_id(corr_id: Optional[str] = None) -> str:
    """Convenience function to set correlation ID."""
    return CorrelationManager.set_correlation_id(corr_id)

def get_request_id() -> Optional[str]:
    """Convenience function to get request ID."""
    return CorrelationManager.get_request_id()

def set_request_id(req_id: Optional[str] = None) -> str:
    """Convenience function to set request ID."""
    return CorrelationManager.set_request_id(req_id)

def get_user_id() -> Optional[str]:
    """Convenience function to get user ID."""
    return CorrelationManager.get_user_id()

def set_user_id(uid: Optional[str]):
    """Convenience function to set user ID."""
    CorrelationManager.set_user_id(uid)

def get_domain() -> Optional[str]:
    """Convenience function to get domain."""
    return CorrelationManager.get_domain()

def set_domain(dom: str):
    """Convenience function to set domain."""
    CorrelationManager.set_domain(dom)