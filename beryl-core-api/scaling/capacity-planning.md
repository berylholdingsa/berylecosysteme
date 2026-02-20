# Capacity planning (fintech)

## Hypotheses
- Pic intraday: 5x baseline.
- Mix operationnel: 85% paiements, 10% remboursements, 5% alerts AML.
- Objectif: absorber 2000 tx/s en pointe sans rupture de conformite.

## Capacite cible
- API nodes: 12 instances min (autoscale jusqu'a 30).
- Workers Kafka: 20 min (scale vers 50).
- Postgres: primaire + 2 replicas avec Pgpool.
- Kafka: 3 brokers, replication factor 3.

## Marges
- CPU steady-state cible: < 70%.
- CPU en pic accepte: < 85%.
- Memoire steady-state cible: < 75%.
- Memoire en pic accepte: < 85%.

## Plan d'expansion
1. Monter partitions Kafka.
2. Augmenter workers consommateurs.
3. Ajouter shards transactions.
4. Revalider SLA p95 et integrite audit chain.
