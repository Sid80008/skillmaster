"""
Test fixtures and database setup.

Uses an in-memory SQLite database for speed and isolation.

Isolation strategy
------------------
* The engine and tables are created once for the whole session.
* Each TEST gets a brand-new Session + explicit transaction.
* After the test the transaction is rolled back so no data leaks between tests.
* Builder helpers generate unique emails/slugs using uuid4() to avoid
  UNIQUE constraint failures across tests.
"""
from __future__ import annotations

import uuid
from collections.abc import Generator
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# Import all models to register them with Base.metadata
import app.models  # noqa: F401
from app.core.database import Base
from app.models.catalog import (
    ActivityFamily,
    Category,
    Skill,
)
from app.models.quest import Quest, QuestAttempt, QuestAttemptStatus
from app.models.recommendation import (
    NoveltyCategory,
    Recommendation,
    RecommendationCandidate,
    RecommendationStatus,
)
from app.models.user import User

# ── Engine ────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def engine():
    """Single SQLite engine for the whole test session."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @event.listens_for(eng, "connect")
    def _fk_pragma(dbapi_con, _con_record):
        dbapi_con.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture(scope="session")
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db(session_factory) -> Generator[Session, None, None]:
    """
    Each test gets a Session with a transaction that is rolled back at teardown.

    We must NOT call db.commit() inside service code during tests — but because
    the services DO call db.commit(), we instead re-create the session from
    scratch per test and rely on SQLite table truncation being fast.

    Simpler approach: use a separate connection + SAVEPOINT per test.
    Since SQLAlchemy's db.commit() flushes the current SAVEPOINT but does not
    close the outer transaction when using begin_nested(), this gives isolation.
    """
    connection = session_factory.kw['bind'].connect()
    trans = connection.begin()
    session = Session(bind=connection)
    session.begin_nested()

    yield session

    session.close()
    trans.rollback()
    connection.close()


# ── Builder helpers – all use unique IDs to avoid UNIQUE constraint collisions ──


def _uid() -> str:
    """Short unique suffix."""
    return uuid.uuid4().hex[:8]


def make_user(
    db: Session,
    *,
    email: str | None = None,
    username: str | None = None,
    password_hash: str = "hashed",
) -> User:
    uid = _uid()
    user = User(
        email=email or f"user-{uid}@example.com",
        username=username or f"user-{uid}",
        hashed_password=password_hash,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def make_category(db: Session, *, slug: str | None = None) -> Category:
    slug = slug or f"cat-{_uid()}"
    cat = Category(slug=slug, name=slug.replace("-", " ").title())
    db.add(cat)
    db.flush()
    return cat


def make_family(
    db: Session,
    *,
    category: Category,
    slug: str | None = None,
) -> ActivityFamily:
    slug = slug or f"fam-{_uid()}"
    fam = ActivityFamily(
        category_id=category.id,
        slug=slug,
        name=slug.replace("-", " ").title(),
    )
    db.add(fam)
    db.flush()
    return fam


def make_skill(
    db: Session,
    *,
    family: ActivityFamily,
    slug: str | None = None,
    is_active: bool = True,
    catalog_version: int = 1,
    duration: int = 60,
    difficulty: int = 5,
    physical_tags: str | None = None,
    equipment_tags: str | None = None,
    **kwargs,
) -> Skill:
    slug = slug or f"skill-{_uid()}"
    skill = Skill(
        activity_family_id=family.id,
        slug=slug,
        name=slug.replace("-", " ").title(),
        is_active=is_active,
        catalog_version=catalog_version,
        estimated_duration_minutes=duration,
        difficulty_level=difficulty,
        physical_restriction_tags=physical_tags,
        required_equipment_tags=equipment_tags,
        **kwargs
    )
    db.add(skill)
    db.flush()
    return skill


def make_quest(db: Session, *, skill: Skill) -> Quest:
    quest = Quest(
        skill_id=skill.id,
        title=f"Quest: {skill.name}",
        catalog_version=skill.catalog_version,
    )
    db.add(quest)
    db.flush()
    return quest


def make_attempt(
    db: Session,
    *,
    user: User,
    skill: Skill,
    quest: Quest,
    status: str = QuestAttemptStatus.PENDING.value,
) -> QuestAttempt:
    attempt = QuestAttempt(
        user_id=user.id,
        quest_id=quest.id,
        skill_id=skill.id,
        skill_catalog_version=skill.catalog_version,
        activity_family_id=skill.activity_family_id,
        status=status,
    )
    db.add(attempt)
    db.flush()
    return attempt


def make_recommendation(
    db: Session,
    *,
    user: User,
    status: str = RecommendationStatus.PENDING.value,
) -> Recommendation:
    rec = Recommendation(user_id=user.id, status=status)
    db.add(rec)
    db.flush()
    return rec


def make_candidate(
    db: Session,
    *,
    recommendation: Recommendation,
    skill: Skill,
    rank: int = 1,
    score: Decimal = Decimal("0.8500"),
    novelty_category: str = NoveltyCategory.UNEXPLORED_TERRITORY.value,
) -> RecommendationCandidate:
    candidate = RecommendationCandidate(
        recommendation_id=recommendation.id,
        skill_id=skill.id,
        skill_catalog_version=skill.catalog_version,
        rank=rank,
        score=score,
        novelty_category=novelty_category,
    )
    db.add(candidate)
    db.flush()
    return candidate

