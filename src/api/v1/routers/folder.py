import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.clients.database_client import DatabaseClient
from src.core.dependencies import get_current_user

router = APIRouter()


class FolderResponse(BaseModel):
    folderId: str


@router.post("/", response_model=FolderResponse, status_code=201)
async def create_folder():
    """Generate a folderId to associate files during ingestion."""
    return FolderResponse(folderId=str(uuid.uuid4()))


@router.get("/files")
async def get_files_by_token(
    user_id: str = Depends(get_current_user),
):
    """Return all ingested files belonging to the authenticated user.

    The userId is read from the ``x-user-id`` header injected by Istio.
    """
    db = DatabaseClient()
    folder_id = await db.get_or_create_folder(user_id)
    documents = await db.get_documents_by_folder_id(folder_id)
    return {"folderId": folder_id, "count": len(documents), "files": documents}
