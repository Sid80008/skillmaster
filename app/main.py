"""
Main FastAPI application.

Entry-point for uvicorn:
    uvicorn app.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth, history, quests, recommendations
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.services.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
    SkillQuestError,
    ValidationError,
)

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("skillquest_startup", environment=get_settings().environment)
    yield
    log.info("skillquest_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Skill Quest API",
        description="Exploration-based skill recommendation backend.",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────
    @app.exception_handler(NotFoundError)
    async def _not_found(_req: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ForbiddenError)
    async def _forbidden(_req: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ConflictError)
    async def _conflict(_req: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(InvalidTransitionError)
    async def _invalid_transition(_req: Request, exc: InvalidTransitionError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ValidationError)
    async def _validation(_req: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )

    @app.exception_handler(SkillQuestError)
    async def _generic_domain(_req: Request, exc: SkillQuestError) -> JSONResponse:
        log.error("unhandled_domain_error", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred."},
        )

    from app.api.v1 import auth, history, quests, recommendations, profile, exploration, mix, lockin

    prefix = "/api/v1"
    app.include_router(auth.router, prefix=prefix)
    app.include_router(recommendations.router, prefix=prefix)
    app.include_router(quests.router, prefix=prefix)
    app.include_router(history.router, prefix=prefix)
    app.include_router(profile.router, prefix=prefix)
    app.include_router(exploration.router, prefix=prefix)
    app.include_router(mix.router, prefix=prefix)
    app.include_router(lockin.router, prefix=prefix)

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        from app.core.database import check_connection
        return {
            "status": "ok",
            "environment": settings.environment,
            "database": "connected" if check_connection() else "unavailable",
        }

    return app


app = create_app()
