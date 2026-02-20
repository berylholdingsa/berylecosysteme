# AML Process Description

- Every transaction is scored in backend (`TransactionRiskScorer`).
- Controls include velocity, threshold amount, sanctions, anomaly detection.
- Flagged transactions are persisted in `suspicious_activity_logs`.
- Suspicious events are emitted to Kafka topic `fintech.suspicious.activity`.
- Metrics: `aml_flagged_total`, `beryl_fintech_risk_score_avg`.
