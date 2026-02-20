# Beryl Core API - DevOps & Infrastructure

## Vue d'ensemble

Cette documentation couvre l'infrastructure complète DevOps pour déployer **beryl-core-api** en production avec Kubernetes, CI/CD, observabilité et sécurité.

## Architecture Infrastructure

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ingress       │    │  API Gateway    │    │  GraphQL        │
│   (nginx)       │────│  (FastAPI)      │────│  Gateway        │
│                 │    │                 │    │  (Graphene)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Event Bus      │    │  Adapters       │    │  Observability  │
│  (Kafka)        │    │  (External APIs)│    │  (Prometheus)   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Databases      │
                    │  (PostgreSQL)   │
                    │  (Redis)        │
                    └─────────────────┘
```

## Prérequis

### Outils Locaux
- **kubectl** >= 1.24
- **helm** >= 3.9
- **docker** >= 20.10
- **kustomize** (optionnel)

### Cluster Kubernetes
- **Kubernetes** >= 1.24
- **NGINX Ingress Controller**
- **cert-manager** pour TLS
- **Prometheus Operator** (optionnel mais recommandé)

### Registre Docker
- **GitHub Container Registry** (recommandé)
- **Docker Hub**
- **AWS ECR**
- **Google GCR**

## Structure des Fichiers

```
k8s/
├── namespaces/           # Namespaces par domaine
│   ├── fintech.yaml
│   ├── mobility.yaml
│   ├── esg.yaml
│   └── social.yaml
├── deployments/          # Déploiements applicatifs
│   ├── beryl-core-api-deployment.yaml
│   ├── graphql-gateway-deployment.yaml
│   └── event-bus-deployment.yaml
├── services/             # Services Kubernetes
├── ingress/              # Configuration Ingress
├── configmaps/           # Configuration non-sensible
├── secrets/              # Secrets (mots de passe, clés)
├── network-policies.yaml # Politiques réseau
├── pdb.yaml             # Pod Disruption Budgets
├── hpa.yaml             # Horizontal Pod Autoscalers
├── certificates.yaml     # Certificats TLS
├── monitoring-config.yaml # Configuration monitoring
└── pvc.yaml             # Volumes persistants

.github/workflows/       # Pipelines CI/CD
├── ci-cd.yml           # Pipeline principal
└── manual-deploy.yml   # Déploiement manuel

Dockerfile               # Image multi-stage
deploy.sh               # Script de déploiement automatisé
```

## Déploiement Rapide

### 1. Configuration
```bash
# Variables d'environnement
export NAMESPACE=default
export ENVIRONMENT=staging
export IMAGE_TAG=latest
export REGISTRY=ghcr.io
export REPO=generalhaypi/beryl_ecosysteme/beryl-core-api
```

### 2. Déploiement Automatique
```bash
# Déploiement complet
./deploy.sh

# Ou déploiement manuel étape par étape
kubectl apply -f k8s/namespaces/
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress/
```

### 3. Vérification
```bash
# Status des déploiements
kubectl get deployments -n default

# Status des pods
kubectl get pods -n default

# Logs d'un pod
kubectl logs -f deployment/beryl-core-api -n default

# Health checks
curl https://api.beryl-ecosystem.com/health
curl https://graphql.beryl-ecosystem.com/health
```

## Configuration Détaillée

### Variables d'Environnement

```bash
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO

# Métriques
METRICS_ENABLED=true

# Tracing
TRACING_ENABLED=true
JAEGER_HOST=jaeger.beryl-monitoring.svc.cluster.local

# Audit
AUDIT_ENABLED=true
AUDIT_LOG_FILE=/var/log/beryl/audit.log

# Event Bus
EVENT_BUS=kafka
KAFKA_BOOTSTRAP_SERVERS=kafka.default.svc.cluster.local:9092

# Secrets (via Kubernetes secrets)
JWT_SECRET_KEY=<from-secret>
DATABASE_PASSWORD=<from-secret>
```

### Secrets Management

Les secrets sont gérés via Kubernetes Secrets avec rotation automatique :

```bash
# Création d'un secret
kubectl create secret generic beryl-secrets \
  --from-literal=jwt-secret-key="$(openssl rand -hex 32)" \
  --from-literal=database-password="secure-password"

# Rotation d'un secret
kubectl patch secret beryl-secrets \
  --type='json' \
  -p='[{"op": "replace", "path": "/data/jwt-secret-key", "value":"'$(openssl rand -hex 32 | base64)'"}]'
```

## CI/CD Pipelines

### Pipeline Principal (ci-cd.yml)

```yaml
jobs:
  lint-test:        # Linting + Tests unitaires
  docker-build-push: # Build + Push image
  security-scan:    # Scan sécurité Trivy
  deploy-staging:   # Déploiement staging
  deploy-production: # Déploiement production
  monitoring-check: # Vérifications post-déploiement
