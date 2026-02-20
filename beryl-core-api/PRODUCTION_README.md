# Beryl Core API - Production Ready

## Vue d'ensemble
API FastAPI multi-domaines (Fintech, Mobilité, ESG, Social) avec sécurité Zero-Trust, observabilité complète et résilience.

## Sécurité Zero-Trust
- Authentification par tokens JWT avec scopes par domaine
- Rate-limiting (100 req/min par IP)
- Logs sécurité pour 401/403
- Fallback si services externes indisponibles
- Isolation réseau avec NetworkPolicies K8s

## Observabilité
- OpenTelemetry : traces (Jaeger/Zipkin), métriques (Prometheus), logs
- Dashboards Grafana pour monitoring
- Audit logging centralisé

## Déploiement
1. Pipeline CI/CD GitHub Actions : tests Zero-Trust, lint, build Docker
2. Image Docker légère, versionnée
3. Déploiement K8s avec secrets, autoscaling, health checks

## Tests
- Tests unitaires et intégration
- Tests Zero-Trust async multi-domaines
- Tests de charge et résilience

### Gateway Layer – Politique de tests

Les tests de rejet (401 / 403) sont exécutés en CI et bloquent les merges.

Les tests positifs (accepts_valid_scope) sont validés uniquement :

- en environnement d’intégration
- avec microservices réels OU stubs avancés

Cette séparation est volontaire pour préserver :

- le Zero-Trust
- la résilience
- la testabilité du core

## Commandes
```bash
# Tests
pytest tests/integration/test_multi_domain_zero_trust.py -v --asyncio-mode=auto

# Build Docker
docker build -t beryl-core-api .

# Déploiement staging
./deploy_staging.sh

# Monitoring
kubectl port-forward svc/prometheus 9090:9090
kubectl port-forward svc/grafana 3000:3000
```

## Configuration
- Variables d'environnement dans `config/settings.py`
- Secrets K8s dans `k8s/secrets/`
- OpenTelemetry dans `src/observability/opentelemetry_config.py`

## Maintenance
- Ajouter tests pour nouveaux endpoints/domaines
- Mettre à jour couverture Zero-Trust
- Centraliser logs dans tableau de bord sécurité