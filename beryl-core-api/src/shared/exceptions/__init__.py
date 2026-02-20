"""
Shared exceptions for the Beryl Core API.

This module defines custom exceptions.
"""

# TODO: Define exceptions

class BerylException(Exception):
    """Base exception for Beryl."""
    pass

class AuthenticationError(BerylException):
    """Authentication error."""
    pass

# TODO: Add more exceptions