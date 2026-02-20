# GreenOS Secret Provider Runbook

## Objective
- Resolve GreenOS signing keys at runtime from a managed secret backend.
- Keep local development simple with environment-based secrets.
- Enforce fail-closed startup behavior in production.

## Provider Selection
- `GREENOS_SECRET_PROVIDER=env|vault|kms`
- `env`: local/dev/staging bootstrap from environment variables.
- `vault`: runtime retrieval from Vault KV HTTP API.
- `kms`: generic KMS integration stub (cloud SDK wiring required for full production use).

## Required GreenOS Secrets
- `GREENOS_SIGNING_SECRET`
- `GREENOS_SIGNING_ACTIVE_KEY_VERSION`
- `GREENOS_SIGNING_KEYS_JSON`
- `GREENOS_ED25519_PRIVATE_KEY`
- `GREENOS_ED25519_PUBLIC_KEY`
- `GREENOS_ED25519_ACTIVE_KEY_VERSION`
- `GREENOS_ED25519_PRIVATE_KEYS_JSON`
- `GREENOS_ED25519_PUBLIC_KEYS_JSON`

## Vault Configuration
- `GREENOS_VAULT_ADDR`
- `GREENOS_VAULT_TOKEN`
- `GREENOS_VAULT_PATH`
- `GREENOS_SECRET_CACHE_TTL_SECONDS` (optional, default `0`)

Expected Vault payload at `GREENOS_VAULT_PATH`:
- One object containing keys named exactly like required GreenOS secret names.

## KMS Configuration (Stub Contract)
- `GREENOS_KMS_KEY_ID`
- `GREENOS_KMS_PROVIDER=aws|gcp|generic`
- `GREENOS_KMS_REGION`

Notes:
- The KMS provider intentionally avoids hard cloud dependencies.
- Wire provider-specific decrypt adapters before production rollout.

## Production Fail-Closed Rules
- In `ENVIRONMENT=production|prod`, startup fails if:
  - Required signing secret is missing or invalid.
  - HMAC secret is placeholder.
  - Active Ed25519 private/public key is missing, placeholder, or invalid.
  - Secret provider `vault/kms` cannot return required secret material.

## Rotation Procedure (HMAC + Ed25519)
1. Add new key version entries in `*_KEYS_JSON`.
2. Set active versions:
   - `GREENOS_SIGNING_ACTIVE_KEY_VERSION`
   - `GREENOS_ED25519_ACTIVE_KEY_VERSION`
3. Update active key material:
   - `GREENOS_SIGNING_SECRET`
   - `GREENOS_ED25519_PRIVATE_KEY`
   - `GREENOS_ED25519_PUBLIC_KEY`
4. Restart service.
5. Validate:
   - `GET /api/v2/esg/public-key`
   - `GET /.well-known/greenos-public-key`
   - `GET /api/v2/esg/internal/secrets/status` (admin only)

## Operational Verification
- `GET /api/v2/esg/internal/secrets/status` returns only:
  - provider name
  - cache TTL
  - per-secret state: `OK`, `MISSING`, `INVALID`
- No secret values are exposed in API or logs.
