# CLAUDE.md - Content Clipper

## Project Overview

Content Clipper is an AI-powered video/audio clipping and social media scheduling platform. It is a full-stack monorepo with a **FastAPI** (Python) backend and a **React** (Vite) frontend, containerized with Docker Compose.

Production domain: `machine-systems.org`

## Repository Structure

```
content-clipper/
├── backend/              # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/       # Versioned API endpoints
│   │   │   └── endpoints/ # One file per resource (auth, media, clips, oauth, etc.)
│   │   ├── core/         # Config, database, auth, security, crypto, storage
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic (oauth, social platform clients)
│   │   ├── tasks/        # Celery async tasks (clip, media, social processing)
│   │   ├── utils/        # AI, video, file utilities
│   │   └── main.py       # FastAPI app entry point
│   ├── tests/            # pytest test suite
│   ├── alembic/          # Database migrations
│   └── requirements.txt  # Python dependencies
├── frontend/             # React + Vite frontend
│   ├── src/
│   │   ├── components/   # Reusable components (Layout/, Common/, Accounts/, etc.)
│   │   ├── pages/        # Page-level components
│   │   ├── services/     # Axios API client modules
│   │   ├── store/        # Zustand global state (store/index.js)
│   │   ├── hooks/        # Custom React hooks
│   │   └── utils/        # Utility functions
│   └── package.json
├── docker/               # Nginx, Postgres init scripts, helper scripts
├── docs/                 # Instagram integration docs, Meta app review docs
├── scripts/              # Utility scripts (Fernet key gen, OAuth config check)
├── docker-compose.yml    # Development environment (9 services)
├── docker-compose.prod.yml
└── .github/workflows/    # CI/CD pipeline
```

## Tech Stack

### Backend
- **Framework**: FastAPI 0.104 with Uvicorn
- **Database**: PostgreSQL 15 via SQLAlchemy 2.0 + Alembic migrations
- **Task Queue**: Celery 5.3 with Redis 7 as broker
- **Object Storage**: MinIO (S3-compatible)
- **AI**: OpenAI API
- **Video Processing**: FFmpeg via ffmpeg-python
- **Auth**: JWT (python-jose) + bcrypt password hashing + Fernet token encryption
- **Python version**: 3.11

### Frontend
- **Framework**: React 18.2 with Vite 5
- **Routing**: React Router DOM 6
- **State**: Zustand 4.4
- **HTTP**: Axios
- **Styling**: Tailwind CSS 3.3
- **Icons**: Lucide React
- **Language**: JavaScript (.jsx), no TypeScript

### Infrastructure
- Docker Compose with 9 services: postgres, redis, minio, pgadmin, backend, celery-worker, celery-beat, flower, frontend
- CI/CD: GitHub Actions (test -> build -> deploy via SSH)

## Common Commands

### Docker (full stack)
```bash
docker compose up -d              # Start all services
docker compose down               # Stop all services
docker compose logs -f backend    # Follow backend logs
docker compose exec backend bash  # Shell into backend container
```

### Backend
```bash
cd backend
pip install -r requirements.txt                    # Install dependencies
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  # Run dev server

# Database migrations
alembic upgrade head              # Apply all migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Testing
pytest tests/ -v                  # Run all tests
pytest tests/ -v --cov=app        # Run with coverage

# Code quality
black app/                        # Format code
ruff app/                         # Lint (fast)
isort app/                        # Sort imports
mypy app/                         # Type check
pylint app/                       # Static analysis
bandit -r app/                    # Security scan
flake8 app --select=E9,F63,F7,F82  # CI lint check
```

### Frontend
```bash
cd frontend
npm install                       # Install dependencies
npm run dev                       # Start Vite dev server (port 3000)
npm run build                     # Production build
npm run lint                      # ESLint check
npm run format                    # Prettier format
```

## Architecture Patterns

### Backend
- **Service layer**: Business logic lives in `app/services/`, not in endpoints. Endpoints in `app/api/v1/endpoints/` handle HTTP concerns and delegate to services.
- **Dependency injection**: FastAPI `Depends()` for DB sessions (`get_db`) and auth (`get_current_user`).
- **Async throughout**: All endpoints are `async def`. Background work goes through Celery tasks.
- **API versioning**: All routes under `/api/v1/` prefix.
- **Configuration**: Single `Settings` class in `app/core/config.py` using Pydantic Settings, loaded from `.env`.
- **Token encryption**: OAuth tokens are Fernet-encrypted before database storage (`app/core/crypto.py`).

