"""
Dependency injection container for the Beryl Core API.

This module provides dependencies for the application, such as database sessions,
external clients, etc.
"""

from fastapi import HTTPException, Request, status

from src.config.settings import settings

# TODO: Implement dependency injection
# Example: database session, external API clients

def get_settings():
    """Get application settings."""
    return settings


def get_current_user(request: Request) -> dict:
    """Return authenticated user payload injected by auth middleware."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    return user

# TODO: Add more dependencies
