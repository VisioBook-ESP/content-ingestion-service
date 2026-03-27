"""add_folders_table

Revision ID: a1b2c3d4e5f6
Revises: f5a76b96de87
Create Date: 2026-03-27 00:00:00.000000+00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f5a76b96de87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("folder_id", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_folders_user_id", "folders", ["user_id"], unique=True)
    op.create_index("ix_folders_folder_id", "folders", ["folder_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_folders_folder_id", table_name="folders")
    op.drop_index("ix_folders_user_id", table_name="folders")
    op.drop_table("folders")
