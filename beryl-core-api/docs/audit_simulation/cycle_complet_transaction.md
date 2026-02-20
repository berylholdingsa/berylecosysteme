# Cycle complet transaction

1. Reception transaction avec correlation ID, nonce, timestamp et idempotency key.
2. Verification signature + controles anti-replay.
3. Evaluation AML (montant, velocite, sanctions, anomalies).
4. Ecriture transaction + evenement d'audit chaine immuable.
5. Publication outbox vers Kafka (ou routage DLQ en cas d'echec de conformite).
6. Exposition metriques et evaluation des alertes critiques.
7. Archivage traces pour audit interne/externe.
