# Horizontal worker scaling blueprint

## Principe
Scalabilité horizontale par workers stateless consommant Kafka avec commits manuels.

## Seuils de scaling
- Scale out si lag > 500 pendant 2 min.
- Scale out immediat si lag > 1000.
- Scale in uniquement si lag < 100 pendant 10 min.

## Capacites
- Worker baseline: 150 tx/s stable.
- Worker peak court: 220 tx/s.
- Cible initiale: 20 workers pour 3000 tx/s soutenu.

## Conditions de qualite
- p95 API < 300 ms.
- DLQ stable (0 en regime nominal).
- Aucun echec signature/HMAC non explique.
