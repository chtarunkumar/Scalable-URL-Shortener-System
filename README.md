# Scalable-URL-Shortener-System
A scalable URL shortening service built using FastAPI, PostgreSQL, Redis, and Docker with caching, rate limiting, JWT authentication, and analytics.

## Features
- Shorten URLs with auto-generated or custom short codes
- Optional link expiry
- JWT-based user authentication (register/login)
- Per-user URL management (list, delete)
- Click analytics (total clicks + recent click history with IP, user agent, referer)
- Redis caching for fast redirects
- Rate limiting on the shorten endpoint
- Dockerized with PostgreSQL and Redis services

## Tech Stack
- **API:** FastAPI, SQLAlchemy (async), Pydantic
- **Database:** PostgreSQL (via `asyncpg`)
- **Cache:** Redis
- **Auth:** JWT (`python-jose`), password hashing with `passlib[bcrypt]`
- **Rate limiting:** SlowAPI
- **Containerization:** Docker & Docker Compose

## Project Structure
```
app/
  main.py           # FastAPI app setup, routers, static UI
  config.py         # App settings (env-driven)
  database.py        # SQLAlchemy engine/session
  models.py          # ORM models (User, URL, Click)
  schemas.py          # Pydantic request/response schemas
  auth.py            # JWT auth helpers & dependencies
  cache.py           # Redis client
  utils.py           # Short code generation
  routers/
    auth.py           # /auth/register, /auth/login, /auth/me
    urls.py           # /shorten, /my-urls, /urls/{short_code}
    analytics.py       # /analytics/{short_code}
    redirect.py        # /{short_code} redirect (catch-all)
  static/index.html    # Simple web UI
```

## Getting Started (Docker)
```bash
git clone https://github.com/chtarunkumar/Scalable-URL-Shortener-System.git
cd Scalable-URL-Shortener-System
docker compose up --build
```
The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

## Environment Variables
Configured via `docker-compose.yml` or a local `.env` file:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@db:5432/urlshortener` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `SECRET_KEY` | JWT signing secret | *(change in production)* |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `60` |
| `BASE_URL` | Base URL used to build short links | `http://localhost:8000` |
| `SHORT_CODE_LENGTH` | Length of generated short codes | `7` |
| `RATE_LIMIT_PER_MINUTE` | Rate limit for `/shorten` | `30` |

## API Endpoints
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Log in and receive a JWT | No |
| POST | `/shorten` | Create a short URL | Optional |
| GET | `/my-urls` | List the current user's URLs | Yes |
| DELETE | `/urls/{short_code}` | Delete a URL | Yes |
| GET | `/analytics/{short_code}` | Get click analytics for a URL | Yes |
| GET | `/{short_code}` | Redirect to the original URL | No |
| GET | `/health` | Health check | No |

## Running Locally Without Docker
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Requires a running PostgreSQL and Redis instance, with connection details set via environment variables or a `.env` file.

