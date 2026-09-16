from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import engine, Base
from app.cache import close_redis
from app.routers import auth, urls, redirect, analytics

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="URL Shortener",
    description="Scalable URL shortening service with JWT auth, Redis caching, and analytics.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown():
    await close_redis()
    await engine.dispose()


# Static files (UI)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
async def serve_ui():
    return FileResponse("app/static/index.html")


# Routers
app.include_router(auth.router)
app.include_router(urls.router)
app.include_router(analytics.router)
app.include_router(redirect.router)  # must be last (catch-all /{short_code})


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
