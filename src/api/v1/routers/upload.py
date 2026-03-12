"""Upload endpoint — stores a file in MinIO and returns a fileId."""

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.services.storage_client import StorageClient

router = APIRouter()


@lru_cache(maxsize=1)
def get_storage_client() -> StorageClient:
    return StorageClient()


class UploadResponse(BaseModel):
    fileId: str
    fileName: str
    fileSize: int
    fileType: str


@router.post("/", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    storage: StorageClient = Depends(get_storage_client),
) -> UploadResponse:
    """Upload a file to MinIO storage and return its fileId."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    file_name = file.filename or "unknown"
    content_type = file.content_type or "application/octet-stream"

    file_id = await storage.upload(
        file_data=content,
        file_name=file_name,
        content_type=content_type,
    )

    return UploadResponse(
        fileId=file_id,
        fileName=file_name,
        fileSize=len(content),
        fileType=Path(file_name).suffix.lower(),
    )
