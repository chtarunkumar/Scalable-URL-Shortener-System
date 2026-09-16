import datetime
from pydantic import BaseModel, HttpUrl, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── URL ───────────────────────────────────────────────────────────────────────

class URLCreate(BaseModel):
    original_url: str
    custom_code: str | None = None
    expires_at: datetime.datetime | None = None

    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class URLOut(BaseModel):
    id: int
    original_url: str
    short_code: str
    short_url: str
    is_active: bool
    created_at: datetime.datetime
    expires_at: datetime.datetime | None = None
    click_count: int = 0

    model_config = {"from_attributes": True}


# ── Analytics ─────────────────────────────────────────────────────────────────

class ClickOut(BaseModel):
    id: int
    clicked_at: datetime.datetime
    ip_address: str | None
    country: str | None
    referer: str | None

    model_config = {"from_attributes": True}


class AnalyticsOut(BaseModel):
    short_code: str
    original_url: str
    total_clicks: int
    recent_clicks: list[ClickOut]
