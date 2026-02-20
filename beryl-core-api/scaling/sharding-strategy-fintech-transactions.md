# Sharding strategy fintech transactions

## Cible
Sharder les transactions fintech pour absorber les pics sans degrader l'integrite comptable.

## Clé de shard
- Primaire: hash(`actor_id`) modulo N shards.
- Fallback: hash(`wallet_id`) en cas de federation multi-comptes.

## Topologie initiale
- 4 shards logiques (S0..S3) en staging,
- 8 shards logiques cible en production banque partenaire,
- 16 shards prepare pour hyper-scale (phase VC Serie A+).

## Garde-fous
- Idempotency key scope = shard + actor_id.
- Audit chain ancree par shard avec verification globale periodique.
- Migrations de shard uniquement hors fenetres de clearing critique.
