"""
Permissions for the Beryl Core API.

This module defines permissions for roles.
"""

# TODO: Define permissions

PERMISSIONS = {
    "admin": ["read", "write", "delete"],
    "user": ["read"],
    "partner": ["read", "write"],
}

# TODO: Add more permission definitions