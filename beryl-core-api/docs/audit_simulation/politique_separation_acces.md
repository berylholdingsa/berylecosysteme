# Politique separation acces

## Separation par environnement
- Reseaux et stacks distincts: `docker-compose.prod.yml` vs `docker-compose.staging.yml`.
- Groupes Kafka et bases de donnees isoles.

## Separation des privileges
- Least privilege applique aux policies secrets.
- Acces production reserve roles valides.
- Acces staging autorise uniquement pour validation reglementaire.

## Gouvernance
- Revue periodique des droits.
- Journalisation structuree des operations sensibles.
- Interdiction de bypass signature et de secrets en clair.
