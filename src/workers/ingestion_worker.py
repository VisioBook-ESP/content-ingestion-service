import logging

from src.clients.database_client import DatabaseClient
from src.processors.docx_processor import DocxProcessor
from src.processors.html_processor import HTMLProcessor
from src.processors.ocr_processor import OCRProcessor
from src.processors.pdf_processor import PDFProcessor
from src.processors.processor_factory import ProcessorFactory
from src.processors.txt_processor import TextProcessor
from src.services.chunking_service import ChunkingService
from src.services.ingestion_service import IngestionService
from src.services.metadata_extractor import MetadataExtractor
from src.services.storage_client import StorageClient
from src.services.text_cleaning_service import TextCleaningService
from src.workers.job_service import job_service

logger = logging.getLogger(__name__)


class IngestionWorker:
    def __init__(self):
        self.service = IngestionService(
            storage_client=StorageClient(),
            chunking_service=ChunkingService(),
            metadata_extractor=MetadataExtractor(),
            db_client=DatabaseClient(),
            processor_factory=ProcessorFactory(
                [
                    PDFProcessor(),
                    TextProcessor(),
                    DocxProcessor(),
                    HTMLProcessor(),
                    OCRProcessor(),
                ]
            ),
            text_cleaning_service=TextCleaningService(),
        )

    async def run(self, job_id: str, file_id: str, project_id: str, options):
        try:
            job_service.set_status(job_id, "processing")
            result = await self.service.ingest(file_id, project_id, options)
            job_service.set_status(job_id, "completed")
            job_service.set_result(job_id, result)
            logger.info(f"Job {job_id} completed: {result['totalChunks']} chunks")
        except Exception as e:
            job_service.set_status(job_id, "failed")
            job_service.set_error(job_id, str(e))
            logger.error(f"Job {job_id} failed: {e}")


_ingestion_worker: IngestionWorker | None = None


def get_ingestion_worker() -> IngestionWorker:
    global _ingestion_worker
    if _ingestion_worker is None:
        _ingestion_worker = IngestionWorker()
    return _ingestion_worker
