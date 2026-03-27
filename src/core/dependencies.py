"""FastAPI dependencies for authentication and request context."""

import re
from typing import Optional

from fastapi import Header, HTTPException, Request

# UUID v4 pattern
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


async def get_current_user(
    x_user_id: str = Header(..., alias="x-user-id"),
) -> str:
    """Extract and validate the userId set by Istio gateway.

    Istio validates the JWT and injects ``x-user-id`` (from the JWT ``sub``
    claim).  This dependency simply reads the header and validates its format.

    Raises:
        HTTPException 401 – header missing or not a valid UUID.
    """
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(status_code=401, detail="Missing x-user-id header")

    user_id = x_user_id.strip()
    if not _UUID_RE.match(user_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid x-user-id header: must be a valid UUID",
        )
    return user_id


async def get_optional_user(
    x_user_id: Optional[str] = Header(None, alias="x-user-id"),
) -> Optional[str]:
    """Same as ``get_current_user`` but returns ``None`` instead of 401."""
    if not x_user_id or not x_user_id.strip():
        return None
    user_id = x_user_id.strip()
    if not _UUID_RE.match(user_id):
        return None
    return user_id


async def get_authorization_header(
    request: Request,
) -> Optional[str]:
    """Extract the raw Authorization header value (e.g. ``Bearer <token>``).

    Istio forwards the original token when ``forwardOriginalToken: true`` is
    set.  This dependency captures it so outbound S2S calls can propagate it.
    """
    return request.headers.get("Authorization")


async def get_request_id(
    x_request_id: Optional[str] = Header(None, alias="x-request-id"),
) -> Optional[str]:
    """Extract the X-Request-Id header for distributed tracing."""
    return x_request_id
