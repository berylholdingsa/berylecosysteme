"""Secret providers for GreenOS runtime cryptographic material."""

from .env_provider import EnvSecretProvider
from .factory import build_secret_provider
from .kms_provider import KmsSecretProvider
from .names import (
    GREENOS_REQUIRED_SIGNING_SECRETS,
    SECRET_GREENOS_ED25519_ACTIVE_KEY_VERSION,
    SECRET_GREENOS_ED25519_PRIVATE_KEY,
    SECRET_GREENOS_ED25519_PRIVATE_KEYS_JSON,
    SECRET_GREENOS_ED25519_PUBLIC_KEY,
    SECRET_GREENOS_ED25519_PUBLIC_KEYS_JSON,
    SECRET_GREENOS_SIGNING_ACTIVE_KEY_VERSION,
    SECRET_GREENOS_SIGNING_KEYS_JSON,
    SECRET_GREENOS_SIGNING_SECRET,
)
from .provider import SecretInvalidError, SecretMissingError, SecretProvider, SecretProviderError
from .vault_provider import VaultSecretProvider

__all__ = [
    "SecretProvider",
    "SecretProviderError",
    "SecretMissingError",
    "SecretInvalidError",
    "EnvSecretProvider",
    "VaultSecretProvider",
    "KmsSecretProvider",
    "build_secret_provider",
    "SECRET_GREENOS_SIGNING_SECRET",
    "SECRET_GREENOS_SIGNING_ACTIVE_KEY_VERSION",
    "SECRET_GREENOS_SIGNING_KEYS_JSON",
    "SECRET_GREENOS_ED25519_PRIVATE_KEY",
    "SECRET_GREENOS_ED25519_PUBLIC_KEY",
    "SECRET_GREENOS_ED25519_ACTIVE_KEY_VERSION",
    "SECRET_GREENOS_ED25519_PRIVATE_KEYS_JSON",
    "SECRET_GREENOS_ED25519_PUBLIC_KEYS_JSON",
    "GREENOS_REQUIRED_SIGNING_SECRETS",
]