```

### Déclencheurs
- **Push sur main/develop**: Pipeline complet
- **Pull Request**: Tests uniquement
- **Manual**: Déploiement manuel avec rollback

### Secrets GitHub Actions

```yaml
# Repository secrets requis
KUBE_CONFIG_STAGING: # kubeconfig staging
KUBE_CONFIG_PRODUCTION: # kubeconfig production
DOCKER_USERNAME: # Registry username
DOCKER_PASSWORD: # Registry password
```

## Observabilité

### Métriques (Prometheus)

Endpoints exposés :
- `/metrics` - Métriques Prometheus
- `/health` - Health checks

Métriques collectées :
- HTTP requests (status, duration, endpoint)
- Business operations (domain, operation, status)
- Events (published/consumed)
- Adapters calls (success/failure)
- Resources (CPU, memory)

### Logs (ELK Stack)

Configuration Fluent Bit :
- **Application logs** → Elasticsearch `app-*`
- **Audit logs** → Elasticsearch `audit-*`
- **Correlation IDs** pour traçabilité

### Tracing (Jaeger/OpenTelemetry)

Spans collectés :
- HTTP requests
- GraphQL resolvers
- Business operations
- Adapter calls
- Event publishing/consuming

## Sécurité

### Network Policies

Politiques appliquées :
- **API Gateway** : Ingress seulement depuis ingress-nginx
- **GraphQL Gateway** : Communication uniquement avec core API
- **Event Bus** : Accès restreint aux services autorisés

### RBAC

ServiceAccounts avec permissions minimales :
- **beryl-api-sa** : Accès pods, services, configmaps
- **beryl-graphql-sa** : Accès limité
- **beryl-eventbus-sa** : Accès messaging

### TLS/SSL

Certificats Let's Encrypt automatiques :
- **api.beryl-ecosystem.com**
- **graphql.beryl-ecosystem.com**
- **monitoring.beryl-ecosystem.com**

## Scalabilité

### Horizontal Pod Autoscaler (HPA)

Configuration par service :
- **beryl-core-api** : 3-20 replicas (CPU 70%, Memory 80%)
- **graphql-gateway** : 2-10 replicas
- **event-bus** : 3-5 replicas (messages/sec)

### Pod Disruption Budget (PDB)

Garantie haute disponibilité :
- **beryl-core-api** : Min 2 pods disponibles
- **graphql-gateway** : Min 1 pod disponible
- **event-bus** : Min 2 pods disponibles

## Monitoring & Alerting

### Dashboards Grafana

Métriques disponibles :
- **Performance** : Latence, throughput, erreurs
- **Business** : Transactions, rides, ESG scores
- **Infrastructure** : CPU, mémoire, réseau

### Alertes Prometheus

Règles d'alerte configurées :
- **Pods crash** : restart > 5/min
- **High latency** : p95 > 2s
- **Error rate** : > 5%
- **Resource usage** : CPU/Memory > 90%

## Troubleshooting

### Commandes Utiles

```bash
# Debug pods
kubectl describe pod <pod-name> -n default
kubectl logs -f <pod-name> -n default

# Port forwarding pour debug
kubectl port-forward deployment/beryl-core-api 8000:8000 -n default

# Exec dans un pod
kubectl exec -it deployment/beryl-core-api -n default -- /bin/bash

# Check endpoints
kubectl get endpoints -n default
kubectl describe ingress beryl-ingress -n default
```

### Logs Centralisés

```bash
# Application logs
kubectl logs -l app=beryl-core-api -n default --tail=100

# Audit logs
kubectl exec deployment/beryl-core-api -n default -- tail -f /var/log/beryl/audit.log

# ELK search
curl -X GET "elasticsearch:9200/app-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "level": "ERROR"
    }
  }
}'
```

### Rollback

```bash
# Rollback automatique
kubectl rollout undo deployment/beryl-core-api -n default

# Rollback manuel
kubectl set image deployment/beryl-core-api beryl-core-api=beryl/core-api:v1.0.0 -n default
```

## Performance & Optimisation

### Resource Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Optimisations

- **Multi-stage Docker build** : Image optimisée
- **Connection pooling** : PostgreSQL, Redis
- **Caching** : Redis pour sessions, cache applicatif
- **Async/Await** : Non-blocking I/O partout

## Backup & Recovery

### Base de Données

```bash
# Backup PostgreSQL
kubectl exec -it deployment/postgres -n default -- pg_dump beryl_db > backup.sql

# Restore
kubectl exec -it deployment/postgres -n default -- psql beryl_db < backup.sql
```

### Logs d'Audit

Logs immuables stockés sur PV persistant avec rotation automatique.

## Conformité

### RGPD
- **Audit trails** complets pour données personnelles
- **Data retention** configurable
- **Right to erasure** implémenté

### Sécurité
- **Secrets rotation** automatique
- **Network policies** strictes
- **RBAC** minimal
- **TLS 1.3** obligatoire

## Support & Maintenance

### Mises à Jour

```bash
# Update image
kubectl set image deployment/beryl-core-api beryl-core-api=beryl/core-api:v1.1.0

# Rolling update
kubectl rollout status deployment/beryl-core-api -n default
```

### Monitoring Continu

- **Uptime monitoring** : Pingdom/New Relic
- **Performance monitoring** : DataDog/AppDynamics
- **Log aggregation** : ELK / Loki
- **Alerting** : PagerDuty/OpsGenie

---

## 🚀 Checklist Déploiement Production

- [ ] Cluster Kubernetes configuré
- [ ] NGINX Ingress installé
- [ ] cert-manager déployé
- [ ] Secrets créés et sécurisés
- [ ] Monitoring stack opérationnel
- [ ] CI/CD pipelines configurés
- [ ] Tests d'intégration passés
- [ ] Sécurité auditée
- [ ] Documentation à jour
- [ ] Equipe formée

**Status: 🟢 PRODUCTION READY**

Infrastructure complète déployable avec `./deploy.sh` ! 🎯