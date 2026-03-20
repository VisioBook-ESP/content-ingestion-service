"""Client for core-user-service — resolves folderId from a Bearer token."""

import logging
from typing import Optional

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class UserCoreClient:
    def __init__(self) -> None:
        self.base_url = settings.CORE_USER_SERVICE_URL
        self.timeout = httpx.Timeout(10.0)

    async def get_folder_id(self, token: str) -> Optional[str]:
        """Return the folderId associated with the user identified by token."""
        logger.info("resolve-folder: calling core-user-service")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/resolve-folder",
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                folder_id = response.json().get("folderId")
                logger.info("resolve-folder: success — folder_id=%s", folder_id)
                return folder_id
        except httpx.HTTPStatusError as e:
            logger.warning("resolve-folder: HTTP %s from core-user-service", e.response.status_code)
            return None
        except Exception as e:
            logger.warning("resolve-folder: failed to reach core-user-service — %s", e)
            return None
