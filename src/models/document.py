"""Document SQLAlchemy model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Document(Base):
    """Ingested document stored as JSONB with searchable columns."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    file_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    project_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    file_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    file_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (Index("ix_documents_project_status", "project_id", "status"),)

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, file_id={self.file_id}, status={self.status})>"
