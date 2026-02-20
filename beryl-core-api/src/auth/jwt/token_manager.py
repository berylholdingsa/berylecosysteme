"""JWT token management delegating to rotating key service."""

from __future__ import annotations

from datetime import timedelta

from src.core.security.jwt_rotation import jwt_rotation_service


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create an access token signed with active key-id."""
    return jwt_rotation_service.issue_access_token(data, expires_delta=expires_delta).token
