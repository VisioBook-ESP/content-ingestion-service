"""Client for persisting ingestion results to the local PostgreSQL database."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.database.connection import get_session
from src.models.document import Document
from src.models.folder import Folder

logger = logging.getLogger(__name__)


class DatabaseClient:
    async def save_document(
        self,
        project_id: str,
        file_id: str,
        document: dict,
    ) -> bool:
        """Upsert the ingestion result JSON into the documents table."""
        try:
            async with get_session() as session:
                stmt = (
                    insert(Document)
                    .values(
                        file_id=file_id,
                        project_id=project_id,
                        file_name=document.get("fileName"),
                        file_type=document.get("fileType"),
                        status="completed",
                        processed_at=datetime.now(timezone.utc),
                        data=document,
                    )
                    .on_conflict_do_update(
                        index_elements=["file_id"],
                        set_={
                            "project_id": project_id,
                            "status": "completed",
                            "processed_at": datetime.now(timezone.utc),
                            "data": document,
                            "updated_at": datetime.now(timezone.utc),
                        },
                    )
                )
                await session.execute(stmt)
            logger.info(f"Saved document for file {file_id} in project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save document {file_id}: {e}")
            return False

    async def get_document(self, project_id: str, file_id: str) -> dict | None:
        """Retrieve a document by file_id."""
        try:
            async with get_session() as session:
                result = await session.execute(select(Document).where(Document.file_id == file_id))
                doc = result.scalar_one_or_none()
                if doc is None:
                    return None
                return doc.data
        except Exception as e:
            logger.error(f"Failed to get document {file_id}: {e}")
            return None

    async def delete_document(self, project_id: str, file_id: str) -> bool:
        """Delete a document by file_id."""
        try:
            async with get_session() as session:
                result = await session.execute(select(Document).where(Document.file_id == file_id))
                doc = result.scalar_one_or_none()
                if doc:
                    await session.delete(doc)
            logger.info(f"Deleted document for file {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {file_id}: {e}")
            return False

    async def get_documents_by_folder_id(self, folder_id: str) -> list[dict]:
        """Retrieve all documents associated with a given folderId."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(Document).where(Document.data["folderId"].astext == folder_id)
                )
                docs = result.scalars().all()
                return [doc.data for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get documents for folderId {folder_id}: {e}")
            return []

    async def get_or_create_folder(self, user_id: str) -> str:
        """Return the existing folderId for user_id, or create and persist a new one."""
        async with get_session() as session:
            result = await session.execute(select(Folder).where(Folder.user_id == user_id))
            folder = result.scalar_one_or_none()
            if folder:
                logger.info(f"Found existing folder_id={folder.folder_id} for user_id={user_id}")
                return folder.folder_id
            folder_id = str(uuid.uuid4())
            session.add(Folder(user_id=user_id, folder_id=folder_id))
            logger.info(f"Created new folder_id={folder_id} for user_id={user_id}")
            return folder_id

    async def health_check(self) -> bool:
        try:
            async with get_session() as session:
                await session.execute(select(1))
            return True
        except Exception:
            return False
