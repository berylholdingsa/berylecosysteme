# GreenOS Ed25519 Key Rotation Runbook

## Objective
- Keep GreenOS signatures externally verifiable during key rotation.
- Preserve backward verification for historical ledger and MRV records.

## Required Environment Variables
- `GREENOS_ED25519_ACTIVE_KEY_VERSION`
- `GREENOS_ED25519_PRIVATE_KEY`
- `GREENOS_ED25519_PUBLIC_KEY`
- `GREENOS_ED25519_PRIVATE_KEYS_JSON`
- `GREENOS_ED25519_PUBLIC_KEYS_JSON`

## Rotation Procedure
1. Generate a new Ed25519 keypair in a managed secret system (Vault or KMS-backed workflow).
2. Keep old keys in `GREENOS_ED25519_PRIVATE_KEYS_JSON` and `GREENOS_ED25519_PUBLIC_KEYS_JSON`.
3. Add the new keypair in both keyrings under the new version (example: `v3`).
4. Switch `GREENOS_ED25519_ACTIVE_KEY_VERSION` to the new version.
5. Set `GREENOS_ED25519_PRIVATE_KEY` and `GREENOS_ED25519_PUBLIC_KEY` to the new active key material.
6. Restart GreenOS service and validate:
   - `GET /api/v2/esg/public-key`
   - `GET /.well-known/greenos-public-key`
   - Existing records still verify (`/api/v2/esg/verify/{trip_id}` and MRV verify endpoint).
7. After retention window, remove deprecated key versions from keyrings.

## Production Safety
- GreenOS startup fails in `production/prod` if:
  - HMAC secret is missing/placeholder.
  - Active Ed25519 private/public key is missing, invalid, or placeholder.
- This enforces fail-closed behavior before any ESG signing operation.
