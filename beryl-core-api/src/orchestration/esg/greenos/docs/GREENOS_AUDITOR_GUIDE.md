# GreenOS Auditor Guide

Version: 2026-02-17
Audience: independent external auditors, ministry inspection teams, climate-finance due diligence teams

## 1. Audit objective
Verify that a GreenOS impact or MRV artifact is:
- internally consistent;
- cryptographically intact;
- bound to a declared methodology version;
- independently verifiable with public key material.

## 2. Required artifacts
For trip-level verification:
- impact record (`/api/v2/esg/impact/{trip_id}`)
- verification result (`/api/v2/esg/verify/{trip_id}`)

For MRV-level verification:
- export payload (`/api/v2/esg/mrv/export`)
- export verification (`/api/v2/esg/mrv/export/{export_id}/verify`)
- methodology details (`/api/v2/esg/mrv/methodology/current` or `/api/v2/esg/mrv/methodology/{version}`)

For asymmetric verification:
- public key endpoint (`/api/v2/esg/public-key`)
- well-known endpoint (`/.well-known/greenos-public-key`)

## 3. How to obtain public key and fingerprint
### 3.1 Fetch key metadata
Request:
- `GET /api/v2/esg/public-key`
or
- `GET /.well-known/greenos-public-key`

Expected fields:
- `public_key` (base64 Ed25519 public key)
- `fingerprint_sha256` (hex)
- `signature_algorithm` (`ED25519`)
- `key_version`
- `encoding` (`base64`)

### 3.2 Recompute fingerprint independently
Algorithm:
1. decode `public_key` from base64 to raw bytes.
2. compute SHA-256 over raw bytes.
3. compare with returned `fingerprint_sha256`.

If mismatch occurs:
- treat key material as untrusted;
- stop verification workflow;
- escalate as security incident.

## 4. Verifying Ed25519 signatures (public key only)
Example Python reference:

```python
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

def verify_ed25519(hash_hex: str, signature_b64: str, public_key_b64: str) -> bool:
    try:
        public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
        signature = base64.b64decode(signature_b64)
        public_key.verify(signature, hash_hex.encode("utf-8"))
        return True
    except Exception:
        return False
```

Inputs:
- for ledger: `hash_hex = event_hash`, `signature_b64 = asym_signature`
- for MRV: `hash_hex = verification_hash`, `signature_b64 = asym_signature`

## 5. End-to-end MRV verification workflow
1. Fetch export artifact and capture:
   - `payload`
   - `verification_hash`
   - `signature`/`signature_algorithm`/`key_version`
   - `asym_signature`/`asym_algorithm`/`asym_key_version`
   - `methodology_version`
   - `methodology_hash`
2. Recompute canonical JSON hash from `payload`.
3. Compare recomputed hash vs `verification_hash`.
4. Verify HMAC status via platform verify endpoint.
5. Verify Ed25519 signature using public key endpoint data.
6. Fetch methodology version and recompute methodology hash.
7. Validate dedup proof block (`non_double_counting_proof`).
8. Confirm final API verification status equals expected local result.

## 6. Tampering scenarios and expected failures
### Scenario A: payload altered after export
Expected:
- `hash_valid = false`
- `verified = false`
- API code on verify endpoint: `GREENOS_MRV_PAYLOAD_TAMPERED` (400)

### Scenario B: HMAC signature replaced
Expected:
- `signature_valid = false`
- `verified = false`
- API code: `GREENOS_MRV_INVALID_SIGNATURE` (400)

### Scenario C: Ed25519 signature replaced
Expected:
- `asym_signature_valid = false`
- `verified = false`
- API code: `GREENOS_MRV_INVALID_SIGNATURE` (400)

### Scenario D: methodology version/hash mismatch
Expected:
- `methodology_valid = false`
- `verified = false`
- API code: `GREENOS_MRV_INVALID_SIGNATURE` (400) with methodology mismatch message

### Scenario E: unknown export ID
Expected:
- API code: `GREENOS_MRV_EXPORT_NOT_FOUND` (404)

### Scenario F: trip payload tampering
Expected:
- trip verify endpoint returns `GREENOS_PAYLOAD_TAMPERED` (400)

## 7. Key rotation audit checks
1. Confirm key publication endpoints expose active `key_version`.
2. Confirm fingerprint published in institutional documentation.
3. Verify historical artifacts still validate (old key versions retained in keyrings).
4. Confirm production fail-closed behavior for missing/invalid key material.
5. Confirm secret provider status endpoint (admin) shows no `MISSING`/`INVALID`.

## 8. Secret governance checks
Operational endpoint:
- `GET /api/v2/esg/internal/secrets/status` (admin scope required)

Audit expectations:
- provider is declared (`env`, `vault`, `kms`)
- no secrets are returned in clear text
- per-secret statuses are only `OK`, `MISSING`, `INVALID`
- production must not run with missing/invalid critical signing secrets

## 9. External audit checklist
1. Verify API health endpoint responsiveness.
2. Verify public key endpoint and well-known endpoint consistency.
3. Recompute and match public key fingerprint.
4. Verify at least one ledger artifact end-to-end.
5. Verify at least one MRV export end-to-end.
6. Recompute MRV canonical hash independently.
7. Validate Ed25519 signatures independently.
8. Validate methodology hash binding.
9. Inspect non-double-counting proof fields.
10. Validate period uniqueness behavior (duplicate export conflict expected).
11. Check outbox reliability evidence (retry, failed, DLQ telemetry).
12. Check Prometheus MRV/outbox counters for anomaly patterns.
13. Check key rotation evidence (version history and publication).
14. Check secret provider governance and fail-closed policy in production.
15. Record residual risk assumptions and required mitigations.

## 10. Minimum evidence package to archive
- export JSON payload and verification response
- ledger sample and trip verification response
- public key payload with fingerprint
- methodology version snapshot and computed methodology hash
- timestamped audit notes and verifier script output

This package enables reproducible third-party re-checks without privileged secret access.
