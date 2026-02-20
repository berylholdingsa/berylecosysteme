# Regulatory Architecture

## Core Components
- API Gateway (`src/main.py` + middleware chain)
- Fintech Transaction Core (`/api/v1/fintech/transactions`)
- Compliance Engine (`src/compliance`)
- Immutable Audit Chain (`src/core/audit`)
- Event Bus (`src/events/bus/kafka_bus.py`)
- Outbox Relay (`src/events/outbox_relay.py`)
- Observability Stack (Prometheus + OTEL + Jaeger)

## Security Boundaries
- Authentication and scope authorization middleware.
- Correlation ID mandatory for protected endpoints.
- Replay protection (`X-Nonce`, `X-Timestamp`).
- Rate limiting with Redis.
- TLS enforcement and restrictive CORS.
- Signed financial event enforcement.
