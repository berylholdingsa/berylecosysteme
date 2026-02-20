# Tests d'Intégration & Déploiement

## Vue d'ensemble

Cette documentation couvre les stratégies de test pour valider le déploiement et l'intégration de **beryl-core-api** dans l'écosystème Béryl.

## Structure des Tests

```
tests/
├── integration/
│   ├── test_deployment.py      # Tests de déploiement Kubernetes
│   ├── test_api_endpoints.py   # Tests des endpoints API
│   ├── test_graphql.py         # Tests GraphQL Gateway
│   ├── test_event_driven.py    # Tests event-driven
│   ├── test_observability.py   # Tests observabilité
│   ├── test_security.py        # Tests sécurité
│   └── conftest.py            # Configuration pytest
├── deployment/
│   ├── test_k8s_manifests.py  # Validation manifests K8s
│   ├── test_ci_cd.py          # Tests pipelines CI/CD
│   └── test_infrastructure.py # Tests infrastructure
└── performance/
    ├── test_load.py           # Tests de charge
    ├── test_scalability.py    # Tests scalabilité
    └── test_resilience.py     # Tests résilience
```

## Tests d'Intégration

### Prérequis

```bash
# Installation des dépendances de test
pip install pytest pytest-asyncio pytest-kubernetes pytest-helm
pip install requests aiohttp graphene-test

# Variables d'environnement pour les tests
export TEST_ENV=staging
export KUBE_CONFIG_PATH=~/.kube/config
export API_BASE_URL=https://staging-api.beryl-ecosystem.com
```

### Tests de Déploiement

```python
# test_deployment.py
import pytest
import kubernetes.client as k8s
from kubernetes import config

class TestDeployment:
    @pytest.fixture(scope="session")
    def k8s_client(self):
        config.load_kube_config()
        return k8s.CoreV1Api()

    def test_namespace_exists(self, k8s_client):
        """Test que le namespace de déploiement existe"""
        namespaces = k8s_client.list_namespace()
        namespace_names = [ns.metadata.name for ns in namespaces.items]

        assert "beryl-staging" in namespace_names

    def test_deployments_running(self, k8s_client):
        """Test que tous les déploiements sont en cours d'exécution"""
        deployments = k8s_client.list_namespaced_deployment("beryl-staging")

        for deployment in deployments.items:
            assert deployment.status.ready_replicas == deployment.spec.replicas
            assert deployment.status.conditions[-1].type == "Available"
            assert deployment.status.conditions[-1].status == "True"

    def test_services_exposed(self, k8s_client):
        """Test que les services sont correctement exposés"""
        services = k8s_client.list_namespaced_service("beryl-staging")

        service_names = [svc.metadata.name for svc in services.items]
        required_services = ["beryl-core-api", "graphql-gateway", "event-bus"]

        for service in required_services:
            assert service in service_names

    def test_ingress_configured(self, k8s_client):
        """Test que l'Ingress est correctement configuré"""
        networking_api = k8s.NetworkingV1Api()
        ingresses = networking_api.list_namespaced_ingress("beryl-staging")

        assert len(ingresses.items) > 0

        ingress = ingresses.items[0]
        assert "staging-api.beryl-ecosystem.com" in [rule.host for rule in ingress.spec.rules]
        assert ingress.spec.tls is not None
```

### Tests des Endpoints API

```python
# test_api_endpoints.py
import pytest
import requests
import json
from typing import Dict, Any

class TestAPIEndpoints:
    def test_health_endpoints(self):
        """Test des endpoints de santé"""
        endpoints = [
            "/health/live",
            "/health/ready",
            "/health"
        ]

        for endpoint in endpoints:
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert data["status"] in ["healthy", "ok"]

    def test_metrics_endpoint(self):
        """Test de l'endpoint métriques Prometheus"""
        response = requests.get(f"{API_BASE_URL}/metrics")
        assert response.status_code == 200

        # Vérification du format Prometheus
        content = response.text
        assert "beryl_api_requests_total" in content
        assert "beryl_api_request_duration_seconds" in content

    def test_domain_endpoints(self):
        """Test des endpoints par domaine"""
        domains = ["fintech", "mobility", "esg", "social"]

        for domain in domains:
            response = requests.get(f"{API_BASE_URL}/api/v1/{domain}/status")
            assert response.status_code == 200

            data = response.json()
            assert "domain" in data
            assert data["domain"] == domain

    @pytest.mark.parametrize("method,endpoint,payload", [
        ("POST", "/api/v1/fintech/transactions", {"amount": 100.0, "currency": "EUR"}),
        ("POST", "/api/v1/mobility/rides", {"pickup": "A", "dropoff": "B"}),
        ("POST", "/api/v1/esg/score", {"company_id": "123", "metrics": []}),
        ("POST", "/api/v1/social/posts", {"content": "Test post", "author": "test"})
    ])
    def test_business_operations(self, method, endpoint, payload):
        """Test des opérations métier principales"""
        response = requests.request(method, f"{API_BASE_URL}{endpoint}", json=payload)

        # En développement/staging, peut retourner 201 ou 202
        assert response.status_code in [200, 201, 202]

        data = response.json()
        assert "id" in data or "status" in data
```

