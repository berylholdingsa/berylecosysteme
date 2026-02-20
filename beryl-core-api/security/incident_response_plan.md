# Incident Response Plan

## Severity Levels
- `SEV-1`: financial integrity or data breach risk.
- `SEV-2`: service degradation or sustained queue lag.
- `SEV-3`: isolated failures without customer impact.

## Process
1. Detect via metrics/alerts (`security_incident_total`, `signature_validation_failures_total`, `dlq_events_total`).
2. Triage in <= 15 minutes.
3. Contain (block keys, isolate consumers, enforce fail-closed).
4. Eradicate root cause and replay safe backlog.
5. Recover with post-incident verification.
6. Postmortem in 48h with corrective actions.

## Regulatory Evidence
- Preserve immutable audit chain.
- Export correlation IDs and suspicious activity records.
- Retain incident timeline and remediation actions.
