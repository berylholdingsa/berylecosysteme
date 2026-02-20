# Sécurité Baseline - Beryl Core API v0.1-zero-trust-baseline

## Vue d'ensemble
Cette baseline représente l'état figé de la sécurité Zero-Trust pour beryl-core-api en tant qu'API Gateway. Elle garantit que seules les fonctionnalités de sécurité sont validées et opérationnelles.

## Périmètre de Garantie
La Gateway garantit exclusivement :
- **Authentification JWT** : Validation des tokens via IdP externe
- **Autorisation par scopes** : Contrôle d'accès par domaine (fintech, mobility, esg, social)
- **Rejet par défaut** : Tout accès non autorisé est bloqué (401/403)
- **Logging sécurité** : Traces d'audit pour tous les accès refusés
- **Rate-limiting** : Protection contre les abus (100 req/min/IP)

## Hypothèses
- **IdP fiable** : Les tokens JWT sont émis par un Identity Provider de confiance
- **Validité des tokens** : Les tokens sont vérifiés pour leur intégrité et expiration
- **Microservices externes** : Les services métier ne garantissent pas la sécurité (pas de confiance implicite)

## Limites Connues
- **Absence de logique métier** : La Gateway n'exécute aucune logique fonctionnelle
- **Tests positifs désactivés** : Les tests d'acceptation sont gelés hors environnement d'intégration
- **Dépendance aux stubs** : Les tests positifs nécessitent des microservices ou stubs avancés

## Couverture des Tests
### Tests Exécutés (Bloquants)
- `require_auth` : Rejet des requêtes sans token (401)
- `rejects_invalid_token` : Rejet des tokens malformés (401)
- `rejects_invalid_scope` : Rejet des tokens sans scope approprié (403)
- `security_logs_emitted` : Émission de logs pour accès refusé

### Tests Gelés (Non-bloquants)
- `accepts_valid_scope` : Acceptation des tokens valides (marqués @pytest.mark.skip)
- Raison : Nécessitent microservices actifs ou stubs contractuels

## Métriques de Sécurité
- **Tentatives d'accès refusées** : Comptabilisées dans les logs
- **Scopes invalides** : Tracés par domaine
- **Taux d'erreur authN/authZ** : Calculable via logs structurés

## Gouvernance
- **Versionnage** : Tag Git immuable `v0.1-zero-trust-baseline`
- **Audit** : Tous les changements post-baseline nécessitent validation sécurité
- **Rollback** : Possibilité de retour à cette baseline en cas de régression

## Conformité
Cette baseline assure la conformité aux principes Zero-Trust :
- Vérification continue
- Moins de privilèges
- Défense en profondeur

**Date de gel :** 5 janvier 2026
**Responsable :** CTO / Architecte Sécurité