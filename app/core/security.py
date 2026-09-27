"""
Security utilities: password hashing and JWT token management.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt
import bcrypt

from app.core.config import get_settings




# ── Passwords ─────────────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Parameters
    ----------
    subject:
        Usually the user's UUID as a string.
    extra_claims:
        Optional additional JWT claims (e.g. ``{"role": "admin"}``).
    expires_delta:
        Custom expiry.  If omitted, ``ACCESS_TOKEN_EXPIRE_MINUTES`` is used.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify *token*, raising ``JWTError`` on failure."""
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
