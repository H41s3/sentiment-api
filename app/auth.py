from fastapi import Header, HTTPException, status

from app.config import settings

__all__ = ["verify_api_key"]


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency that enforces API key authentication when configured.

    Auth is deliberately opt-in: if API_KEY is not set in the environment this
    dependency is a no-op and all requests pass through. This means existing
    deployments keep working after this feature ships — operators enable auth
    by setting a single env var, no code change required.

    Implemented as a route-level dependency rather than middleware so that the
    health endpoints (/health/live, /health/ready) remain publicly accessible.
    Container orchestration probes must always reach them, regardless of auth state.
    """
    if settings.api_key is None:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Invalid or missing X-Api-Key header."},
        )
