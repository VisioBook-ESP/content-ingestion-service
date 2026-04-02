"""Endpoints for retrieving processed document data by fileId."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.clients.database_client import DatabaseClient
from src.core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentTextResponse(BaseModel):
    """Response shape consumed by core-project-service."""

    text: str
    wordCount: int
    metadata: dict


@router.get("/{file_id}", response_model=DocumentTextResponse)
async def get_document_text(
    file_id: str,
    user_id: str = Depends(get_current_user),
):
    """Return extracted text, word count, and metadata for a processed file.

    Ownership is enforced: the document's ``userId`` must match the
    caller's ``x-user-id`` header.
    """
    db = DatabaseClient()
    doc = await db.get_document_by_file_id(file_id)

    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Ownership check — return 404 (not 403) to prevent enumeration
    if doc.get("userId") != user_id:
        logger.warning(
            "Ownership mismatch for file_id=%s: expected=%s got=%s",
            file_id,
            doc.get("userId"),
            user_id,
        )
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.get("status") != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Document processing not completed (status: {doc.get('status')})",
        )

    # Reconstruct full text from chunks if available, otherwise use raw text
    chunks = doc.get("chunks", [])
    if chunks:
        text = "\n".join(chunk.get("content", "") for chunk in chunks)
    else:
        text = doc.get("text", "")

    metadata = doc.get("metadata", {})
    word_count = metadata.get("wordCount", 0) or len(text.split())

    return DocumentTextResponse(
        text=text,
        wordCount=word_count,
        metadata=metadata,
    )
