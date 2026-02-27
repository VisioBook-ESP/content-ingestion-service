"""initial_create_documents_table

Revision ID: f5a76b96de87
Revises:
Create Date: 2026-02-13 09:21:38.602476+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f5a76b96de87"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("file_id", sa.String(255), nullable=False),
        sa.Column("project_id", sa.String(255), nullable=True),
        sa.Column("file_name", sa.String(500), nullable=True),
        sa.Column("file_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data", postgresql.JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("ix_documents_file_id", "documents", ["file_id"], unique=True)
    op.create_index("ix_documents_project_id", "documents", ["project_id"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index(
        "ix_documents_project_status", "documents", ["project_id", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_documents_project_status", table_name="documents")
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_project_id", table_name="documents")
    op.drop_index("ix_documents_file_id", table_name="documents")
    op.drop_table("documents")
