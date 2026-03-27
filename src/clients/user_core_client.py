"""Client for core-user-service — resolves userId from a Bearer token."""

import logging
from typing import Optional

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class UserCoreClient:
    def __init__(self) -> None:
        self.base_url = settings.CORE_USER_SERVICE_URL
        self.timeout = httpx.Timeout(10.0)

    async def get_user_id(self, token: str) -> Optional[str]:
        """Return the userId of the user identified by token."""
        logger.info("get-user-id: calling core-user-service")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                user_id = response.json().get("uuid")
                logger.info("get-user-id: success — user_id=%s", user_id)
                return str(user_id) if user_id else None
        except httpx.HTTPStatusError as e:
            logger.warning("get-user-id: HTTP %s from core-user-service", e.response.status_code)
            return None
        except Exception as e:
            logger.warning("get-user-id: failed to reach core-user-service — %s", e)
            return None
