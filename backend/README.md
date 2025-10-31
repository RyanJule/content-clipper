# Content Clipper Backend

FastAPI backend for the Content Clipper application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the server:
```bash
uvicorn app.main:app --reload
```

## Docker

Build and run with Docker:
```bash
docker-compose up -d backend
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Testing

Run tests:
```bash
pytest tests/ -v
```

## Project Structure
```
backend/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Core configuration
│   ├── models/        # Database models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   ├── tasks/         # Celery tasks
│   └── utils/         # Utility functions
├── tests/             # Test suite
├── alembic/           # Database migrations
└── requirements.txt   # Dependencies
```