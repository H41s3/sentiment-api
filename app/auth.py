from fastapi import Header, HTTPException, status

from app.config import settings


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if settings.api_key is None:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Invalid or missing X-Api-Key header."},
        )
