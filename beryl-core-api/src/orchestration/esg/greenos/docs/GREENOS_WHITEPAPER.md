# GreenOS - MRV & Crypto Audit-Ready

Version: 2026-02-17
Audience: Ministeres, collectivites, fonds climat, auditeurs techniques et bailleurs
Scope: GreenOS ESG v2 (ledger, MRV, signatures, outbox, observabilite)

## 1. Executive Summary
GreenOS est une infrastructure ESG orientee preuve, construite pour produire des impacts carbone verifiables, exportables en MRV, et auditables sans dependance a une confiance implicite dans l'operateur.

Le systeme combine:
- un ledger append-only pour les impacts unitaires;
- une generation MRV canonique et versionnee;
- une double signature cryptographique (HMAC-SHA256 + Ed25519);
- une publication de cle publique pour verification externe independante;
- un outbox transactionnel avec retry, DLQ et metriques.

Objectif institutionnel:
- reduire les risques de contestation d'impacts;
- permettre un audit externe reproductible;
- fournir une base de confiance pour des programmes PPP, municipaux et climate-finance.

## 2. Vision et cas d'usage PPP / Communes
### 2.1 Problematique publique
Les programmes de transition (mobilite propre, electrification, substitutions thermiques) souffrent souvent de trois faiblesses:
- preuve insuffisante de l'impact;
- methodes heterogenes non comparables;
- gouvernance faible sur la chaine de calcul et de signature.

### 2.2 Positionnement GreenOS
GreenOS impose une logique de "preuve d'abord":
- chaque impact unitaire est calcule, hash, signe et persiste de facon immuable;
- chaque export MRV est construit de facon deterministe sur un JSON canonique;
- chaque verification peut etre rejouee.

### 2.3 Cas d'usage cibles
- Programme municipal de reduction CO2: reporting trimestriel/semestre/annuel.
- Dossier de financement Fonds Vert: export MRV versionne, signatures verifiables.
- Due diligence VC climate-tech: verification de non-repudiation et anti-tampering.
- Reporting ministeriel inter-communes: harmonisation par version de methodologie.

## 3. Architecture de reference
### 3.1 Composants structurants
- `esg_impact_ledger`: impacts unitaires append-only.
- `esg_audit_metadata`: snapshots d'audit append-only.
- `esg_mrv_exports`: exports MRV materialises.
- `esg_mrv_methodology`: registre de methodologie versionnee.
- `esg_outbox_events`: outbox transactionnel pour emission evenementielle fiable.

### 3.2 Flux principal
1. Ingestion d'un evenement de trajet ESG.
2. Calcul CO2 evite et production `event_hash` + `checksum`.
3. Signature HMAC et signature Ed25519.
4. Ecriture en ledger append-only.
5. Enqueue outbox dans la meme transaction.
6. Relay outbox vers bus d'evenements, avec retry/backoff ou DLQ.
7. Export MRV periodique et verification cryptographique.

### 3.3 Garantie d'immutabilite
Le modele bloque les operations `UPDATE` et `DELETE` sur:
- `esg_impact_ledger`;
- `esg_audit_metadata`.

Cela force un paradigme append-only: la correction fonctionnelle se fait par nouvelle ecriture, pas par mutation retroactive.

### 3.4 Contrats d'evenements
Topics versionnes:
- `trip_completed.v1`
- `esg_calculated.v1`
- `audit_generated.v1`
- DLQ: `esg_greenos.dlq.v1`

Les enveloppes sont strictes (schema versionne, validation pydantic stricte).

## 4. MRV: export, versioning, canonique
### 4.1 Periodes MRV
GreenOS supporte:
- `3M`
- `6M`
- `12M`

Chaque export inclut bornes temporelles, aggregation, impacts unitaires et preuves anti double comptage.

### 4.2 Canonical JSON
Le hash MRV (`verification_hash`) est calcule sur une serialisation canonique stricte:
- tri deterministe des cles;
- normalisation numerique deterministe (Decimal quantize);
- separateurs stables.

Resultat: meme payload logique => meme hash.

