"""Unit tests for health check endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v1.routers.health import router as health_router


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(health_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_200(self, client):
        """Test that health endpoint returns 200."""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        """Test that health endpoint returns healthy status."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "content-ingestion-service"


class TestLivenessEndpoint:
    """Tests for GET /health/live endpoint."""

    def test_liveness_returns_200(self, client):
        """Test that liveness endpoint returns 200."""
        response = client.get("/health/live")

        assert response.status_code == 200

    def test_liveness_returns_alive_status(self, client):
        """Test that liveness endpoint returns alive status."""
        response = client.get("/health/live")
        data = response.json()

        assert data["status"] == "alive"


class TestReadinessEndpoint:
    """Tests for GET /health/ready endpoint."""

    def test_readiness_with_database_connected(self, client):
        """Test readiness when database is connected."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock()

        with patch("src.api.v1.routers.health.get_session") as mock_get_session:
            mock_get_session.return_value = mock_session

            response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"

    def test_readiness_with_database_disconnected(self, client):
        """Test readiness when database is disconnected."""
        with patch("src.api.v1.routers.health.get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Connection refused")

            response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not ready"
        assert data["database"] == "disconnected"
