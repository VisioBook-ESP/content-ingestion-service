"""Integration tests for the complete ingestion pipeline."""

import pytest
import tempfile
import os
from pathlib import Path

from src.services.ingestion_service import IngestionService
from src.services.text_cleaning_service import TextCleaningService
from src.services.chunking_service import ChunkingService
from src.services.metadata_extractor import MetadataExtractor
from src.processors.processor_factory import ProcessorFactory
from src.processors.txt_processor import TextProcessor
from src.processors.html_processor import HTMLProcessor
from src.schemas.ingest import IngestionOptions
from tests.mocks import MockStorageClient, MockDatabaseClient


class TestIngestionPipelineIntegration:
    """Integration tests for the full ingestion pipeline with mocked external services."""

    @pytest.fixture
    def real_services(self):
        """Create real services (processors, cleaners, etc.) with mocked clients."""
        storage = MockStorageClient(
            content="Ceci est un document de test pour valider le pipeline d'ingestion. "
                    "Le document contient plusieurs phrases avec du contenu en français. "
                    "Il permet de tester l'extraction de texte, le nettoyage, "
                    "la détection de langue et le découpage en chunks."
        )
        db_client = MockDatabaseClient()

        processor_factory = ProcessorFactory([
            TextProcessor(),
            HTMLProcessor(),
        ])

        service = IngestionService(
            storage_client=storage,
            chunking_service=ChunkingService(),
            metadata_extractor=MetadataExtractor(),
            db_client=db_client,
            processor_factory=processor_factory,
            text_cleaning_service=TextCleaningService(),
        )

        return {
            "service": service,
            "storage": storage,
            "db_client": db_client,
        }

    @pytest.mark.asyncio
    async def test_full_pipeline_txt_ingestion(self, real_services):
        """Test complete ingestion of a TXT file."""
        service = real_services["service"]
        db_client = real_services["db_client"]

        options = IngestionOptions(
            cleanText=True,
            extractMetadata=True,
            chunkSize=20,
            overlap=5,
        )

        result = await service.ingest("file-001", "project-001", options)

        assert result["status"] == "completed"
        assert result["totalChunks"] > 0

        assert db_client.save_called
        assert len(db_client.saved_documents) == 1
        saved = db_client.saved_documents[0]
        assert saved["project_id"] == "project-001"
        assert saved["file_id"] == "file-001"
        assert len(saved["document"]["chunks"]) > 0

    @pytest.mark.asyncio
    async def test_pipeline_detects_french_language(self, real_services):
        """Test that pipeline correctly detects French language."""
        service = real_services["service"]
        db_client = real_services["db_client"]

        options = IngestionOptions(
            cleanText=True,
            extractMetadata=True,
            chunkSize=100,
            overlap=10,
        )

        await service.ingest("file-002", "project-001", options)

        saved = db_client.saved_documents[0]
        metadata = saved["document"]["metadata"]
        assert metadata.get("language") == "fr"

    @pytest.mark.asyncio
    async def test_pipeline_counts_words(self, real_services):
        """Test that pipeline correctly counts words."""
        service = real_services["service"]
        db_client = real_services["db_client"]

        options = IngestionOptions(
            cleanText=True,
            extractMetadata=True,
            chunkSize=100,
            overlap=10,
        )

        await service.ingest("file-003", "project-001", options)

        saved = db_client.saved_documents[0]
        metadata = saved["document"]["metadata"]
        assert metadata.get("wordCount", 0) > 0

    @pytest.mark.asyncio
    async def test_pipeline_without_cleaning(self, real_services):
        """Test pipeline with text cleaning disabled."""
        service = real_services["service"]
        db_client = real_services["db_client"]

        options = IngestionOptions(
            cleanText=False,
            extractMetadata=True,
            chunkSize=100,
            overlap=10,
        )

        result = await service.ingest("file-004", "project-001", options)

        assert result["status"] == "completed"
        assert db_client.save_called

    @pytest.mark.asyncio
    async def test_pipeline_without_metadata(self, real_services):
        """Test pipeline with metadata extraction disabled."""
        service = real_services["service"]
        db_client = real_services["db_client"]

        options = IngestionOptions(
            cleanText=True,
            extractMetadata=False,
            chunkSize=100,
            overlap=10,
        )

        result = await service.ingest("file-005", "project-001", options)

        assert result["status"] == "completed"
        saved = db_client.saved_documents[0]
        assert saved["document"]["metadata"] == {}

    @pytest.mark.asyncio
    async def test_pipeline_small_chunks(self, real_services):
        """Test pipeline with very small chunk size."""
        service = real_services["service"]
        db_client = real_services["db_client"]

        options = IngestionOptions(
            cleanText=True,
            extractMetadata=True,
            chunkSize=5,
            overlap=1,
        )

        result = await service.ingest("file-006", "project-001", options)

        assert result["status"] == "completed"
        assert result["totalChunks"] > 5

    @pytest.mark.asyncio
    async def test_pipeline_large_chunks(self, real_services):
        """Test pipeline with chunk size larger than document."""
        service = real_services["service"]
        db_client = real_services["db_client"]

        options = IngestionOptions(
            cleanText=True,
            extractMetadata=True,
            chunkSize=10000,
            overlap=100,
        )

        result = await service.ingest("file-007", "project-001", options)

        assert result["status"] == "completed"
        assert result["totalChunks"] == 1