### 4.3 Methodologie versionnee
Le registre MRV impose:
- unicite de `methodology_version`;
- statut `ACTIVE` ou `DEPRECATED`;
- un seul `ACTIVE` a la fois.

L'export embarque:
- `methodology_version`;
- `methodology_hash`;
- references baseline/facteurs.

La verification MRV controle aussi le binding entre export et methodologie active/resolue.

### 4.4 Verification MRV
Un export est valide si et seulement si:
- `hash_valid = true`;
- `signature_valid = true` (HMAC);
- `asym_signature_valid = true` (Ed25519);
- `methodology_valid = true`.

## 5. Securite et non-repudiation
### 5.1 Double signature
GreenOS maintient deux plans cryptographiques complementaires:
- Signature symetrique HMAC-SHA256 (continuites internes et rotation historique).
- Signature asymetrique Ed25519 (verification externe par cle publique).

La signature HMAC n'est pas retiree. Elle coexiste avec Ed25519.

### 5.2 Verification externe independante
Un auditeur externe peut verifier Ed25519 sans secret partage en utilisant:
- `GET /api/v2/esg/public-key`
- `GET /.well-known/greenos-public-key`

Payload cle publique:
- `public_key` (base64)
- `fingerprint_sha256`
- `signature_algorithm`
- `key_version`
- `encoding`

### 5.3 Rotation de cles
Rotation HMAC et Ed25519 supportee via:
- `*_ACTIVE_KEY_VERSION`
- `*_KEYS_JSON` (historique multi-version)

La verification tente d'abord la version demandee, puis les cles disponibles.

### 5.4 Secrets runtime institutionnels
Providers runtime:
- `env` (dev/staging)
- `vault` (prod)
- `kms` (interface generique prete a integrer)

En `production/prod`, comportement fail-closed:
- demarrage refuse si secret critique manquant/invalide/placeholder.
- endpoint interne admin de statut non sensible:
  - `GET /api/v2/esg/internal/secrets/status`

## 6. Anti double comptage: preuves et contraintes
### 6.1 Niveau ledger
Contrainte d'unicite:
- `(trip_id, model_version)` unique.

Cela bloque le double insert exact sur meme version de modele.

### 6.2 Niveau MRV
Lors de l'export:
- les lignes sont dedupliquees par `trip_id`;
- regle appliquee: conservation de l'enregistrement le plus recent;
- `non_double_counting_proof` fournit:
  - nombre brut;
  - nombre retenu;
  - nombre supprime;
  - IDs dupliques;
  - frequence des duplicats;
  - `proof_hash`.

### 6.3 Niveau periode
Contrainte d'unicite MRV:
- `(period_start, period_end)` unique.

Cela empeche de publier deux exports pour la meme fenetre canonique.

## 7. Observabilite et supervision
### 7.1 Metriques MRV
- `greenos_mrv_exports_total`
- `greenos_mrv_verification_failures_total`
- `greenos_mrv_methodology_version_active{methodology_version=...}`
- `greenos_mrv_methodology_mismatch_total`

### 7.2 Metriques outbox
- `greenos_outbox_pending`
- `greenos_outbox_retry_total`
- `greenos_outbox_failed_total`

### 7.3 Comportement resilience
Le relay outbox applique:
- backoff exponentiel;
- seuil max retry configurable;
- bascule DLQ + marquage `FAILED`;
- `skip_locked` en PostgreSQL pour securiser le multi-worker.

## 8. Gouvernance et runbooks
### 8.1 Runbooks disponibles
- `ed25519_rotation_runbook.md`
- `public_key_publication.md`
- `secret_provider_runbook.md`

### 8.2 Politique de gouvernance clefs
- versionnement obligatoire des cles;
- publication du fingerprint a chaque rotation;
- conservation des anciennes versions pendant la fenetre d'audit;
- tests de verification apres rotation.

### 8.3 Separation des responsabilites
Pratique recommandee:
- equipe data/methodologie responsable des versions MRV;
- equipe securite responsable rotation secrets/cles;
- equipe audit responsable verification independante.

