import hmac

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


async def verify_token(authorization: str | None = Header(default=None)) -> None:
    """Optional bearer-token guard. Enabled only when API_AUTH_TOKEN is set."""
    expected = get_settings().api_auth_token
    if not expected:
        return
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing bearer token")
