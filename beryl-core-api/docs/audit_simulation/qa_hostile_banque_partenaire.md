# Q&A hostile banque partenaire

## Q1. Comment prouvez-vous l'immutabilite de la piste d'audit ?
- Chaque evenement financier est chaine par `previous_hash` + `current_hash` signe en HMAC.
- Un test d'integrite de chaine est execute en CI et en staging.
- Une alerte critique `AuditIntegrityFailure` est declenchee au premier echec.

## Q2. Que se passe-t-il si la signature PSP est invalide ?
- Rejet immediate du message.
- Incrementation de la metrique `signature_validation_failures_total`.
- Routage DLQ et alerte `SignatureFailureAnomaly`.

## Q3. Comment evitez-vous les secrets en clair ?
- Aucun secret applicatif n'est versionne.
- Les variables sensibles sont injectees au runtime.
- La politique `infra/vault-policy.hcl` borne strictement les chemins autorises.

## Q4. Comment detectez-vous un replay PSP ?
- Protection nonce/timestamp et verification HMAC.
- Alerte `PSPReplayDetectionAnomaly` sur incidents de replay.

## Q5. Comment gelez-vous un incident AML massif ?
- Spike AML detecte via `AMLSpikeAnomaly`.
- Escalade automatique au plan de reponse fraude.
