# Beryl Core API

This is the central API Gateway and orchestration layer for the Béryl ecosystem.

## Overview

The `beryl-core-api` serves as the single entry point for all frontends and partners, centralizing authentication, authorization, logging, rate limiting, and orchestrating business workflows across all services.

## Architecture

- **Clean Architecture**: Strict separation of concerns with routing, orchestration, adapters, and domain layers.
- **Microservices Orchestration**: Acts as the orchestration layer for various branches: Fintech, Electric Mobility, ESG & Pedometer, and Social Network.
- **Scalable and Modular**: Designed to be future-proof with clear module boundaries.
- **Zero-Trust Security**: Implements comprehensive authentication and authorization with JWT and RBAC.
- **Observability**: Full OpenTelemetry instrumentation for traces, metrics, and logs with Jaeger and Prometheus.

## Strategic Mapping

- `beryl_mamba_core` → Fintech branch (payments, wallets, transactions, risk, compliance)
- `beryl-ai-engine` → Electric mobility branch (demand prediction, routing, fleet intelligence)
- `berylcommunity-wb` → ESG & pedometer branch (health data, ESG metrics, sustainability scoring)
- `berylcommunity-ai-engine` → Social network branch (recommendations, moderation, social intelligence)

## Getting Started

### Local Development

1. Clone the repository.
2. Install dependencies: `poetry install` (recommended) or `pip install -r requirements.txt`.
3. Set up environment variables using `.env.example`.
4. Run the application: `uvicorn src.main:app --reload`.
5. For Docker: `docker-compose up`.

### Testing

Run tests with: `pytest`

For Zero-Trust enforcement tests: `pytest tests/integration/test_zero_trust_enforcement.py`

### API Documentation

Once running, visit `/docs` for interactive API documentation.

## Deployment

### CI/CD

Automated pipelines via GitHub Actions:

- **Testing**: Runs on every push/PR with pytest, linting, and security scans.
- **Build & Deploy**: On main branch merge, builds Docker image and deploys to staging/production.

### Docker

Multi-stage build for optimized images:

```bash
docker build -t beryl-core-api .
docker run -p 8000:8000 beryl-core-api
```

### Kubernetes

Production deployment with:

- Horizontal Pod Autoscaling (HPA)
- Network Policies for zero-trust networking
- RBAC and security contexts
- Ingress with TLS
- Monitoring with Prometheus and Jaeger

Deploy to staging: `./deploy_staging.sh`

### Monitoring & Observability

- **Metrics**: Prometheus scraping on `/metrics`
- **Tracing**: Jaeger for distributed tracing
- **Logs**: Structured logging with OpenTelemetry
- **Dashboards**: Grafana for visualization (see `docs/grafana_dashboard.json`)

## Security

- **Zero-Trust**: All requests require valid JWT with appropriate scopes.
- **RBAC**: Role-based access control for multi-domain operations.
- **Network Policies**: Kubernetes network isolation.
- **Secrets Management**: Encrypted secrets in K8s.

## Project Structure

See the repository structure for detailed organization.

## Contributing

1. Follow the clean architecture principles.
2. Add tests for new features.
3. Update documentation.
4. Ensure security compliance.

## License

TODO: Add license information.
