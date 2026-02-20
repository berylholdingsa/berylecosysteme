# Beryl Core API - Observability Layer

## Vue d'ensemble

La couche d'observabilité de Beryl Core API fournit une solution complète de monitoring, logging, tracing et audit pour garantir la visibilité, la résilience et la conformité du système distribué.

## Composants

### 1. Logging Structuré (`logging/`)
- **logger.py**: Logger JSON principal avec correlation tracking
- **formatters.py**: Formatters spécialisés (audit, metrics, performance)
- **correlation.py**: Gestion des IDs de corrélation et contexte

### 2. Métriques Prometheus (`metrics/`)
- **prometheus.py**: Métriques principales (HTTP, business, events, adapters)
- **counters.py**: Compteurs métier spécialisés
- **histograms.py**: Histogrammes de performance

### 3. Tracing Distribué (`tracing/`)
- **opentelemetry.py**: Intégration OpenTelemetry (Jaeger, Zipkin)
- **tracer.py**: Interface de tracing avec context managers

### 4. Audit & Conformité (`audit/`)
- **audit_logger.py**: Logger d'audit immutable avec hash d'intégrité
- **audit_events.py**: Types d'événements d'audit prédéfinis

### 5. Bootstrap (`observability_bootstrap.py`)
Initialisation centralisée de tous les composants d'observabilité.

## Configuration

```bash
# Logging
LOG_LEVEL=INFO

# Metrics
METRICS_ENABLED=true

# Tracing
TRACING_ENABLED=true
JAEGER_HOST=localhost
JAEGER_PORT=14268
ZIPKIN_ENDPOINT=http://localhost:9411/api/v2/spans

# Audit
AUDIT_ENABLED=true
AUDIT_LOG_FILE=/var/log/beryl/audit.log

# Event Bus
EVENT_BUS=mock  # mock, kafka, rabbitmq
```

## Utilisation

### Logging

```python
from src.observability import logger

logger.info("Operation completed",
           user_id="user123",
           correlation_id=get_correlation_id(),
           extra_data={"result": "success"})
```

### Métriques

```python
from src.observability import metrics, counters, histograms

# Métriques HTTP
metrics.record_http_request("GET", "/api/v1/users", 200, 0.1, "fintech")

# Compteurs métier
counters.increment_fintech_operation("payment", currency="EUR")

# Histogrammes performance
histograms.observe_fintech_operation("transaction", 0.05)
```

### Tracing

```python
from src.observability import tracer

with tracer.trace_business_operation("fintech", "process_payment") as span:
    # Votre logique métier
    tracer.add_attributes_to_current_span({"amount": 100.0})
```

### Audit

```python
from src.observability import audit_logger

audit_logger.log_payment_accessed(
    user_id="user123",
    payment_id="pay_456",
    action="VIEW",
    ip_address="192.168.1.1"
)
```

## Endpoints

- **GET /health**: Status de santé avec état de l'observabilité
- **GET /metrics**: Métriques Prometheus (format texte)

## Intégration FastAPI

Le middleware `ObservabilityMiddleware` est automatiquement ajouté et fournit :

- Injection automatique des correlation IDs
- Logging structuré des requêtes HTTP
- Métriques de performance
- Tracing distribué
- Audit des opérations sensibles

## Conformité

### RGPD & Données Sensibles
- Audit automatique des accès aux données de santé
- Hash d'intégrité pour les événements critiques
- Retention configurable (7 ans pour données financières)

### Périmètre d'Audit
- Accès aux paiements et portefeuilles
- Modifications de données de santé
- Calculs de scores ESG
- Export de données utilisateur

## Monitoring

### ELK Stack (Recommandé)
- Logs structurés JSON → Elasticsearch
- Visualisations Kibana
- Alerting sur patterns

### Prometheus + Grafana
- Métriques temps réel
- Dashboards métier
- Alerting SLA/SLO

### Jaeger/Tempo
- Traces distribuées
- Analyse de performance
- Debug de bottlenecks

## Architecture

```
HTTP Request
    ↓
ObservabilityMiddleware
    ↓
├── Logging (JSON + correlation)
├── Metrics (Prometheus)
├── Tracing (OpenTelemetry)
└── Audit (immutable logs)
    ↓
Business Logic
```

## Sécurité

- **Aucun impact** sur la logique métier
- **Middleware non-bloquant** (pas de crash si backend indisponible)
- **Audit immutable** avec hash d'intégrité
- **Contexte isolé** par requête

## Performance

- **Overhead minimal** (< 1ms par requête)
- **Async partout** pour non-blocking I/O
- **Buffering intelligent** pour les métriques
- **Lazy initialization** des composants optionnels

## Demo

```python
from src.observability.demo import run_observability_demo

# Lance une démonstration complète
run_observability_demo()
```

## Checklist Déploiement

- [ ] Variables d'environnement configurées
- [ ] Répertoires de logs créés (`/var/log/beryl/`)
- [ ] Jaeger/Zipkin accessibles
- [ ] Prometheus scraping configuré
- [ ] ELK stack opérationnel
- [ ] Tests d'observabilité exécutés