## 9. Limites et hypotheses (honnetete audit)
### 9.1 Limites assumees
- GreenOS prouve l'integrite et la non-alteration des donnees traitees, pas la veracite physique intrinseque de chaque source amont.
- La qualite des facteurs pays depend de la gouvernance du referentiel `GREENOS_COUNTRY_FACTORS_JSON`.
- La deduplication MRV est par `trip_id` (regle explicite); une fraude sur identifiants amont reste un risque organisationnel.

### 9.2 Hypotheses de confiance minimales
- identite technique de l'emetteur d'evenement d'origine;
- controle d'acces API et journalisation operationnelle;
- gestion des secrets conforme au runbook.

### 9.3 Risques residuels
- erreurs semantiques metier non detectees par cryptographie pure;
- incidents d'horodatage ou de synchronisation systemes amont;
- mauvaise hygiene de rotation si runbook non applique.

## 10. Roadmap 12 mois
### Trimestre 1
- durcissement de l'operabilite production (SLO/SLA, alertes).
- formalisation complete du dossier "preuve anti fraude".
- publication cadencee de fingerprints de cles.

### Trimestre 2
- enrichissement des controles methodology (qualite facteurs, derive detection).
- pack audit externe standardise (scripts de verification fournis).
- extension des artefacts MRV pour reporting bailleurs multi-formats.

### Trimestre 3
- resilience avancee (tests de chaos outbox/DLQ et recovery drills).
- evidence store signe pour piste d'audit longue retention.
- integration CI de verification cryptographique cross-language.

### Trimestre 4
- couche IA ESG de confiance (scoring heuristique puis modele supervise).
- alignement cadres taxonomiques regionaux/internationaux.
- capacite "programme multi-communes" avec tableaux de bord institutionnels.

## 11. Mode operatoire institutionnel (PPP et communes)
### 11.1 Gouvernance programme
Un deploiement institutionnel GreenOS fonctionne avec trois instances de responsabilite:
- autorite metier (ministere, commune, syndicat mixte): valide objectifs, perimetre et publication;
- operateur technique: execute la chaine de calcul, de signature, d'export et d'archivage;
- organe de controle (audit interne/externe): verifie l'integrite, la methode et les preuves.

### 11.2 Cadence recommandee
- quotidien: monitoring outbox, erreurs verification, disponibilite endpoints.
- hebdomadaire: revue anomalies de verification et hygiene de secrets.
- mensuelle: revue metriques MRV/outbox et coherence de facteurs pays.
- trimestrielle: generation export MRV et kit audit.
- semestrielle: revue gouvernance de la methodologie et rotation planifiee des cles.

### 11.3 Evidence institutionnelle minimale
Pour chaque periode de reporting:
- export MRV signe (payload + metadata cryptographique);
- verification API positive;
- cle publique et fingerprint publies;
- preuve de version methodology (`methodology_version` + `methodology_hash`);
- extrait de logs et metriques operationnelles.

## 12. Cycle de vie de la donnee et tracabilite
### 12.1 Entree
Un evenement de trajet est recu avec:
- identifiants (`trip_id`, `user_id`, `vehicle_id`);
- contexte (`country_code`, `geo_hash`, `event_timestamp`);
- mesure principale (`distance_km`).

### 12.2 Transformation
Le moteur temps reel produit:
- `co2_avoided_kg`;
- `event_hash`;
- `checksum`;
- signatures HMAC et Ed25519 + versions de cle.

### 12.3 Persistance
L'impact est ecrit en ledger append-only avec horodatage et correlation ID.
Une entree outbox est ecrite dans la meme transaction pour fiabiliser l'emission event-driven.

### 12.4 Exploitation MRV
L'export MRV:
- recalcule une vue periodique;
- deduplique les trips selon regle explicite;
- construit un JSON canonique;
- signe le `verification_hash`;
- persiste un snapshot materialise.

### 12.5 Verification et audit
Les endpoints de verification rejouent les controles:
- integrite hash/checksum;
- validite signatures;
- validite binding methodologique.

