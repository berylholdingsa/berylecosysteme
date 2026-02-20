"""Domain errors for GreenOS services."""

from __future__ import annotations


class GreenOSError(Exception):
    """Base GreenOS domain error."""


class CountryFactorNotConfiguredError(GreenOSError):
    """Raised when no carbon factors are configured for a country."""


class ImpactNotFoundError(GreenOSError):
    """Raised when requested impact record does not exist."""


class LedgerIntegrityError(GreenOSError):
    """Raised when ledger uniqueness/idempotency constraints are violated."""


class EventContractValidationError(GreenOSError):
    """Raised when Kafka event payload does not satisfy strict schema contract."""


class SignatureVerificationError(GreenOSError):
    """Raised when stored signature cannot be verified with configured key material."""


class PayloadTamperingDetectedError(GreenOSError):
    """Raised when immutable hash/checksum verification fails."""


class MrvExportAlreadyExistsError(GreenOSError):
    """Raised when an MRV export already exists for the requested period."""


class MrvExportNotFoundError(GreenOSError):
    """Raised when an MRV export cannot be found."""


class MrvVerificationError(GreenOSError):
    """Raised when MRV export integrity or signature verification fails."""


class MrvMethodologyNotFoundError(GreenOSError):
    """Raised when requested MRV methodology version does not exist."""


class MrvMethodologyConflictError(GreenOSError):
    """Raised when MRV methodology activation/version constraints are violated."""


class MrvMethodologyValidationError(GreenOSError):
    """Raised when active methodology is incomplete for certified export usage."""
