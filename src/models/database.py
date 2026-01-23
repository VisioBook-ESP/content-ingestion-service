"""SQLAlchemy database models."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.models.schemas import ContentType, IngestionStatus


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Content(Base):
    """Content model for storing ingested content."""

    __tablename__ = "contents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[IngestionStatus] = mapped_column(
        Enum(IngestionStatus), default=IngestionStatus.PENDING, nullable=False
    )
    content_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    processed_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Content(id={self.id}, type={self.content_type}, status={self.status})>"
