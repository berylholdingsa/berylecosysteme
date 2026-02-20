# Plan reprise sinistre

## Objectifs
- RPO <= 5 min
- RTO <= 30 min

## Strategie
- Kafka replication factor 3, min ISR 2
- Postgres HA avec primaire + replicas + pgpool
- Sauvegardes et tests de restauration periodiques

## Procedure
1. Declaration incident et bascule cellule de crise.
2. Verification etat Kafka/Postgres HA.
3. Restauration selective si corruption.
4. Verification integrite audit chain.
5. Reprise progressive avec surveillance DLQ/latence.
