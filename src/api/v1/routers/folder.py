import uuid

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class FolderResponse(BaseModel):
    folderId: str


@router.post("/", response_model=FolderResponse, status_code=201)
async def create_folder():
    """Generate a folderId to associate files during ingestion."""
    return FolderResponse(folderId=str(uuid.uuid4()))
