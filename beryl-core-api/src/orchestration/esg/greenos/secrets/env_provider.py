"""Environment-backed SecretProvider for dev/staging workflows."""

from __future__ import annotations

import os

from src.config.settings import settings

from .names import ENV_NAME_TO_SETTINGS_ATTR
from .provider import SecretMissingError, SecretProvider


class EnvSecretProvider(SecretProvider):
    """Reads GreenOS secrets from environment variables/settings."""

    provider_name = "env"

    def __init__(self, *, cache_ttl_seconds: float = 0.0) -> None:
        super().__init__(cache_ttl_seconds=cache_ttl_seconds)

    def _get_secret(self, *, name: str) -> str:
        env_value = os.getenv(name)
        if isinstance(env_value, str) and env_value.strip():
            return env_value.strip()

        settings_attr = ENV_NAME_TO_SETTINGS_ATTR.get(name)
        if settings_attr:
            value = getattr(settings, settings_attr, None)
            if isinstance(value, str) and value.strip():
                return value.strip()

        raise SecretMissingError(f"Environment secret '{name}' is missing")