class TestMultipleFileIngestion:
    """Test ingesting multiple files in sequence."""

    @pytest.fixture
    def shared_clients(self):
        """Create shared mock clients for multiple ingestions."""
        return {
            "db_client": MockDatabaseClient(),
        }

    @pytest.mark.asyncio
    async def test_ingest_multiple_files(self, shared_clients):
        """Test ingesting multiple files uses same clients."""
        db_client = shared_clients["db_client"]

        for i in range(3):
            storage = MockStorageClient(content=f"Document {i} content for testing.")
            service = IngestionService(
                storage_client=storage,
                chunking_service=ChunkingService(),
                metadata_extractor=MetadataExtractor(),
                db_client=db_client,
                processor_factory=ProcessorFactory([TextProcessor()]),
                text_cleaning_service=TextCleaningService(),
            )

            options = IngestionOptions(chunkSize=100, overlap=10)
            await service.ingest(f"file-{i}", "project-multi", options)

        assert len(db_client.saved_documents) == 3


class TestDocumentOutputStructure:
    """Test that output documents have the correct JSON structure."""

    @pytest.fixture
    def service_with_mock(self):
        """Create service with mock clients."""
        storage = MockStorageClient(content="Test document content for structure validation.")
        db_client = MockDatabaseClient()

        service = IngestionService(
            storage_client=storage,
            chunking_service=ChunkingService(),
            metadata_extractor=MetadataExtractor(),
            db_client=db_client,
            processor_factory=ProcessorFactory([TextProcessor()]),
            text_cleaning_service=TextCleaningService(),
        )

        return {"service": service, "db_client": db_client}

    @pytest.mark.asyncio
    async def test_document_contains_all_required_fields(self, service_with_mock):
        """Test that saved document has all required fields."""
        service = service_with_mock["service"]
        db_client = service_with_mock["db_client"]

        options = IngestionOptions(
            cleanText=True,
            extractMetadata=True,
            chunkSize=100,
            overlap=10,
        )

        await service.ingest("file-test", "project-test", options)

        document = db_client.saved_documents[0]["document"]

        assert "fileId" in document
        assert "projectId" in document
        assert "processedAt" in document
        assert "status" in document
        assert "options" in document
        assert "metadata" in document
        assert "processing" in document
        assert "chunks" in document

    @pytest.mark.asyncio
    async def test_document_options_reflect_input(self, service_with_mock):
        """Test that options in document match input options."""
        service = service_with_mock["service"]
        db_client = service_with_mock["db_client"]

        options = IngestionOptions(
            cleanText=True,
            extractMetadata=False,
            chunkSize=50,
            overlap=5,
        )

        await service.ingest("file-test", "project-test", options)

        document = db_client.saved_documents[0]["document"]

        assert document["options"]["cleanText"] is True
        assert document["options"]["extractMetadata"] is False
        assert document["options"]["chunkSize"] == 50
        assert document["options"]["overlap"] == 5

    @pytest.mark.asyncio
    async def test_chunks_have_correct_structure(self, service_with_mock):
        """Test that each chunk has index, content, and wordCount."""
        service = service_with_mock["service"]
        db_client = service_with_mock["db_client"]

        options = IngestionOptions(chunkSize=10, overlap=2)

        await service.ingest("file-test", "project-test", options)

        document = db_client.saved_documents[0]["document"]
        chunks = document["chunks"]

        for i, chunk in enumerate(chunks):
            assert chunk["index"] == i
            assert "content" in chunk
            assert "wordCount" in chunk
            assert isinstance(chunk["wordCount"], int)
