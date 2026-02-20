# GreenOS MRV Methodology

Version: 2026-02-17
Scope: GreenOS ESG v2 MRV computation and verification rules

## 1. Baseline definition
Baseline principle:
- estimate emissions from a thermal mobility counterfactual over the same distance.

Operational baseline in GreenOS:
- trip-level baseline uses `thermal_factor_local` by country.
- avoided emissions are computed against EV equivalent (`ev_factor_local`).

Default baseline reference in configuration:
- `GREENOS_MRV_BASELINE_REFERENCE=distance_km * thermal_factor_local baseline`

## 2. Emission factors
Source model:
- country-level factors are loaded from `GREENOS_COUNTRY_FACTORS_JSON`.
- each country must expose:
  - `thermal_factor_local`
  - `ev_factor_local`

Validation rules:
- country code must be ISO alpha-2 format.
- thermal factor must be strictly positive.
- EV factor must be non-negative.
- missing country factors trigger fail-fast (`GREENOS_COUNTRY_FACTOR_NOT_CONFIGURED`).

## 3. Geographic scope
Methodology scope is declared per version (`geographic_scope`) in the MRV methodology registry.

Rules:
- scope is explicit (example: `CI,SN,KE`).
- export is blocked if scope references countries not documented in configured factors.
- no silent fallback factors are allowed.

## 4. Core formulas
### 4.1 Trip-level avoided emissions
`co2_avoided_kg = distance_km * thermal_factor_local - distance_km * ev_factor_local`

Implementation details:
- computed in real-time engine.
- rounded to 6 decimals for deterministic downstream behavior.

### 4.2 Integrity hashes
Trip-level:
- `event_hash = SHA256(canonical payload fields)`
- `checksum = SHA256({event_hash, trip_id, model_version, country_code})`

MRV-level:
- `verification_hash = SHA256(canonical strict JSON payload)`

### 4.3 Signatures
Trip and MRV hashes are signed with:
- HMAC-SHA256 (`signature`, `signature_algorithm`, `key_version`)
- Ed25519 (`asym_signature`, `asym_algorithm`, `asym_key_version`)

## 5. MRV aggregation model
Periods:
- `3M` (90 days)
- `6M` (180 days)
- `12M` (365 days)

Aggregation outputs:
- `total_distance_km`
- `total_co2_avoided_kg`
- `impacts_count`
- methodology metadata snapshot
- anti double counting proof

MRV payload contains:
- period bounds and generation timestamp
- methodology block
- country factors actually used
- model versions encountered
- impact list with cryptographic attributes
- dedup proof object

## 6. Canonical JSON and determinism
GreenOS MRV canonicalization enforces:
- sorted keys
- stable JSON separators
- decimal normalization via quantization
- stable hash generation over normalized content

Consequence:
- same logical input produces the same canonical JSON and same hash.

## 7. Versioning rules
Methodology registry model:
- unique `methodology_version`
- status in `ACTIVE | DEPRECATED`
- one ACTIVE version at a time (conflict on second ACTIVE insert)

Binding controls:
- each export carries `methodology_version` and `methodology_hash`.
- verification recomputes methodology hash from registry state.
- mismatch sets `methodology_valid = false`.

## 8. Non-double-counting controls
### 8.1 Ledger-level uniqueness
Unique key:
- `(trip_id, model_version)`

### 8.2 Export-level deduplication
Rule:
- keep latest record per `trip_id` (based on creation order logic in engine).

Proof fields:
- `raw_impacts_count`
- `selected_impacts_count`
- `duplicates_removed_count`
- `duplicate_trip_ids`
- `duplicate_trip_frequencies`
- `deduplication_rule`
- `proof_hash`
- `double_counting_blocked`

### 8.3 Export-period uniqueness
Unique key:
- `(period_start, period_end)`

Effect:
- duplicate publication of the same canonical period returns conflict.

## 9. Quality controls
### 9.1 Input and schema controls
- strict request schemas (`extra=forbid`, strict types).
- explicit errors for invalid/missing fields.

### 9.2 Cryptographic controls
- hash and checksum verification.
- HMAC and Ed25519 verification gates in API verify endpoints.
- public-key publication for independent asymmetric verification.

### 9.3 Methodology controls
- export blocked when baseline or references are empty.
- export blocked when documented country factors are incomplete.
- methodology mismatch counted as verification failure.

### 9.4 Operational controls
- outbox relay retries with exponential backoff.
- DLQ fallback after retry exhaustion.
- Prometheus counters/gauges for MRV and outbox health.

## 10. Known constraints and assumptions
- The methodology verifies internal consistency and tamper resistance, not direct physical truth of external sensor sources.
- Country factors must be governed and periodically reviewed by a designated authority.
- Deduplication is ID-based; upstream identity governance remains critical.

## 11. Change log policy
For each methodology release:
1. increment `methodology_version`.
2. document updated baseline and factor references.
3. validate scope-country coverage.
4. publish migration and backward-compatibility impact.
5. keep prior version accessible as `DEPRECATED` for audit replay.
