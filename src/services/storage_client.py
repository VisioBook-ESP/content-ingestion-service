"""Client for support-storage-service communication."""

import httpx
import tempfile
import os
from pathlib import Path
from typing import Optional
import logging

from src.core.config import settings


logger = logging.getLogger(__name__)


class StorageClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.STORAGE_SERVICE_URL
        self.timeout = httpx.Timeout(60.0)

    async def download(self, file_id: str) -> Path:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/files/{file_id}")
                response.raise_for_status()

                content_disposition = response.headers.get("content-disposition", "")
                filename = file_id
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[1].strip('"')

                suffix = os.path.splitext(filename)[1] or ".bin"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(response.content)
                    path = Path(tmp.name)

                logger.info(f"Downloaded file {file_id} to {path}")
                return path

        except httpx.HTTPStatusError as e:
            logger.error(f"Storage service returned error: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Could not reach storage service: {e}")
            raise

    async def get_file_info(self, file_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/files/{file_id}/info")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {}

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False