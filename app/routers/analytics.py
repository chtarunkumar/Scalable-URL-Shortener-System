from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import URL, Click, User
from app.schemas import AnalyticsOut, ClickOut
from app.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/{short_code}", response_model=AnalyticsOut)
async def get_analytics(
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

    # Total clicks
    count_result = await db.execute(
        select(func.count(Click.id)).where(Click.url_id == url.id)
    )
    total_clicks = count_result.scalar_one()

    # Recent 20 clicks
    clicks_result = await db.execute(
        select(Click)
        .where(Click.url_id == url.id)
        .order_by(Click.clicked_at.desc())
        .limit(20)
    )
    recent_clicks = [ClickOut.model_validate(c) for c in clicks_result.scalars().all()]

    return AnalyticsOut(
        short_code=short_code,
        original_url=url.original_url,
        total_clicks=total_clicks,
        recent_clicks=recent_clicks,
    )
