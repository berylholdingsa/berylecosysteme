"""KMS-backed SecretProvider skeleton (cloud SDK optional)."""

from __future__ import annotations

import os

from .provider import SecretInvalidError, SecretMissingError, SecretProvider


class KmsSecretProvider(SecretProvider):
    """Generic KMS provider stub with optional environment bootstrap fallback.

    This implementation intentionally avoids hard dependencies on cloud SDKs.
    Wire a real decrypt adapter in production (AWS KMS, GCP KMS, etc.).
    """

    provider_name = "kms"

    def __init__(
        self,
        *,
        kms_key_id: str,
        kms_provider: str,
        kms_region: str,
        cache_ttl_seconds: float = 30.0,
        enable_env_bootstrap_fallback: bool = True,
    ) -> None:
        super().__init__(cache_ttl_seconds=cache_ttl_seconds)
        self._kms_key_id = (kms_key_id or "").strip()
        self._kms_provider = (kms_provider or "").strip().lower()
        self._kms_region = (kms_region or "").strip()
        self._enable_env_bootstrap_fallback = enable_env_bootstrap_fallback

    def _get_secret(self, *, name: str) -> str:
        if not self._kms_key_id:
            raise SecretInvalidError("GREENOS_KMS_KEY_ID is required when GREENOS_SECRET_PROVIDER=kms")
        if self._kms_provider not in {"aws", "gcp", "generic"}:
            raise SecretInvalidError("GREENOS_KMS_PROVIDER must be one of: aws, gcp, generic")
        if not self._kms_region:
            raise SecretInvalidError("GREENOS_KMS_REGION is required when GREENOS_SECRET_PROVIDER=kms")

        if self._enable_env_bootstrap_fallback:
            value = os.getenv(name)
            if isinstance(value, str) and value.strip():
                return value.strip()

        raise SecretMissingError(
            f"KMS secret '{name}' is unavailable. Wire provider-specific decrypt adapter for {self._kms_provider}."
        )

    def _decrypt_with_aws_example(self, ciphertext_b64: str) -> str:
        raise NotImplementedError(
            "Example only: call boto3 KMS decrypt and return plaintext. No SDK dependency is bundled here."
        )

    def _decrypt_with_gcp_example(self, ciphertext_b64: str) -> str:
        raise NotImplementedError(
            "Example only: call Google Cloud KMS decrypt and return plaintext. No SDK dependency is bundled here."
        )

