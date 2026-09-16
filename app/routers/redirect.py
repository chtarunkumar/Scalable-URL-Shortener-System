import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import URL, Click
from app.cache import get_redis
from app.config import settings

router = APIRouter(tags=["redirect"])

CACHE_TTL = 3600


@router.get("/{short_code}")
async def redirect_url(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    redis = await get_redis()
    cache_key = f"url:{short_code}"

    # Try cache first
    original_url = await redis.get(cache_key)

    if original_url is None:
        result = await db.execute(
            select(URL).where(URL.short_code == short_code, URL.is_active == True)
        )
        url: URL | None = result.scalar_one_or_none()

        if not url:
            raise HTTPException(status_code=404, detail="Short URL not found")

        # Check expiry
        if url.expires_at and url.expires_at < datetime.datetime.now(datetime.timezone.utc):
            raise HTTPException(status_code=410, detail="This link has expired")

        original_url = url.original_url
        await redis.setex(cache_key, CACHE_TTL, original_url)
        url_id = url.id
    else:
        # Fetch id for click tracking (lightweight query)
        result = await db.execute(select(URL.id).where(URL.short_code == short_code))
        row = result.first()
        url_id = row[0] if row else None

    # Record click asynchronously (best-effort)
    if url_id:
        click = Click(
            url_id=url_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer"),
        )
        db.add(click)
        await db.commit()

    return RedirectResponse(url=original_url, status_code=302)
