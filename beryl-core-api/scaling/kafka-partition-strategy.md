# Kafka partition strategy (fintech)

## Objectifs
- Supporter la montee en charge sans perte d'ordre logique par compte.
- Limiter le consumer lag en conservant une distribution homogene.
- Preserver la tolerance panne (RF=3, min ISR=2).

## Strategie
- Topic critiques: `fintech.transaction.completed`, `fintech.suspicious.activity`, `fintech.payment.failed`.
- Cle de partition: `actor_id` ou `wallet_id` selon domaine metier.
- Partition count initial recommande:
  - `fintech.transaction.completed`: 96
  - `fintech.suspicious.activity`: 48
  - `fintech.payment.failed`: 24
- Ajustement trimestriel base sur p95 lag et volume horaire.

## Regles
- Interdiction auto-create topics en production.
- Toute augmentation de partitions doit etre accompagnee d'un test de reequilibrage.
- Alerting critique au-dela de 1000 messages de lag cumule par groupe.
