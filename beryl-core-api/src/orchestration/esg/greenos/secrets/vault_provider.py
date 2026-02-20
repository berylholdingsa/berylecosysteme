"""Vault-backed runtime SecretProvider."""

from __future__ import annotations

import json
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

from src.observability.logging.logger import logger

from .provider import SecretInvalidError, SecretMissingError, SecretProvider, SecretProviderError


class VaultSecretProvider(SecretProvider):
    """Reads GreenOS secrets from HashiCorp Vault KV HTTP API."""

    provider_name = "vault"

    def __init__(
        self,
        *,
        vault_addr: str,
        vault_token: str,
        vault_path: str,
        cache_ttl_seconds: float = 30.0,
        timeout_seconds: float = 3.0,
    ) -> None:
        super().__init__(cache_ttl_seconds=cache_ttl_seconds)
        self._vault_addr = (vault_addr or "").strip()
        self._vault_token = (vault_token or "").strip()
        self._vault_path = (vault_path or "").strip()
        self._timeout_seconds = max(float(timeout_seconds), 0.1)

    def _get_secret(self, *, name: str) -> str:
        bundle = self._load_bundle()
        value = bundle.get(name)
        if value is None:
            raise SecretMissingError(f"Vault secret '{name}' not found at path '{self._vault_path}'")
        if isinstance(value, str):
            return value
        if isinstance(value, (dict, list)):
            return json.dumps(value, separators=(",", ":"), sort_keys=True)
        return str(value)

    def _load_bundle(self) -> dict[str, Any]:
        cache_key = "__vault_bundle__"
        cached = self._cache_get(cache_key)
        if isinstance(cached, dict):
            return dict(cached)

        bundle = self._fetch_secret_bundle()
        normalized = {str(key): value for key, value in bundle.items()}
        self._cache_set(cache_key, normalized)
        logger.info(
            "event=greenos_vault_bundle_loaded",
            provider=self.provider_name,
            path=self._vault_path,
            keys_count=len(normalized),
        )
        return dict(normalized)

    def _fetch_secret_bundle(self) -> dict[str, Any]:
        if not self._vault_addr:
            raise SecretInvalidError("GREENOS_VAULT_ADDR is required when GREENOS_SECRET_PROVIDER=vault")
        if not self._vault_token:
            raise SecretInvalidError("GREENOS_VAULT_TOKEN is required when GREENOS_SECRET_PROVIDER=vault")
        if not self._vault_path:
            raise SecretInvalidError("GREENOS_VAULT_PATH is required when GREENOS_SECRET_PROVIDER=vault")

        endpoint = f"{self._vault_addr.rstrip('/')}/v1/{self._vault_path.lstrip('/')}"
        request = urlrequest.Request(
            endpoint,
            headers={
                "X-Vault-Token": self._vault_token,
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with urlrequest.urlopen(request, timeout=self._timeout_seconds) as response:
                status_code = getattr(response, "status", 200)
                payload = response.read().decode("utf-8")
        except urlerror.HTTPError as exc:
            raise SecretProviderError(
                f"Vault HTTP error while reading path '{self._vault_path}': {exc.code}"
            ) from exc
        except urlerror.URLError as exc:
            raise SecretProviderError(
                f"Vault connection error while reading path '{self._vault_path}': {exc.reason}"
            ) from exc

        if status_code >= 400:
            raise SecretProviderError(
                f"Vault responded with status={status_code} for path '{self._vault_path}'"
            )

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise SecretInvalidError("Vault response is not valid JSON") from exc

        data = parsed.get("data")
        if isinstance(data, dict) and isinstance(data.get("data"), dict):
            data = data.get("data")
        if not isinstance(data, dict):
            raise SecretInvalidError("Vault response does not contain a KV object under 'data'")
        return data