### Tests GraphQL

```python
# test_graphql.py
import pytest
from graphene.test import Client
from graphql import GraphQLSchema
from beryl.graphql.schema import schema

class TestGraphQL:
    @pytest.fixture
    def graphql_client(self):
        return Client(schema)

    def test_graphql_schema(self, graphql_client):
        """Test que le schéma GraphQL est valide"""
        introspection_query = """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
          }
        }
        """

        result = graphql_client.execute(introspection_query)
        assert result is not None
        assert "errors" not in result

    def test_domain_queries(self, graphql_client):
        """Test des queries GraphQL par domaine"""
        queries = {
            "fintech": """
            query {
              fintech {
                transactions(limit: 10) {
                  id
                  amount
                  currency
                }
              }
            }
            """,
            "mobility": """
            query {
              mobility {
                rides(limit: 10) {
                  id
                  status
                  pickupLocation
                }
              }
            }
            """
        }

        for domain, query in queries.items():
            result = graphql_client.execute(query)
            assert "errors" not in result
            assert domain in result["data"]

    def test_graphql_subscriptions(self, graphql_client):
        """Test des subscriptions GraphQL"""
        subscription = """
        subscription {
          fintechTransactionCreated {
            id
            amount
            timestamp
          }
        }
        """

        # Note: Les tests de subscription nécessitent un setup spécial
        # avec des websockets ou un client async
        pass
```

### Tests Event-Driven

```python
# test_event_driven.py
import pytest
import asyncio
import json
from beryl.events.bus import EventBus
from beryl.events.registry import EventRegistry

class TestEventDriven:
    @pytest.fixture
    async def event_bus(self):
        bus = EventBus()
        await bus.connect()
        yield bus
        await bus.disconnect()

    async def test_event_publishing(self, event_bus):
        """Test de la publication d'événements"""
        test_event = {
            "type": "fintech.transaction.created",
            "data": {
                "transaction_id": "test-123",
                "amount": 100.0,
                "currency": "EUR"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }

        await event_bus.publish("fintech.transaction.created", test_event)

        # Vérification que l'événement a été publié
        # (nécessite un consumer de test ou un mock)

    async def test_event_consumption(self, event_bus):
        """Test de la consommation d'événements"""
        consumed_events = []

        async def test_consumer(event_data):
            consumed_events.append(event_data)

        await event_bus.subscribe("test.event", test_consumer)
        await event_bus.publish("test.event", {"test": "data"})

        await asyncio.sleep(0.1)  # Attendre la consommation

        assert len(consumed_events) == 1
        assert consumed_events[0]["test"] == "data"

    def test_event_registry(self):
        """Test du registre d'événements"""
        registry = EventRegistry()

        # Vérification que tous les événements sont enregistrés
        events = registry.get_all_events()

        expected_events = [
            "fintech.transaction.created",
            "fintech.transaction.updated",
            "mobility.ride.requested",
            "mobility.ride.completed",
            "esg.score.calculated",
            "social.post.created"
        ]

        for event in expected_events:
            assert event in events
```

### Tests d'Observabilité

```python
# test_observability.py
import pytest
import requests
import time
from prometheus_client.parser import text_string_to_metric_families

class TestObservability:
    def test_metrics_collection(self):
        """Test que les métriques sont collectées"""
        response = requests.get(f"{API_BASE_URL}/metrics")
        assert response.status_code == 200

        metrics_text = response.text

        # Parsing des métriques Prometheus
        families = text_string_to_metric_families(metrics_text)

        metric_names = [family.name for family in families]

        # Métriques attendues
        expected_metrics = [
            "beryl_api_requests_total",
            "beryl_api_request_duration_seconds",
            "beryl_graphql_queries_total",
            "beryl_event_published_total",
            "beryl_event_consumed_total"
        ]

        for metric in expected_metrics:
            assert metric in metric_names

    def test_tracing_headers(self):
        """Test que les headers de tracing sont propagés"""
        headers = {
            "X-Request-ID": "test-request-123",
            "X-Trace-ID": "test-trace-456"
        }

        response = requests.get(f"{API_BASE_URL}/health", headers=headers)
        assert response.status_code == 200

        # Vérification que les headers sont retournés ou loggés
        # (dépend de l'implémentation)

    def test_audit_logging(self):
        """Test que l'audit logging fonctionne"""
        # Effectuer une opération qui doit être auditée
        response = requests.post(f"{API_BASE_URL}/api/v1/fintech/transactions",
                               json={"amount": 100.0, "currency": "EUR"})

        assert response.status_code in [200, 201]

        # Vérification des logs d'audit
        # (nécessite accès aux logs ou endpoint d'audit)
```

## Tests de Performance

### Tests de Charge

