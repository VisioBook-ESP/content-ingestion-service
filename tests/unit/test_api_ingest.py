"""Unit tests for ingestion API endpoints."""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v1.routers.ingest import router as ingest_router


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(ingest_router, prefix="/ingest")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestIngestionEndpoint:
    """Tests for POST /ingest endpoint."""

    def test_ingest_creates_job(self, client):
        """Test that POST /ingest creates a job and returns job ID."""
        with (
            patch("src.api.v1.routers.ingest.job_service") as mock_job_service,
            patch("src.api.v1.routers.ingest.get_ingestion_worker"),
        ):

            mock_job_service.create_job.return_value = "test-job-123"

            response = client.post(
                "/ingest/",
                json={
                    "fileId": "file-abc",
                    "projectId": "project-xyz",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["jobId"] == "test-job-123"
            assert data["status"] == "queued"

    def test_ingest_with_options(self, client):
        """Test ingestion with custom options."""
        with (
            patch("src.api.v1.routers.ingest.job_service") as mock_job_service,
            patch("src.api.v1.routers.ingest.get_ingestion_worker"),
        ):

            mock_job_service.create_job.return_value = "test-job-456"

            response = client.post(
                "/ingest/",
                json={
                    "fileId": "file-abc",
                    "projectId": "project-xyz",
                    "options": {
                        "cleanText": False,
                        "extractMetadata": True,
                        "chunkSize": 500,
                        "overlap": 50,
                    },
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["jobId"] == "test-job-456"

    def test_ingest_validates_required_fields(self, client):
        """Test that required fields are validated."""
        response = client.post("/ingest/", json={})

        assert response.status_code == 422


class TestStatusEndpoint:
    """Tests for GET /ingest/status/{job_id} endpoint."""

    def test_get_status_existing_job(self, client):
        """Test getting status of existing job."""
        with patch("src.api.v1.routers.ingest.job_service") as mock_job_service:
            mock_job_service.get_status.return_value = {"status": "processing"}

            response = client.get("/ingest/status/job-123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing"

    def test_get_status_completed_job(self, client):
        """Test getting status of completed job."""
        with patch("src.api.v1.routers.ingest.job_service") as mock_job_service:
            mock_job_service.get_status.return_value = {"status": "completed"}

            response = client.get("/ingest/status/job-456")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"

    def test_get_status_unknown_job(self, client):
        """Test getting status of unknown job returns 404."""
        with patch("src.api.v1.routers.ingest.job_service") as mock_job_service:
            mock_job_service.get_status.return_value = {"status": "unknown"}

            response = client.get("/ingest/status/nonexistent-job")

            assert response.status_code == 404


class TestCancelEndpoint:
    """Tests for POST /ingest/cancel/{job_id} endpoint."""

    def test_cancel_queued_job(self, client):
        """Test cancelling a queued job."""
        with patch("src.api.v1.routers.ingest.job_service") as mock_job_service:
            mock_job_service.get_status.return_value = {"status": "queued"}

            response = client.post("/ingest/cancel/job-123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"
            assert data["jobId"] == "job-123"
            mock_job_service.set_status.assert_called_once_with("job-123", "cancelled")

    def test_cancel_processing_job(self, client):
        """Test cancelling a processing job."""
        with patch("src.api.v1.routers.ingest.job_service") as mock_job_service:
            mock_job_service.get_status.return_value = {"status": "processing"}

            response = client.post("/ingest/cancel/job-456")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"

    def test_cancel_completed_job(self, client):
        """Test cancelling an already completed job."""
        with patch("src.api.v1.routers.ingest.job_service") as mock_job_service:
            mock_job_service.get_status.return_value = {"status": "completed"}

            response = client.post("/ingest/cancel/job-789")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert "already completed" in data["message"]

    def test_cancel_unknown_job(self, client):
        """Test cancelling an unknown job returns 404."""
        with patch("src.api.v1.routers.ingest.job_service") as mock_job_service:
            mock_job_service.get_status.return_value = {"status": "unknown"}

            response = client.post("/ingest/cancel/nonexistent")

            assert response.status_code == 404
