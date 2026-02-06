from fastapi import APIRouter

from src.api.v1.routers import extract, health, ingest, preprocess, validate

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(preprocess.router, prefix="/preprocess", tags=["preprocess"])
api_router.include_router(extract.router, prefix="/extract", tags=["extract"])
api_router.include_router(validate.router, prefix="/validate", tags=["validate"])
