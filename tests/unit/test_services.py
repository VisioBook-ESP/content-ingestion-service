"""Unit tests for services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from src.services.text_cleaning_service import TextCleaningService
from src.services.chunking_service import ChunkingService
from src.services.metadata_extractor import MetadataExtractor
from src.services.ingestion_service import IngestionService
from src.schemas.preprocess import CleanOptions
from src.schemas.ingest import IngestionOptions


class TestTextCleaningService:
    """Tests for TextCleaningService."""

    def test_remove_extra_spaces(self):
        service = TextCleaningService()
        options = CleanOptions(
            removeExtraSpaces=True,
            normalizeQuotes=False,
            fixEncoding=False,
        )

        text = "Hello    world   with    spaces"
        cleaned, changes = service.clean(text, options)

        assert "    " not in cleaned
        assert "removeExtraSpaces" in changes

    def test_normalize_quotes(self):
        service = TextCleaningService()
        options = CleanOptions(
            removeExtraSpaces=False,
            normalizeQuotes=True,
            fixEncoding=False,
        )

        text = 'Test «guillemets» et "quotes"'
        cleaned, changes = service.clean(text, options)

        assert "«" not in cleaned
        assert "»" not in cleaned
        assert "normalizeQuotes" in changes

    def test_fix_encoding(self):
        service = TextCleaningService()
        options = CleanOptions(
            removeExtraSpaces=False,
            normalizeQuotes=False,
            fixEncoding=True,
        )

        text = "Café résumé"
        cleaned, changes = service.clean(text, options)

        assert "fixEncoding" in changes
        assert isinstance(cleaned, str)

    def test_all_options_enabled(self, clean_options):
        service = TextCleaningService()
        text = "Test   «guillemets»   avec   espaces"

        cleaned, changes = service.clean(text, clean_options)

        assert len(changes) >= 2
        assert "  " not in cleaned

    def test_no_options_enabled(self):
        service = TextCleaningService()
        options = CleanOptions(
            removeExtraSpaces=False,
            normalizeQuotes=False,
            fixEncoding=False,
            removeHeaders=False,
            removeFooters=False,
        )

        text = "Original   text   unchanged"
        cleaned, changes = service.clean(text, options)

        assert cleaned == text
        assert len(changes) == 0


class TestChunkingService:
    """Tests for ChunkingService."""

    def test_chunk_simple_text(self):
        service = ChunkingService()
        text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"

        chunks = service.chunk(text, size=5, overlap=1)

        assert len(chunks) >= 2
        assert all(len(chunk.split()) <= 5 for chunk in chunks)

    def test_chunk_with_overlap(self):
        service = ChunkingService()
        text = "one two three four five six seven eight nine ten"

        chunks = service.chunk(text, size=5, overlap=2)

        if len(chunks) >= 2:
            first_words = set(chunks[0].split())
            second_words = set(chunks[1].split())
            overlap = first_words & second_words
            assert len(overlap) >= 1

    def test_chunk_short_text(self):
        service = ChunkingService()
        text = "short text"

        chunks = service.chunk(text, size=100, overlap=10)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_empty_text(self):
        service = ChunkingService()
        text = ""

        chunks = service.chunk(text, size=10, overlap=2)

        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_chunk_respects_size(self):
        service = ChunkingService()
        text = " ".join([f"word{i}" for i in range(100)])

        chunks = service.chunk(text, size=20, overlap=5)

        for chunk in chunks:
            assert len(chunk.split()) <= 20


class TestMetadataExtractor:
    """Tests for MetadataExtractor."""

    def test_enrich_adds_word_count(self):
        extractor = MetadataExtractor()
        metadata = {}
        text = "This is a test with seven words"

        enriched = extractor.enrich(metadata, text)

        assert enriched["wordCount"] == 7

    def test_enrich_adds_char_count(self):
        extractor = MetadataExtractor()
        metadata = {}
        text = "Test text"

        enriched = extractor.enrich(metadata, text)

        assert enriched["charCount"] == len(text)

    def test_detect_french_language(self):
        extractor = MetadataExtractor()
        metadata = {}
        text = "Le chat est sur la table dans le jardin"

        enriched = extractor.enrich(metadata, text)

        assert enriched["language"] == "fr"

    def test_detect_english_language(self):
        extractor = MetadataExtractor()
        metadata = {}
        text = "The cat is on the table with the dog and a bird"

        enriched = extractor.enrich(metadata, text)

        assert enriched["language"] == "en"

    def test_preserves_existing_metadata(self):
        extractor = MetadataExtractor()
        metadata = {"title": "Test Title", "author": "Test Author"}
        text = "Some text content"

        enriched = extractor.enrich(metadata, text)

        assert enriched["title"] == "Test Title"
        assert enriched["author"] == "Test Author"

    def test_adds_custom_fields(self):
        extractor = MetadataExtractor()
        metadata = {}
        text = "First paragraph.\n\nSecond paragraph."

        enriched = extractor.enrich(metadata, text)

        assert "customFields" in enriched
        assert "paragraphCount" in enriched["customFields"]


class TestIngestionService:
    """Tests for IngestionService."""

    @pytest.fixture
    def ingestion_service(
        self, mock_storage_client, mock_db_client, mock_processor_factory
    ):
        """Create ingestion service with mocks."""
        return IngestionService(
            storage_client=mock_storage_client,
            chunking_service=ChunkingService(),
            metadata_extractor=MetadataExtractor(),
            db_client=mock_db_client,
            processor_factory=mock_processor_factory,
            text_cleaning_service=TextCleaningService(),
        )

    @pytest.mark.asyncio
    async def test_ingest_downloads_file(
        self, ingestion_service, mock_storage_client, ingestion_options
    ):
        """Test that ingestion downloads the file from storage."""
        await ingestion_service.ingest("file-123", "project-456", ingestion_options)

        assert mock_storage_client.download_called is True
        assert mock_storage_client.downloaded_file_id == "file-123"

    @pytest.mark.asyncio
    async def test_ingest_saves_document(
        self, ingestion_service, mock_db_client, ingestion_options
    ):
        """Test that ingestion saves document to database."""
        await ingestion_service.ingest("file-123", "project-456", ingestion_options)

        assert mock_db_client.save_called is True
        assert len(mock_db_client.saved_documents) == 1
        assert mock_db_client.saved_documents[0]["project_id"] == "project-456"
        assert mock_db_client.saved_documents[0]["file_id"] == "file-123"

    @pytest.mark.asyncio
    async def test_ingest_returns_result(self, ingestion_service, ingestion_options):
        """Test that ingestion returns a result dict."""
        result = await ingestion_service.ingest("file-123", "project-456", ingestion_options)

        assert result["status"] == "completed"
        assert "totalChunks" in result
        assert result["totalChunks"] > 0

    @pytest.mark.asyncio
    async def test_ingest_without_clean_text(
        self, ingestion_service, mock_db_client
    ):
        """Test ingestion without text cleaning."""
        options = IngestionOptions(
            cleanText=False,
            extractMetadata=True,
            chunkSize=100,
            overlap=10,
        )

        await ingestion_service.ingest("file-123", "project-456", options)

        assert mock_db_client.save_called is True

    @pytest.mark.asyncio
    async def test_ingest_without_metadata(
        self, ingestion_service, mock_db_client
    ):
        """Test ingestion without metadata extraction."""
        options = IngestionOptions(
            cleanText=True,
            extractMetadata=False,
            chunkSize=100,
            overlap=10,
        )

        await ingestion_service.ingest("file-123", "project-456", options)

        saved = mock_db_client.saved_documents[0]
        assert saved["document"]["metadata"] == {}

    @pytest.mark.asyncio
    async def test_saved_document_has_correct_structure(
        self, ingestion_service, mock_db_client, ingestion_options
    ):
        """Test that saved document has the expected JSON structure."""
        await ingestion_service.ingest("file-123", "project-456", ingestion_options)

        saved = mock_db_client.saved_documents[0]
        document = saved["document"]

        assert "fileId" in document
        assert "projectId" in document
        assert "processedAt" in document
        assert "status" in document
        assert "options" in document
        assert "metadata" in document
        assert "processing" in document
        assert "chunks" in document

        assert document["fileId"] == "file-123"
        assert document["projectId"] == "project-456"
        assert document["status"] == "completed"
