"""Ingestion service orchestrating the document processing pipeline."""

import logging
import os
from datetime import datetime, timezone

from src.schemas.preprocess import CleanOptions

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        storage_client,
        chunking_service,
        metadata_extractor,
        db_client,
        processor_factory,
        text_cleaning_service,
    ):
        self.storage_client = storage_client
        self.chunking_service = chunking_service
        self.metadata_extractor = metadata_extractor
        self.db_client = db_client
        self.processor_factory = processor_factory
        self.text_cleaning_service = text_cleaning_service

    async def ingest(
        self, file_id: str, project_id: str, options, folder_id: str | None = None
    ) -> dict:
        logger.info(f"Starting ingestion for file {file_id} in project {project_id}")

        file_path = await self.storage_client.download(file_id)
        logger.info(f"Downloaded file to {file_path}")

        try:
            # 1. Extract text from file
            processor = self.processor_factory.get_processor(str(file_path))
            raw_text = processor.extract_text(str(file_path))
            logger.info(f"Extracted {len(raw_text)} characters from file")

            # 2. Clean text (normalize)
            if options.cleanText:
                clean_options = CleanOptions(
                    removeExtraSpaces=True,
                    normalizeQuotes=True,
                    fixEncoding=True,
                    removeHeaders=False,
                    removeFooters=False,
                )
                cleaned_text, changes = self.text_cleaning_service.clean(raw_text, clean_options)
                logger.info(f"Text cleaned, applied: {changes}")
            else:
                cleaned_text = raw_text
                changes = []

            # 3. Extract metadata
            metadata = {}
            if options.extractMetadata:
                metadata = processor.extract_metadata(str(file_path))
                metadata = self.metadata_extractor.enrich(metadata, cleaned_text)
                logger.info(f"Extracted metadata: {metadata.get('wordCount', 0)} words")

            # 4. Chunk text
            chunks = self.chunking_service.chunk(
                cleaned_text,
                options.chunkSize,
                options.overlap,
            )
            logger.info(f"Created {len(chunks)} chunks")

            # 5. Build JSON output document
            output_document = {
                "fileId": file_id,
                "projectId": project_id,
                "folderId": folder_id,
                "fileName": file_path.name,
                "fileType": file_path.suffix.lower(),
                "processedAt": datetime.now(timezone.utc).isoformat(),
                "status": "completed",
                "options": {
                    "cleanText": options.cleanText,
                    "extractMetadata": options.extractMetadata,
                    "chunkSize": options.chunkSize,
                    "overlap": options.overlap,
                },
                "metadata": metadata,
                "processing": {
                    "cleaningApplied": changes,
                    "totalChunks": len(chunks),
                    "totalCharacters": len(cleaned_text),
                },
                "chunks": [
                    {
                        "index": i,
                        "content": chunk,
                        "wordCount": len(chunk.split()),
                    }
                    for i, chunk in enumerate(chunks)
                ],
            }

            # 6. Save JSON to database
            await self.db_client.save_document(project_id, file_id, output_document)
            logger.info(f"Saved JSON document to database for file {file_id}")

            return {
                "status": "completed",
                "fileId": file_id,
                "projectId": project_id,
                "folderId": folder_id,
                "totalChunks": len(chunks),
                "metadata": metadata,
            }

        finally:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file {file_path}")
