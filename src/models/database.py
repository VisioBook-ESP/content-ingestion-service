"""SQLAlchemy database models."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, String, Text
from sqlalchemy.orm import DeclarativeBase

from src.models.schemas import ContentType, IngestionStatus


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Content(Base):
    """Content model for storing ingested content."""

    __tablename__ = "contents"

    id = Column(String(36), primary_key=True, index=True)
    content_type = Column(Enum(ContentType), nullable=False)
    source = Column(Text, nullable=False)
    status = Column(Enum(IngestionStatus), default=IngestionStatus.PENDING, nullable=False)
    metadata = Column(JSON, nullable=True)
    processed_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Content(id={self.id}, type={self.content_type}, status={self.status})>"
