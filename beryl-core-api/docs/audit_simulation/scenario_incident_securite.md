# Scenario incident securite

## Incident
Tentative de replay massif sur webhook PSP avec signatures alterees.

## Detection
- `SignatureFailureAnomaly` > seuil
- `PSPReplayDetectionAnomaly` active
- Augmentation `security_incident_total`

## Containment
- Blocage source au WAF/API gateway
- Rotation des secrets HMAC impactes
- Passage des flux PSP en mode verification renforcee

## Eradication
- Purge des notifications non conformes
- Relecture des evenements outbox et DLQ

## Recovery
- Reprise graduelle avec monitoring p95 et lag Kafka
- Validation integrite audit chain post-incident
