"""MinIO storage client."""

import asyncio
import io
import logging
import tempfile
import uuid
from pathlib import Path

from minio import Minio

from src.core.config import settings

logger = logging.getLogger(__name__)


class StorageClient:
    def __init__(self) -> None:
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            logger.info(f"Created MinIO bucket: {self.bucket}")

    async def upload(self, file_data: bytes, file_name: str, content_type: str) -> str:
        file_id = str(uuid.uuid4())
        object_name = f"{file_id}/{file_name}"

        def _put() -> None:
            self.client.put_object(
                self.bucket,
                object_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
            )

        await asyncio.to_thread(_put)
        logger.info(f"Uploaded {file_name} → MinIO {object_name}")
        return file_id

    async def download(self, file_id: str) -> Path:
        def _list():
            return list(self.client.list_objects(self.bucket, prefix=f"{file_id}/"))

        objects = await asyncio.to_thread(_list)
        if not objects:
            raise FileNotFoundError(f"File {file_id} not found in MinIO")

        object_name = objects[0].object_name
        suffix = Path(object_name).suffix or ".bin"

        def _get() -> bytes:
            response = self.client.get_object(self.bucket, object_name)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        data = await asyncio.to_thread(_get)

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(data)
            path = Path(tmp.name)

        logger.info(f"Downloaded {object_name} → {path}")
        return path

    async def get_file_info(self, file_id: str) -> dict:
        def _list():
            return list(self.client.list_objects(self.bucket, prefix=f"{file_id}/"))

        objects = await asyncio.to_thread(_list)
        if not objects:
            return {}

        obj = objects[0]
        return {
            "fileId": file_id,
            "fileName": Path(obj.object_name).name,
            "size": obj.size,
            "lastModified": obj.last_modified.isoformat() if obj.last_modified else None,
        }

    async def delete(self, file_id: str) -> None:
        def _delete() -> None:
            objects = list(self.client.list_objects(self.bucket, prefix=f"{file_id}/"))
            for obj in objects:
                self.client.remove_object(self.bucket, obj.object_name)

        await asyncio.to_thread(_delete)
        logger.info(f"Deleted MinIO objects for file_id={file_id}")

    async def health_check(self) -> bool:
        try:
            await asyncio.to_thread(self.client.bucket_exists, self.bucket)
            return True
        except Exception:
            return False
