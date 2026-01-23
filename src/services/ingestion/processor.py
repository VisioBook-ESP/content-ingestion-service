"""Content processor for ingestion operations."""

import uuid
from typing import List, Optional

import structlog
from sqlalchemy import select

from src.database.connection import get_session
from src.models.database import Content
from src.models.schemas import (
    ContentCreateRequest,
    ContentResponse,
    ContentType,
    IngestionStatus,
)

logger = structlog.get_logger(__name__)


class ContentProcessor:
    """Handles content ingestion and processing."""

    async def create_content(self, request: ContentCreateRequest) -> str:
        """Create a new content entry."""
        content_id = str(uuid.uuid4())

        async with get_session() as session:
            content = Content(
                id=content_id,
                content_type=request.content_type,
                source=request.source,
                status=IngestionStatus.PENDING,
                metadata=request.metadata,
            )
            session.add(content)
            await session.commit()

        logger.info("Content created", content_id=content_id, content_type=request.content_type)
        return content_id

    async def process_content(self, content_id: str) -> None:
        """Process content based on its type."""
        try:
            async with get_session() as session:
                result = await session.execute(select(Content).where(Content.id == content_id))
                content = result.scalar_one_or_none()

                if not content:
                    logger.error("Content not found", content_id=content_id)
                    return

                content.status = IngestionStatus.PROCESSING
                await session.commit()

            logger.info(
                "Processing content", content_id=content_id, content_type=content.content_type
            )

            # Process based on content type
            if content.content_type == ContentType.URL:
                await self._process_url_content(content_id, content.source)
            elif content.content_type == ContentType.TEXT:
                await self._process_text_content(content_id, content.source)
            elif content.content_type == ContentType.FILE:
                await self._process_file_content(content_id, content.source)
            elif content.content_type == ContentType.JSON:
                await self._process_json_content(content_id, content.source)

            # Mark as completed
            async with get_session() as session:
                result = await session.execute(select(Content).where(Content.id == content_id))
                content = result.scalar_one_or_none()
                if content:
                    content.status = IngestionStatus.COMPLETED
                    await session.commit()

            logger.info("Content processing completed", content_id=content_id)

        except Exception as e:
            logger.error("Content processing failed", content_id=content_id, error=str(e))
            async with get_session() as session:
                result = await session.execute(select(Content).where(Content.id == content_id))
                content = result.scalar_one_or_none()
                if content:
                    content.status = IngestionStatus.FAILED
                    content.error_message = str(e)
                    await session.commit()

    async def _process_url_content(self, content_id: str, url: str) -> None:
        """Process URL content."""
        # TODO: Implement URL content fetching and processing
        logger.info("Processing URL content", content_id=content_id, url=url)
        pass

    async def _process_text_content(self, content_id: str, text: str) -> None:
        """Process text content."""
        # TODO: Implement text processing
        logger.info("Processing text content", content_id=content_id)
        pass

    async def _process_file_content(self, content_id: str, file_path: str) -> None:
        """Process file content."""
        # TODO: Implement file processing
        logger.info("Processing file content", content_id=content_id, file_path=file_path)
        pass

    async def _process_json_content(self, content_id: str, json_data: str) -> None:
        """Process JSON content."""
        # TODO: Implement JSON processing
        logger.info("Processing JSON content", content_id=content_id)
        pass

    async def get_content_status(self, content_id: str) -> Optional[ContentResponse]:
        """Get content processing status."""
        async with get_session() as session:
            result = await session.execute(select(Content).where(Content.id == content_id))
            content = result.scalar_one_or_none()

            if not content:
                return None

            return ContentResponse(
                id=content.id,
                status=content.status,
                content_type=content.content_type,
                source=content.source,
                metadata=content.metadata,
                created_at=content.created_at,
                updated_at=content.updated_at,
                error=content.error_message,
            )

    async def list_contents(self, skip: int = 0, limit: int = 100) -> List[ContentResponse]:
        """List all contents with pagination."""
        async with get_session() as session:
            result = await session.execute(select(Content).offset(skip).limit(limit))
            contents = result.scalars().all()

            return [
                ContentResponse(
                    id=content.id,
                    status=content.status,
                    content_type=content.content_type,
                    source=content.source,
                    metadata=content.metadata,
                    created_at=content.created_at,
                    updated_at=content.updated_at,
                    error=content.error_message,
                )
                for content in contents
            ]
