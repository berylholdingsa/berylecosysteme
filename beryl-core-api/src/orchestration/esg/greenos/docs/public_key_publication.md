# GreenOS Public Key Publication

## Objective
- Provide a stable public trust anchor for independent external verification.
- Allow auditors to verify GreenOS signatures using only public material.

## Public Distribution Channels
1. API endpoint: `GET /api/v2/esg/public-key`
2. Well-known endpoint: `GET /.well-known/greenos-public-key`
3. Official documentation and release notes (publish key version + fingerprint)

## Canonical Public Key Metadata
- `public_key`: base64-encoded Ed25519 public key.
- `fingerprint_sha256`: SHA-256 digest of raw public key bytes (hex).
- `signature_algorithm`: `Ed25519`.
- `key_version`: active key version.
- `encoding`: `base64`.

## Versioning and Rotation Requirements
1. Keep previous public keys available for historical verification through versioned keyring config.
2. Publish each new `key_version` and `fingerprint_sha256` in official documentation.
3. Do not remove old key versions until retention/audit windows are closed.
4. Cross-check endpoint payload and published documentation after each rotation.

## External Auditor Verification Model
- Auditor fetches the public key from either public endpoint.
- Auditor verifies `event_hash` and MRV `verification_hash` signatures with Ed25519.
- No shared secret is required for asymmetric verification.