## 13. Modele de menace et controles
### 13.1 Menaces considerees
- alteration malveillante du payload apres generation;
- substitution de signatures;
- publication de faux export sans correspondance methodologique;
- indisponibilite du bus evenements provoquant perte silencieuse;
- mauvaise hygiene de secret management.

### 13.2 Controles techniques
- hash deterministe et checksum;
- double signature independante (symetrique + asymetrique);
- verification stricte avant statut "verified";
- outbox transactionnel + retry + DLQ;
- demarrage fail-closed en production si secrets invalides.

### 13.3 Controles organisationnels recommandes
- separation des droits de rotation cles / publication MRV;
- double validation humaine pour changement de methodologie active;
- revue croisee trimestrielle entre equipe metier et equipe securite;
- archivage des preuves d'audit sur retention longue.

### 13.4 Ce que GreenOS ne pretend pas couvrir seul
- authenticite physique du capteur amont;
- prevention totale de fraude identitaire externe;
- elimination de toute erreur de gouvernance hors systeme.

## 14. Blueprint de deploiement institutionnel
### 14.1 Environnement cible
- environnement production segmente;
- secret provider `vault` ou `kms`;
- supervision continue metrics/logs/traces;
- sauvegarde et retention de preuves.

### 14.2 Parametres critiques
- `GREENOS_SECRET_PROVIDER`
- `GREENOS_SIGNING_*`
- `GREENOS_ED25519_*`
- `GREENOS_COUNTRY_FACTORS_JSON`
- `GREENOS_OUTBOX_*`

### 14.3 Sequence de mise en service
1. charger facteurs pays et methode active.
2. configurer provider de secrets runtime.
3. valider endpoint public key et well-known.
4. executer tests d'integrite (trip + MRV).
5. activer publication operationnelle.

### 14.4 Sequence de reprise incident
1. identifier type incident (donnee, secret, outbox, methode).
2. geler publication externe si verification invalide.
3. corriger configuration ou gouvernance.
4. rejouer verifications sur echantillon representatif.
5. publier rapport d'incident avec impact et corrections.

## 15. Assurance package pour parties prenantes
### 15.1 Pour un ministere
Points de decision:
- conformite procedurale;
- reproductibilite des calculs;
- existence de controle anti-tampering;
- capacite de controle independant.

### 15.2 Pour un Fonds Vert
Points de decision:
- qualite et stabilite MRV;
- robustesse governance methodologique;
- disponibilite d'un dossier de preuve auditable;
- risque operationnel residuel explicite.

### 15.3 Pour un VC climate-tech
Points de decision:
- defensabilite technique face a due diligence hostile;
- capacite de scale sans perte d'integrite;
- clarte de roadmap et trajectoire de maturite.

### 15.4 Dossier evidence standard (proposition)
- extrait ledger signe;
- export MRV signe;
- rapport verification API;
- fingerprint cle publique publie;
- etat provider de secrets (non sensible);
- set metriques periode.

## 16. Glossaire operationnel
- Append-only: ecriture sans modification/suppression retroactive.
- MRV: Measurement, Reporting, Verification.
- Canonical JSON: representation deterministe d'un payload.
- Verification hash: hash de reference d'un export MRV canonique.
- Methodology hash: hash du descripteur de methode appliquee.
- DLQ: Dead Letter Queue pour evenements non publiables apres retries.
- Fail-closed: refus de demarrer/operer en cas de configuration de securite invalide.
- Non-repudiation: capacite a prouver qu'un artefact a ete signe par une cle donnee.

## 17. Conclusion
GreenOS fournit un socle institutionnel concret:
- immuable;
- versionne;
- signe symetriquement et asymetriquement;
- verifiable independamment;
- exploitable pour finance climat et controle public.

L'etape technique est franchie. La prochaine valeur strategique est la standardisation des pratiques d'audit et de gouvernance sur ce socle.

## 18. Annexe - matrice de tracabilite implementation
Cette matrice lie les affirmations du whitepaper a des artefacts techniques concrets.

### 18.1 Immutabilite append-only
- modele ledger append-only:
  - `src/db/models/esg_greenos.py` (`EsgImpactLedgerModel`)
