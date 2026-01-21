# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Digadoin Backend API - A FastAPI-based microservice backend for the WaaS platform.

## Tech Stack

- **FastAPI 0.109.0** with Python 3.10
- **PostgreSQL 15** (via docker-compose)
- **SQLAlchemy 2.0.23** ORM
- **JWT authentication** (python-jose, passlib)
- **Docker** with docker-compose

## Architecture

The codebase follows a modular architecture where each developer owns a separate module:

```
app/
├── main.py              # FastAPI app with CORS & router registration
├── dependencies.py      # Dependency injection (get_db)
├── core/
│   ├── config.py       # Pydantic Settings for environment configuration
│   └── database.py     # SQLAlchemy engine & session factory
└── modules/
    ├── auth/           # Authentication module
    ├── transactions/   # Transaction handling module
    └── service_delivery/  # Service delivery module
```

Each module follows this pattern:
- `models.py` - SQLAlchemy models
- `router.py` - FastAPI router with endpoints
- `services.py` - Business logic layer

When adding a new module, register its router in `app/main.py` with appropriate prefix and tags. All routes are prefixed with `/api/v1/`.

## Commands

### Development
```bash
# Run with hot-reload (after activating venv)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or use Docker Compose
docker-compose up --build
```

### Database
Tables are auto-created via `Base.metadata.create_all()` on startup. For production, use Alembic (already in requirements.txt):
```bash
alembic init alembic
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Testing
```bash
pytest
```

## Configuration

### Environment Variables (.env)
| Variable | Purpose |
|----------|---------|
| `DB_USER`, `DB_PASSWORD` | PostgreSQL credentials |
| `DB_SERVER`, `DB_PORT` | Database connection (default: `db:5432`) |
| `DB_NAME` | Database name |
| `SECRET_KEY` | JWT signing (generate with `openssl rand -hex 32` for production) |

### CORS Origins
- Development: `http://localhost:3000` (Next.js frontend)
- Production: `https://waas-frontend.vercel.app`

## Database

Database session is injected via dependency:
```python
from app.dependencies import get_db

def endpoint(db: Session = Depends(get_db)):
    ...
```
