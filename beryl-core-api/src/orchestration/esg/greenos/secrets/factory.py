"""SecretProvider factory for GreenOS signing runtime."""

from __future__ import annotations

from src.config.settings import settings

from .env_provider import EnvSecretProvider
from .kms_provider import KmsSecretProvider
from .provider import SecretInvalidError, SecretProvider
from .vault_provider import VaultSecretProvider


def build_secret_provider(
    *,
    provider_name: str | None = None,
    cache_ttl_seconds: float | None = None,
) -> SecretProvider:
    """Instantiate the configured GreenOS secret provider."""
    selected = (provider_name or settings.greenos_secret_provider or "env").strip().lower()
    ttl = float(cache_ttl_seconds) if cache_ttl_seconds is not None else float(settings.greenos_secret_cache_ttl_seconds)

    if selected == "env":
        return EnvSecretProvider(cache_ttl_seconds=ttl)
    if selected == "vault":
        return VaultSecretProvider(
            vault_addr=settings.greenos_vault_addr,
            vault_token=settings.greenos_vault_token,
            vault_path=settings.greenos_vault_path,
            cache_ttl_seconds=ttl,
        )
    if selected == "kms":
        return KmsSecretProvider(
            kms_key_id=settings.greenos_kms_key_id,
            kms_provider=settings.greenos_kms_provider,
            kms_region=settings.greenos_kms_region,
            cache_ttl_seconds=ttl,
        )

    raise SecretInvalidError(
        f"Unsupported GREENOS_SECRET_PROVIDER='{selected}'. Supported: env, vault, kms"
    )

