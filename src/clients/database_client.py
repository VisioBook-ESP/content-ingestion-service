"""Client for core-database-service communication."""

import logging
from typing import Optional

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or getattr(
            settings, "DATABASE_SERVICE_URL", "http://localhost:8081"
        )
        self.timeout = httpx.Timeout(60.0)

    async def save_document(
        self,
        project_id: str,
        file_id: str,
        document: dict,
    ) -> bool:
        """Save the complete ingestion result as JSON document."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/documents",
                    json=document,
                )
                response.raise_for_status()
                logger.info(f"Saved document for file {file_id} in project {project_id}")
                return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Database service returned error: {e.response.status_code}")
            return False
        except httpx.RequestError as e:
            logger.warning(f"Could not reach database service: {e}")
            return False

    async def get_document(self, project_id: str, file_id: str) -> Optional[dict]:
        """Retrieve a document by project and file ID."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/documents/{project_id}/{file_id}",
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None

    async def delete_document(self, project_id: str, file_id: str) -> bool:
        """Delete a document."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/api/v1/documents/{project_id}/{file_id}",
                )
                response.raise_for_status()
                logger.info(f"Deleted document for file {file_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