- blocage update/delete:
  - `src/db/models/esg_greenos.py` listeners `before_update`/`before_delete`

### 18.2 Signature double plan
- service signature HMAC + Ed25519:
  - `src/orchestration/esg/greenos/services/signing.py`
- stockage signatures symetrique et asymetrique:
  - `src/db/models/esg_greenos.py` colonnes `signature*` et `asym_*`

### 18.3 Publication cle publique
- endpoint public API:
  - `src/orchestration/esg/greenos/api/router.py` (`/public-key`)
- endpoint well-known:
  - `src/main.py` (`/.well-known/greenos-public-key`)

### 18.4 Verification independante
- verification trip:
  - `src/orchestration/esg/greenos/services/greenos_service.py` (`verify_trip_signature`)
- verification MRV:
  - `src/orchestration/esg/greenos/services/greenos_service.py` (`verify_mrv_export`)
- helper verification Ed25519 public key only:
  - `src/orchestration/esg/greenos/services/signing.py` (`verify_hash_with_public_key`)

### 18.5 Canonical MRV hashing
- canonical strict JSON:
  - `src/orchestration/esg/greenos/mrv/canonical.py`
- hash export MRV:
  - `src/orchestration/esg/greenos/mrv/engine.py` (`sha256_hex_strict`)

### 18.6 Methodologie versionnee
- repository methodologie:
  - `src/orchestration/esg/greenos/mrv/methodology_repository.py`
- contrainte active unique:
  - verification conflit `ACTIVE` dans `create_in_session`
- hash methodologie:
  - `src/orchestration/esg/greenos/mrv/engine.py` (`methodology_hash`)

### 18.7 Anti double comptage
- unicite ledger:
  - `src/db/models/esg_greenos.py` `uq_esg_impact_trip_model`
- dedup export par trip:
  - `src/orchestration/esg/greenos/mrv/engine.py` (`_deduplicate_trip_records`)
- preuve dedup:
  - `non_double_counting_proof` dans payload MRV

### 18.8 Outbox transactionnel et DLQ
- persistence outbox:
  - `src/orchestration/esg/greenos/outbox/repository.py`
- relay retry/backoff/DLQ:
  - `src/orchestration/esg/greenos/outbox/relay_service.py`
- topic DLQ:
  - `src/orchestration/esg/greenos/contracts/kafka.py` (`esg_greenos.dlq.v1`)

### 18.9 Observabilite
- metriques MRV:
  - `src/orchestration/esg/greenos/mrv/metrics.py`
- metriques outbox:
  - `src/orchestration/esg/greenos/outbox/metrics.py`

### 18.10 Secret management runtime
- providers runtime:
  - `src/orchestration/esg/greenos/secrets/`
- wiring signature service:
  - `src/orchestration/esg/greenos/services/signing.py`
- endpoint statut non sensible admin:
  - `src/orchestration/esg/greenos/api/router.py` (`/internal/secrets/status`)

### 18.11 API publique ESG v2
- routes GreenOS:
  - `src/orchestration/esg/greenos/api/router.py`
- schemas stricts de reponse:
  - `src/orchestration/esg/greenos/schemas/responses.py`

### 18.12 Evidence de tests unitaires
- suite unitaire GreenOS:
  - `tests/unit/greenos/test_greenos_foundation.py`
- couverture explicite:
  - signatures valides;
  - detection tampering;
  - rotation de cles;
  - publication cle publique;
  - endpoint well-known;
  - statut secrets admin.

## 19. Cadre KPI / SLO institutionnel recommande
Cette section propose un cadre de pilotage quantitatif pour operationnaliser GreenOS dans un environnement public ou finance climat.

### 19.1 KPI d'integrite
- Taux de verification trip:
  - definition: pourcentage de `verify/{trip_id}` avec `verified=true`.
  - cible recommandee: >= 99.9%.
- Taux de verification MRV:
  - definition: pourcentage de `mrv/export/{export_id}/verify` avec `verified=true`.
  - cible recommandee: 100% avant publication institutionnelle.
- Taux d'echec methodologie:
  - definition: ratio des `methodology_valid=false`.
  - cible recommandee: 0 hors tests.

