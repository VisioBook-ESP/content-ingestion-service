"""Unit tests for workers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.workers.job_service import JobService, job_service
from src.schemas.ingest import IngestionOptions


class TestJobService:
    """Tests for JobService."""

    def test_create_job_returns_uuid(self):
        """Test that create_job returns a valid UUID."""
        service = JobService()
        job_id = service.create_job()

        assert isinstance(job_id, str)
        assert len(job_id) == 36  # UUID format

    def test_create_job_initializes_status(self):
        """Test that new job has queued status."""
        service = JobService()
        job_id = service.create_job()

        status = service.get_status(job_id)
        assert status["status"] == "queued"

    def test_set_status_updates_job(self):
        """Test that set_status updates job status."""
        service = JobService()
        job_id = service.create_job()

        service.set_status(job_id, "processing")
        status = service.get_status(job_id)

        assert status["status"] == "processing"

    def test_set_status_to_completed(self):
        """Test setting status to completed."""
        service = JobService()
        job_id = service.create_job()

        service.set_status(job_id, "completed")
        status = service.get_status(job_id)

        assert status["status"] == "completed"

    def test_set_status_to_failed(self):
        """Test setting status to failed."""
        service = JobService()
        job_id = service.create_job()

        service.set_status(job_id, "failed")
        status = service.get_status(job_id)

        assert status["status"] == "failed"

    def test_get_status_unknown_job(self):
        """Test getting status of unknown job."""
        service = JobService()

        status = service.get_status("nonexistent-job-id")

        assert status["status"] == "unknown"

    def test_multiple_jobs_independent(self):
        """Test that multiple jobs have independent statuses."""
        service = JobService()

        job1 = service.create_job()
        job2 = service.create_job()

        service.set_status(job1, "completed")
        service.set_status(job2, "failed")

        assert service.get_status(job1)["status"] == "completed"
        assert service.get_status(job2)["status"] == "failed"


class TestIngestionWorker:
    """Tests for IngestionWorker."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for worker."""
        with patch("src.workers.ingestion_worker.StorageClient") as mock_storage, \
             patch("src.workers.ingestion_worker.ChunkingService") as mock_chunk, \
             patch("src.workers.ingestion_worker.MetadataExtractor") as mock_meta, \
             patch("src.workers.ingestion_worker.DatabaseClient") as mock_db, \
             patch("src.workers.ingestion_worker.ProcessorFactory") as mock_factory, \
             patch("src.workers.ingestion_worker.TextCleaningService") as mock_clean, \
             patch("src.workers.ingestion_worker.job_service") as mock_job:

            yield {
                "storage": mock_storage,
                "chunk": mock_chunk,
                "meta": mock_meta,
                "db": mock_db,
                "factory": mock_factory,
                "clean": mock_clean,
                "job": mock_job,
            }

    @pytest.mark.asyncio
    async def test_worker_sets_processing_status(self, mock_services):
        """Test that worker sets processing status at start."""
        from src.workers.ingestion_worker import IngestionWorker

        mock_job = mock_services["job"]
        mock_service = MagicMock()
        mock_service.ingest = AsyncMock(return_value={"status": "completed", "totalChunks": 5})

        worker = IngestionWorker()
        worker.service = mock_service

        options = IngestionOptions()
        await worker.run("job-123", "file-456", "project-789", options)

        mock_job.set_status.assert_any_call("job-123", "processing")

    @pytest.mark.asyncio
    async def test_worker_sets_completed_on_success(self, mock_services):
        """Test that worker sets completed status on success."""
        from src.workers.ingestion_worker import IngestionWorker

        mock_job = mock_services["job"]
        mock_service = MagicMock()
        mock_service.ingest = AsyncMock(return_value={"status": "completed", "totalChunks": 5})

        worker = IngestionWorker()
        worker.service = mock_service

        options = IngestionOptions()
        await worker.run("job-123", "file-456", "project-789", options)

        mock_job.set_status.assert_any_call("job-123", "completed")

    @pytest.mark.asyncio
    async def test_worker_sets_failed_on_error(self, mock_services):
        """Test that worker sets failed status on error."""
        from src.workers.ingestion_worker import IngestionWorker

        mock_job = mock_services["job"]
        mock_service = MagicMock()
        mock_service.ingest = AsyncMock(side_effect=Exception("Test error"))

        worker = IngestionWorker()
        worker.service = mock_service

        options = IngestionOptions()
        await worker.run("job-123", "file-456", "project-789", options)

        mock_job.set_status.assert_any_call("job-123", "failed")
