"""Pydantic schemas for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, HttpUrl


class IngestionStatus(str, Enum):
    """Content ingestion status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentType(str, Enum):
    """Supported content types."""

    TEXT = "text"
    URL = "url"
    FILE = "file"
    JSON = "json"


class ContentCreateRequest(BaseModel):
    """Request model for creating new content."""

    content_type: ContentType = Field(..., description="Type of content to ingest")
    source: str = Field(..., description="Content source (URL, text, file path, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "content_type": "url",
                "source": "https://example.com/article",
                "metadata": {
                    "author": "John Doe",
                    "tags": ["news", "technology"],
                },
            }
        }


class ContentResponse(BaseModel):
    """Response model for content operations."""

    id: str = Field(..., description="Unique content identifier")
    status: IngestionStatus = Field(..., description="Current processing status")
    message: Optional[str] = Field(None, description="Status message")
    content_type: Optional[ContentType] = None
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error: Optional[str] = Field(None, description="Error message if status is failed")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "message": "Content successfully ingested",
                "content_type": "url",
                "source": "https://example.com/article",
                "created_at": "2024-01-16T10:00:00Z",
                "updated_at": "2024-01-16T10:01:00Z",
            }
        }
