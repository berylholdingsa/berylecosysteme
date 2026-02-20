"""
Client for fintech mamba core API.

This module provides a client to interact with the fintech API.
"""

import httpx
from src.config.settings import settings

class FintechClient:
    """Client for fintech API."""

    def __init__(self):
        self.base_url = settings.fintech_api_url
        self.client = httpx.AsyncClient()

    async def get_payments(self):
        """Get payments from fintech API."""
        # Stub for testing
        return {"payments": []}

    async def healthcheck(self):
        """Health check for fintech API."""
        return True

# TODO: Add more client methods