### Frontend
- **Feature-based organization**: Components grouped by feature (YouTube/, TikTok/, Calendar/, etc.) under `src/components/`.
- **Page components**: One file per route in `src/pages/`.
- **Service layer**: One service file per API domain in `src/services/`, all using a shared Axios instance (`api.js`) with interceptors for auth tokens.
- **Global state**: Single Zustand store at `src/store/index.js` managing auth, accounts, media, clips, schedules, and posts.
- **Protected routes**: `ProtectedRoute` component wraps authenticated routes.

### Database Models
Core tables: `users`, `accounts` (OAuth connections), `media`, `clips`, `social_posts`, `content_schedules`, `scheduled_posts`. All models in `app/models/` with relationship cascading.

## API Routes

All routes prefixed with `/api/v1/`:

| Prefix | Module | Purpose |
|--------|--------|---------|
| `/health` | health | Health checks |
| `/auth` | auth | Login, register, JWT tokens |
| `/users` | users | User profile management |
| `/accounts` | accounts | Connected social accounts CRUD |
| `/oauth` | oauth | OAuth callbacks for all platforms |
| `/media` | media | File upload and management |
| `/clips` | clips | Clip creation and editing |
| `/schedules` | schedules | Content scheduling |
| `/social` | social | Cross-platform social posting |
| `/instagram` | instagram | Instagram Graph API operations |
| `/youtube` | youtube | YouTube Data API operations |
| `/tiktok` | tiktok | TikTok Content Posting API |

Interactive API docs available at `/api/docs` (Swagger) and `/api/redoc`.

## Code Style & Conventions

### Python (Backend)
- **Formatter**: black (line length default 88)
- **Linter**: ruff, pylint, flake8
- **Import sorting**: isort
- **Type checking**: mypy
- **Naming**: PascalCase for classes/models/enums, snake_case for functions/variables/table names
- **Type hints**: Used on all function signatures

### JavaScript (Frontend)
- **Linter**: ESLint with react, react-hooks, react-refresh plugins
- **Formatter**: Prettier (no semicolons, single quotes, 2-space indent, 100 char width, trailing commas in ES5, no parens on single-arg arrows)
- **Components**: Functional components with hooks, `.jsx` extension
- **Naming**: PascalCase for components, camelCase for functions/variables
- **Prop validation**: prop-types disabled (no PropTypes used)
- **Styling**: Tailwind CSS utility classes inline, no separate CSS modules

## Environment Variables

Copy `.env.example` to `.env` and fill in values. Key groups:

- **Core**: `ENVIRONMENT`, `DEBUG`, `SECRET_KEY`, `FERNET_KEY`
- **Database**: `DATABASE_URL`, `POSTGRES_*`
- **Redis**: `REDIS_URL`
- **MinIO**: `MINIO_ENDPOINT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`
- **AI**: `OPENAI_API_KEY`
- **OAuth**: `INSTAGRAM_CLIENT_ID/SECRET`, `YOUTUBE_CLIENT_ID/SECRET`, `TIKTOK_CLIENT_KEY/SECRET`, `LINKEDIN_CLIENT_ID/SECRET`, `TWITTER_*`
- **Frontend**: `VITE_API_URL`

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci-cd.yml`):

1. **test**: Lint with flake8, run pytest (triggers on push to main/develop, PRs to main)
2. **build**: Build Docker images (main branch only)
3. **deploy**: SSH into server, pull, rebuild, restart containers (main branch only)

## Testing

- Framework: pytest with pytest-asyncio, pytest-mock, pytest-cov
- Test location: `backend/tests/`
- Existing test coverage focuses on Instagram publishing (images, carousels, reels, stories)
- Run: `pytest tests/ -v` from the `backend/` directory

## Key Files to Know

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app creation, middleware, router inclusion |
| `backend/app/core/config.py` | All settings via Pydantic Settings |
| `backend/app/core/database.py` | SQLAlchemy engine and session factory |
| `backend/app/core/auth.py` | JWT token validation, `get_current_user` dependency |
| `backend/app/core/security.py` | Password hashing, token creation |
| `backend/app/core/crypto.py` | Fernet encrypt/decrypt for OAuth tokens |
| `backend/app/core/storage.py` | MinIO client wrapper |
| `backend/app/api/v1/__init__.py` | Router aggregation for all endpoints |
| `frontend/src/App.jsx` | Route definitions and app structure |
| `frontend/src/store/index.js` | Zustand global state store |
| `frontend/src/services/api.js` | Axios instance with auth interceptors |
| `docker-compose.yml` | Full development environment |

## Social Platform Integrations

Each platform has a dedicated service, endpoint module, and frontend page:

- **Instagram**: Graph API for photos, videos, carousels, reels, stories, insights
- **YouTube**: Data API v3 for uploads, thumbnails, community posts, analytics
- **TikTok**: Content Posting API for videos, photos, stories
- **LinkedIn/Twitter**: OAuth connection, posting via social service
