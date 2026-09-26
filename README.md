# Skill Quest Backend

## Stack
- **Python 3.12+**
- **FastAPI** – HTTP API framework
- **SQLAlchemy 2.0** – ORM (sync, using `Session`)
- **Alembic** – database migrations
- **PostgreSQL** – primary database
- **passlib + python-jose** – authentication (bcrypt + JWT)
- **structlog** – structured logging
- **pytest** – test suite

## Project Layout

```
skillmaster/
├── app/
│   ├── core/           # config, db, logging, security
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic request/response schemas
│   ├── api/            # FastAPI routers
│   │   └── v1/
│   ├── services/       # business logic layer
│   └── main.py         # application entry-point
├── alembic/            # migration scripts
├── tests/              # pytest test suite
├── pyproject.toml
└── .env.example
```

## Quick start

```bash
# 1. install dependencies
pip install -e ".[dev]"

# 2. copy and configure environment
cp .env.example .env
# edit .env – set DATABASE_URL and SECRET_KEY

# 3. run migrations
alembic upgrade head

# 4. start the dev server
uvicorn app.main:app --reload

# 5. run tests (requires a test database)
pytest
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | yes | PostgreSQL DSN, e.g. `postgresql://user:pass@localhost/skillquest` |
| `TEST_DATABASE_URL` | yes (tests) | Separate test database DSN |
| `SECRET_KEY` | yes | JWT signing secret (min 32 chars) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | Default 60 |
| `ALGORITHM` | no | JWT algorithm, default `HS256` |
| `LOG_LEVEL` | no | `debug`/`info`/`warning`, default `info` |
| `ENVIRONMENT` | no | `development`/`production`, default `development` |
