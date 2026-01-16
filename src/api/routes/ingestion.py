"""Content ingestion endpoints."""

from typing import List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from src.models.schemas import ContentCreateRequest, ContentResponse, IngestionStatus
from src.services.ingestion.processor import ContentProcessor

router = APIRouter()
processor = ContentProcessor()


@router.post(
    "/ingest",
    response_model=ContentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_content(
    content_request: ContentCreateRequest,
    background_tasks: BackgroundTasks,
):
    """
    Ingest new content for processing.

    The content will be processed asynchronously in the background.
    """
    try:
        content_id = await processor.create_content(content_request)
        background_tasks.add_task(processor.process_content, content_id)

        return ContentResponse(
            id=content_id,
            status=IngestionStatus.PENDING,
            message="Content ingestion started",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start content ingestion: {str(e)}",
        )


@router.get(
    "/ingest/{content_id}",
    response_model=ContentResponse,
)
async def get_ingestion_status(content_id: str):
    """Get the status of a content ingestion job."""
    try:
        content = await processor.get_content_status(content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content with id {content_id} not found",
            )
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve content status: {str(e)}",
        )


@router.get(
    "/ingest",
    response_model=List[ContentResponse],
)
async def list_ingested_content(
    skip: int = 0,
    limit: int = 100,
):
    """List all ingested content with pagination."""
    try:
        contents = await processor.list_contents(skip=skip, limit=limit)
        return contents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list contents: {str(e)}",
        )
