"""Mock classes for testing ingestion pipeline."""

import tempfile
from pathlib import Path
from typing import List, Optional


class MockStorageClient:
    """Mock storage client for testing."""

    def __init__(self, content: str = "Texte de test pour l'ingestion mock."):
        self.content = content
        self.download_called = False
        self.downloaded_file_id: Optional[str] = None

    async def download(self, file_id: str) -> Path:
        """Simulate file download."""
        self.download_called = True
        self.downloaded_file_id = file_id

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(self.content)
            return Path(f.name)

    async def get_file_info(self, file_id: str) -> dict:
        return {
            "id": file_id,
            "filename": f"{file_id}.txt",
            "size": len(self.content),
            "content_type": "text/plain",
        }

    async def health_check(self) -> bool:
        return True


class MockDatabaseClient:
    """Mock database client for testing."""

    def __init__(self):
        self.save_called = False
        self.saved_documents: List[dict] = []

    async def save_document(
        self,
        project_id: str,
        file_id: str,
        document: dict,
    ) -> bool:
        """Save complete JSON document."""
        self.save_called = True
        self.saved_documents.append(
            {
                "project_id": project_id,
                "file_id": file_id,
                "document": document,
            }
        )
        return True

    async def get_document(self, project_id: str, file_id: str) -> Optional[dict]:
        for saved in self.saved_documents:
            if saved["project_id"] == project_id and saved["file_id"] == file_id:
                return saved["document"]
        return None

    async def delete_document(self, project_id: str, file_id: str) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


class MockPDFProcessor:
    """Mock PDF processor as specified in documentation."""

    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith(".pdf")

    def extract_text(self, file_path: str) -> str:
        return "Texte extrait du PDF mock pour les tests."

    def extract_metadata(self, file_path: str) -> dict:
        return {
            "title": "Test Document",
            "author": "Test Author",
            "pages": 10,
        }


class MockTextProcessor:
    """Mock text processor for testing."""

    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith(".txt")

    def extract_text(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def extract_metadata(self, file_path: str) -> dict:
        return {}


class MockProcessorFactory:
    """Mock processor factory for testing."""

    def __init__(self):
        self.processors = [
            MockPDFProcessor(),
            MockTextProcessor(),
        ]

    def get_processor(self, file_path: str):
        for processor in self.processors:
            if processor.can_handle(file_path):
                return processor
        raise Exception(f"Unsupported file type: {file_path}")


class MockJobService:
    """Mock job service for testing."""

    def __init__(self):
        self.jobs = {}

    def create_job(self) -> str:
        import uuid

        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {"status": "queued", "result": None, "error": None}
        return job_id

    def set_status(self, job_id: str, status: str):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
        else:
            self.jobs[job_id] = {"status": status}

    def set_result(self, job_id: str, result: dict):
        if job_id in self.jobs:
            self.jobs[job_id]["result"] = result

    def set_error(self, job_id: str, error: str):
        if job_id in self.jobs:
            self.jobs[job_id]["error"] = error

    def get_status(self, job_id: str) -> dict:
        return self.jobs.get(job_id, {"status": "unknown"})

    def get_job(self, job_id: str) -> Optional[dict]:
        return self.jobs.get(job_id)
