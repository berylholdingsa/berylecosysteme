"""
Main entry point for the Beryl Core API application.

This module initializes the FastAPI application, includes routers,
and sets up middleware for the central API Gateway.
"""

from typing import Any

from fastapi import Depends, FastAPI
from fastapi.security import HTTPBearer
from starlette.middleware.cors import CORSMiddleware

from src.api.v1.api_router import api_router
from src.api.v2.api_router import api_v2_router
from src.api.v1.endpoints.health import router as health_router
from src.api.v1.middlewares.aoq_fail_closed_middleware import AoqFailClosedMiddleware
from src.api.v1.middlewares.auth_middleware import AuthMiddleware
from src.api.v1.middlewares.error_handler_middleware import ErrorHandlerMiddleware
from src.api.v1.middlewares.observability_middleware import ObservabilityMiddleware
from src.config.settings import settings
from src.core.security.key_management import key_manager
from src.core.security.middleware import SecurityMiddleware
from src.orchestration.esg.greenos.api.router import get_greenos_service
from src.orchestration.esg.greenos.schemas.responses import GreenOSPublicKeyResponse
from src.orchestration.esg.greenos.services.greenos_service import GreenOSService

# Initialize observability
from src.observability.observability_bootstrap import init_observability
init_observability()
key_manager.validate_runtime_security()

app = FastAPI(
    title="Beryl Core API",
    description="Central API Gateway and orchestration layer for Béryl ecosystem",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_oauth2_redirect_url=None,
)

# Security scheme for Swagger
security_scheme = HTTPBearer()

# Restrictive CORS policy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Correlation-ID",
        "X-Nonce",
        "X-Timestamp",
        "X-PSP-Signature",
        "Idempotency-Key",
    ],
)

# Add middleware stack.
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(AoqFailClosedMiddleware)
app.add_middleware(ObservabilityMiddleware)

# Include API router
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_v2_router, prefix="/api/v2")
app.include_router(health_router)


@app.get("/.well-known/greenos-public-key", response_model=GreenOSPublicKeyResponse)
async def greenos_public_key_well_known(
    version: str | None = None,
    service: GreenOSService = Depends(get_greenos_service),
):
    return GreenOSPublicKeyResponse.model_validate(service.get_public_key(key_version=version))


@app.on_event("startup")
async def startup_greenos_outbox_worker() -> None:
    if not settings.enable_outbox_worker:
        return
    from src.orchestration.esg.greenos.outbox.greenos_outbox_worker import GreenOSOutboxWorker

    worker = GreenOSOutboxWorker()
    await worker.start()
    app.state.greenos_outbox_worker = worker


@app.on_event("shutdown")
async def shutdown_greenos_outbox_worker() -> None:
    worker: Any = getattr(app.state, "greenos_outbox_worker", None)
    if worker is None:
        return
    await worker.stop()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
