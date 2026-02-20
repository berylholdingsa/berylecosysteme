"""
Domain events for the Beryl Core API.

This module defines domain events.
"""

# TODO: Define domain events

class UserCreatedEvent:
    """Event for user creation."""
    def __init__(self, user_id: str):
        self.user_id = user_id

# TODO: Add more events