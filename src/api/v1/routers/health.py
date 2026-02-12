"""Health check endpoints."""

from fastapi import APIRouter, status
from sqlalchemy import text

from src.database.connection import get_session

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "content-ingestion-service",
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check including database connectivity."""
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "not ready",
            "database": "disconnected",
            "error": str(e),
        }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """Liveness check."""
    return {"status": "alive"}
