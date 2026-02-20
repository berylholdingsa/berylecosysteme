"""Cryptographic signer for certified statement hashes."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa

from src.config.settings import settings
from src.observability.logging.logger import logger


@dataclass(frozen=True)
class SignatureMetadata:
    algorithm: str
    key_id: str
    public_key_pem: str


class StatementSigner:
    """Signs statement document hashes with Beryl private key."""

    def __init__(self, *, private_key_pem: bytes | None = None, private_key_b64: str | None = None) -> None:
        raw_key = private_key_pem
        if raw_key is None:
            b64 = private_key_b64 or settings.bfos_statement_signing_private_key_b64
            raw_key = base64.b64decode(b64.encode("utf-8")) if b64 else None

        self._private_key = None
        self._public_key_pem = ""
        self._key_id = ""

        if raw_key:
            key = serialization.load_pem_private_key(raw_key, password=None)
            self._private_key = key
            public_pem = key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            self._public_key_pem = public_pem.decode("utf-8")
            self._key_id = hashlib.sha256(public_pem).hexdigest()[:32]

    @property
    def algorithm(self) -> str:
        return settings.bfos_statement_signing_algorithm

    def metadata(self) -> SignatureMetadata:
        if self._private_key is None:
            raise RuntimeError("statement signing key is not configured")
        return SignatureMetadata(
            algorithm=self.algorithm,
            key_id=self._key_id,
            public_key_pem=self._public_key_pem,
        )

    def sign_document(self, hash_hex: str) -> str:
        if self._private_key is None:
            raise RuntimeError("statement signing key is not configured")

        payload = hash_hex.encode("utf-8")
        if isinstance(self._private_key, rsa.RSAPrivateKey):
            signature = self._private_key.sign(
                payload,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        else:
            signature = self._private_key.sign(payload, ec.ECDSA(hashes.SHA256()))

        encoded = base64.b64encode(signature).decode("utf-8")
        logger.info("event=bfos_statement_hash_signed", key_id=self._key_id, algorithm=self.algorithm)
        return encoded

    def verify_signature(self, hash_hex: str, signature: str) -> bool:
        if self._private_key is None:
            return False

        payload = hash_hex.encode("utf-8")
        raw_signature = base64.b64decode(signature.encode("utf-8"))
        pub_key = self._private_key.public_key()

        try:
            if isinstance(pub_key, rsa.RSAPublicKey):
                pub_key.verify(raw_signature, payload, padding.PKCS1v15(), hashes.SHA256())
            else:
                pub_key.verify(raw_signature, payload, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:  # pragma: no cover
            return False


statement_signer = StatementSigner()
