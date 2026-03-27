import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from src.clients.database_client import DatabaseClient
from src.clients.user_core_client import UserCoreClient

router = APIRouter()


class FolderResponse(BaseModel):
    folderId: str


@router.post("/", response_model=FolderResponse, status_code=201)
async def create_folder():
    """Generate a folderId to associate files during ingestion."""
    return FolderResponse(folderId=str(uuid.uuid4()))


@router.get("/files")
async def get_files_by_token(request: Request):
    """Return all ingested files belonging to the authenticated user."""
    auth_header = request.headers.get("Authorization", "")
    token = (
        auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else None
    )
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")

    user_id = await UserCoreClient().get_user_id(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not resolve userId from token"
        )

    db = DatabaseClient()
    folder_id = await db.get_or_create_folder(user_id)
    documents = await db.get_documents_by_folder_id(folder_id)
    return {"folderId": folder_id, "count": len(documents), "files": documents}
