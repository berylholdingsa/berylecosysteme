"""
API router for version 1 of the Beryl Core API.

This module aggregates all route modules for the v1 API.
"""

from fastapi import APIRouter, Depends

from app.payment_terminal.router import router as payment_terminal_router
from src.config.dependencies import get_current_user
from .routes.auth_routes import router as auth_router
from .routes.fintech_routes import router as fintech_router
from .routes.mobility_routes import router as mobility_router
from .routes.esg_routes import router as esg_router
from .routes.social_routes import router as social_router
from .routes.aoq_routes import router as aoq_router
from .routes.security_routes import router as security_router

api_router = APIRouter()

# Include route modules
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(
    fintech_router,
    prefix="/fintech",
    tags=["Fintech"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mobility_router,
    prefix="/mobility",
    tags=["Mobility"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    esg_router,
    prefix="/esg",
    tags=["ESG"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    social_router,
    prefix="/social",
    tags=["Social"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    aoq_router,
    prefix="/aoq",
    tags=["AOQ"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    security_router,
    prefix="/security",
    tags=["Security"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    payment_terminal_router,
    tags=["Payments"],
    dependencies=[Depends(get_current_user)],
)

# TODO: Add more route inclusions as needed
