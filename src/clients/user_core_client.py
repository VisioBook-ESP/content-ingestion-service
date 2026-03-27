"""Client for core-user-service.

NOTE: Since Istio gateway now validates JWT and injects ``x-user-id``, this
client is NO LONGER called on every request to resolve userId.  The
``get_current_user`` FastAPI dependency (``src.core.dependencies``) reads the
header directly.

This client is kept for cases where the service needs to fetch additional user
profile data (e.g. display name, preferences) beyond the userId.
"""

import logging
from typing import Optional

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class UserCoreClient:
    def __init__(self, s2s_headers: Optional[dict[str, str]] = None) -> None:
        self.base_url = settings.CORE_USER_SERVICE_URL
        self.timeout = httpx.Timeout(10.0)
        self._s2s_headers = s2s_headers or {}

    async def get_user_id(self, token: str) -> Optional[str]:
        """Return the userId of the user identified by token.

        DEPRECATED: Prefer reading ``x-user-id`` header via the
        ``get_current_user`` dependency instead.
        """
        logger.info("get-user-id: calling core-user-service")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {**self._s2s_headers, "Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{self.base_url}/api/v1/users/me",
                    headers=headers,
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

    async def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Fetch a user's profile by userId (uses S2S headers)."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {**self._s2s_headers}
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user_id}",
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning("get-user-profile: failed — %s", e)
            return None
