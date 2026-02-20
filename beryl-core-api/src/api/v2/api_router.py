"""API router for version 2 endpoints."""

from fastapi import APIRouter

from src.orchestration.esg.greenos.api.router import router as greenos_router


api_v2_router = APIRouter()

api_v2_router.include_router(
    greenos_router,
    prefix="/esg",
    tags=["ESG GreenOS"],
)
