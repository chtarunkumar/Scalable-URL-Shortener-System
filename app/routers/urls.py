import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models import URL, Click, User
from app.schemas import URLCreate, URLOut
from app.auth import get_current_user, get_current_user_optional
from app.cache import get_redis
from app.config import settings
from app.utils import generate_short_code

router = APIRouter(tags=["urls"])
limiter = Limiter(key_func=get_remote_address)

CACHE_TTL = 3600  # 1 hour


def _build_url_out(url: URL, click_count: int) -> URLOut:
    return URLOut(
        id=url.id,
        original_url=url.original_url,
        short_code=url.short_code,
        short_url=f"{settings.BASE_URL}/{url.short_code}",
        is_active=url.is_active,
        created_at=url.created_at,
        expires_at=url.expires_at,
        click_count=click_count,
    )


@router.post("/shorten", response_model=URLOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def shorten_url(
    request: Request,
    payload: URLCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    short_code = payload.custom_code or generate_short_code()

    # Ensure uniqueness
    existing = await db.execute(select(URL).where(URL.short_code == short_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Short code already in use")

    url = URL(
        original_url=payload.original_url,
        short_code=short_code,
        owner_id=current_user.id if current_user else None,
        expires_at=payload.expires_at,
    )
    db.add(url)
    await db.commit()
    await db.refresh(url)

    # Cache
    redis = await get_redis()
    await redis.setex(f"url:{short_code}", CACHE_TTL, url.original_url)

    return _build_url_out(url, 0)


@router.get("/my-urls", response_model=list[URLOut])
async def list_my_urls(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(URL, func.count(Click.id).label("click_count"))
        .outerjoin(Click, Click.url_id == URL.id)
        .where(URL.owner_id == current_user.id)
        .group_by(URL.id)
        .order_by(URL.created_at.desc())
    )
    rows = result.all()
    return [_build_url_out(url, count) for url, count in rows]


@router.delete("/urls/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url: URL | None = result.scalar_one_or_none()
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    if url.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(url)
    await db.commit()

    redis = await get_redis()
    await redis.delete(f"url:{short_code}")