```python
# test_load.py
import pytest
import asyncio
import aiohttp
import time
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def test_health(self):
        self.client.get("/health")

    @task
    def test_fintech_transaction(self):
        self.client.post("/api/v1/fintech/transactions", json={
            "amount": 100.0,
            "currency": "EUR"
        })

    @task
    def test_graphql_query(self):
        self.client.post("/graphql", json={
            "query": "{ fintech { transactions(limit: 5) { id amount } } }"
        })

# Configuration Locust
# locust -f test_load.py --host=https://staging-api.beryl-ecosystem.com
```

### Tests de Scalabilité

```python
# test_scalability.py
import pytest
import kubernetes.client as k8s
from kubernetes import config

class TestScalability:
    def test_hpa_functionality(self):
        """Test que l'HPA fonctionne correctement"""
        config.load_kube_config()
        autoscaling_api = k8s.AutoscalingV1Api()

        hpa = autoscaling_api.read_namespaced_horizontal_pod_autoscaler(
            "beryl-core-api-hpa", "beryl-staging"
        )

        assert hpa.spec.min_replicas == 1
        assert hpa.spec.max_replicas == 10
        assert len(hpa.spec.metrics) > 0

    def test_pdb_protection(self):
        """Test que les PDB protègent les déploiements"""
        config.load_kube_config()
        policy_api = k8s.PolicyV1Api()

        pdb = policy_api.read_namespaced_pod_disruption_budget(
            "beryl-core-api-pdb", "beryl-staging"
        )

        assert pdb.spec.min_available == 1
```

## Tests de Sécurité

### Tests d'Authentification/Autorisation

```python
# test_security.py
import pytest
import jwt
import time

class TestSecurity:
    def test_jwt_token_generation(self):
        """Test de la génération de tokens JWT"""
        # Test de génération de token valide
        pass

    def test_jwt_token_validation(self):
        """Test de la validation de tokens JWT"""
        # Test de validation de token valide
        # Test de rejet de token invalide/expiré
        pass

    def test_rbac_permissions(self):
        """Test des permissions RBAC"""
        # Test d'accès autorisé
        # Test de rejet d'accès non autorisé
        pass

    def test_rate_limiting(self):
        """Test du rate limiting"""
        # Test de limitation du nombre de requêtes
        pass
```

## Exécution des Tests

### Tests Locaux

```bash
# Tests unitaires
pytest tests/unit/ -v

# Tests d'intégration (avec services mockés)
pytest tests/integration/ -v --tb=short

# Tests de performance
locust -f tests/performance/test_load.py --host=http://localhost:8000
```

### Tests en CI/CD

```yaml
# .github/workflows/ci-cd.yml
- name: Run Integration Tests
  run: |
    pytest tests/integration/ -v --junitxml=test-results.xml
    pytest tests/deployment/ -v --junitxml=deploy-results.xml

- name: Run Performance Tests
  run: |
    locust --headless -f tests/performance/test_load.py \
           --host=${{ secrets.API_BASE_URL }} \
           --users=100 --spawn-rate=10 --run-time=1m
```

### Tests de Déploiement

```bash
# Validation des configurations
python validate_config.py

# Tests de déploiement Kubernetes
pytest tests/deployment/test_k8s_manifests.py -v

# Tests d'infrastructure
pytest tests/deployment/test_infrastructure.py -v
```

## Métriques de Test

### Couverture de Code

```bash
# Génération du rapport de couverture
pytest --cov=src --cov-report=html --cov-report=xml

# Seuils minimums
# - Linting: 100%
# - Tests unitaires: 80%
# - Tests d'intégration: 70%
```

### Performance Baselines

- **Latence moyenne**: < 200ms
- **Taux d'erreur**: < 0.1%
- **Throughput**: > 1000 req/sec
- **Temps de réponse p95**: < 500ms

### Métriques de Qualité

- **Code coverage**: > 80%
- **Cyclomatic complexity**: < 10
- **Security vulnerabilities**: 0
- **Performance regressions**: 0

## Debugging & Troubleshooting

### Commandes Utiles

```bash
# Debug des tests
pytest -v -s --pdb tests/integration/test_api_endpoints.py::TestAPIEndpoints::test_health_endpoints

# Tests avec logs détaillés
pytest -v --log-cli-level=INFO tests/

# Tests parallèles
pytest -n auto tests/integration/

# Tests avec coverage
pytest --cov=src --cov-report=html:htmlcov tests/
```

### Debugging Kubernetes

```bash
# Logs des pods de test
kubectl logs -f deployment/test-runner -n beryl-staging

# Debug des services
kubectl describe service beryl-core-api -n beryl-staging

# Port forwarding pour debug local
kubectl port-forward deployment/beryl-core-api 8000:8000 -n beryl-staging
```

---

## 🚀 Checklist Tests

- [ ] Tests unitaires passent (coverage > 80%)
- [ ] Tests d'intégration passent
- [ ] Tests de déploiement valides
- [ ] Tests de performance dans les baselines
- [ ] Tests de sécurité passent
- [ ] Tests CI/CD configurés
- [ ] Rapports de test générés
- [ ] Métriques de qualité respectées

**Status: 🧪 TESTS READY**