### 19.2 KPI de resilience pipeline
- Outbox pending backlog:
  - definition: valeur courante `greenos_outbox_pending`.
  - alerte: backlog croissant sur 3 fenetres consecutives.
- Retry rate:
  - definition: derivee de `greenos_outbox_retry_total`.
  - alerte: hausse soutenue > seuil operationnel local.
- Failed events:
  - definition: derivee de `greenos_outbox_failed_total`.
  - alerte critique: > 0 en production sur periode de reporting.

### 19.3 KPI de gouvernance methodologique
- Age de la methodologie ACTIVE:
  - definition: delai depuis `created_at` de la version active.
  - cible: revue obligatoire au moins semestrielle.
- Couverture geographique documentee:
  - definition: ratio pays dans scope avec facteurs valides.
  - cible: 100% avant export.

### 19.4 KPI de securite des secrets
- Secret status compliance:
  - definition: pourcentage de secrets critiques en statut `OK`.
  - cible: 100% en production.
- Rotation hygiene:
  - definition: respect du plan de rotation (versions publiees + runbook complete).
  - cible: 100% des rotations tracees et verifiees.

### 19.5 SLO de reference
- Disponibilite endpoints verification: >= 99.5% mensuel.
- Latence p95 verification trip: < 300 ms (cible initiale).
- Latence p95 verification MRV: < 500 ms (cible initiale).
- RTO incident outbox: < 4h.
- RPO de preuves MRV: 0 perte acceptee sur artefacts publies.

### 19.6 Gouvernance d'exception
Tout ecart majeur SLO/KPI doit produire:
1. qualification de severite;
2. analyse de cause racine;
3. plan d'action date et responsable;
4. revalidation cryptographique des artefacts impactes;
5. communication aux parties prenantes si impact reporting.

## 20. Interoperabilite et strategie d'adoption
### 20.1 Interoperabilite applicative
GreenOS est concu pour interoperer via:
- API REST versionnee (`/api/v2/esg/...`);
- contrats d'evenements versionnes (`*.v1`);
- formats JSON stables et hashes deterministes.

Ce triptyque facilite:
- integration avec plateformes de supervision publique;
- connexions a des data warehouses finance climat;
- tests de verification cross-language.

### 20.2 Interoperabilite d'audit
Un auditeur externe peut travailler sans acces au secret interne:
- cle publique publiee;
- fingerprint controle;
- payload MRV verifiable offline;
- regles de verification explicites.

Cette separation reduit:
- les conflits d'interet de verification;
- la dependance a l'operateur technique;
- les risques de contestation procedurale.

### 20.3 Parcours d'adoption recommande (6 phases)
Phase 1 - Cadrage:
- definir perimetre geographique et cas d'usage.
- designer gouvernance methodologie/secret/audit.

Phase 2 - Preparation:
- charger facteurs pays.
- initialiser methodology ACTIVE.
- configurer provider de secrets runtime.

Phase 3 - Validation pilote:
- executer flux trip -> ledger -> outbox -> MRV.
- verifier signatures HMAC et Ed25519.
- valider non-double-counting proof.

Phase 4 - Publication controlee:
- publier cle publique et fingerprint.
- produire premier export institutionnel.
- ouvrir verification externe supervisee.

Phase 5 - Industrialisation:
- activer SLA/SLO.
- renforcer alerting et runbooks.
- integrer audit periodique independant.

Phase 6 - Extension:
- multi-communes / multi-programmes.
- extension des formats de reporting.
- preparation IA ESG confidence layer.

### 20.4 Critere de maturite "audit-ready"
Un programme est considere audit-ready quand:
- verification cryptographique est reproductible;
- methodologie est versionnee et traceable;
- anti double comptage est prouve dans les exports;
- secret governance est fail-closed et documentee;
- observabilite fournit des indicateurs actionnables.

### 20.5 Effets attendus sur finance climat
- reduction du cout de due diligence technique;
- acceleration des cycles de validation bailleurs;
- meilleure comparabilite des rapports multi-projets;
- renforcement de la confiance sur les impacts declares.
