"""JWT validation against rotating key ring."""

from __future__ import annotations

from src.core.security.jwt_rotation import TokenValidationError, jwt_rotation_service


def verify_token(token: str):
    """Verify a JWT token and return claims, else None."""
    try:
        return jwt_rotation_service.verify(token)
    except TokenValidationError:
        return None
