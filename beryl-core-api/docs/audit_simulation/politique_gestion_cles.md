# Politique gestion cles

## Principes
- Rotation automatique des cles tous les 90 jours.
- Separation des cles par environnement (prod/staging).
- Stockage via backend secrets manager abstrait (Vault-compatible).

## Mise en oeuvre
- Script: `infra/key-rotation-cron.sh`
- Policy d'acces: `infra/vault-policy.hcl`
- Trace operationnelle: journal JSON structure.

## Controles
- Simulation de rotation en CI
- Verification stricte via `tools/BankAuditSimulator.py`
