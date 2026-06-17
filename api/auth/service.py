"""
Pure auth helpers — kept for backward compatibility.
New code should use PasswordService and TokenService directly.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from api.auth.password_service import PasswordService
from api.auth.token_service import TokenService

# ── Module-level singletons for legacy call sites ──────────────────────────────
_pwd = PasswordService()


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_access_token(
    user_id: int,
    email: str,
    is_active: bool,
    secret: str,
    algorithm: str,
    expires_minutes: int,
) -> str:
    """Legacy signature wrapper — use TokenService.create_access_token() in new code."""
    from api.config import Settings
    # Build a minimal settings-compatible object for TokenService
    class _MinSettings:
        jwt_secret_key = secret
        jwt_algorithm = algorithm
        jwt_access_token_expire_minutes = expires_minutes
        jwt_refresh_token_bytes = 32
        jwt_refresh_token_expire_days = 30

    return TokenService(_MinSettings()).create_access_token(user_id, email, is_active)  # type: ignore[arg-type]


def decode_access_token(token: str, secret: str, algorithm: str) -> dict:
    """Legacy signature wrapper — use TokenService.decode_access_token() in new code."""
    class _MinSettings:
        jwt_secret_key = secret
        jwt_algorithm = algorithm
        jwt_access_token_expire_minutes = 15
        jwt_refresh_token_bytes = 32
        jwt_refresh_token_expire_days = 30

    return TokenService(_MinSettings()).decode_access_token(token)  # type: ignore[arg-type]


def create_refresh_token_plain(nbytes: int) -> str:
    import secrets
    return secrets.token_urlsafe(nbytes)


def hash_refresh_token(token_plain: str) -> str:
    import hashlib
    return hashlib.sha256(token_plain.encode("utf-8")).hexdigest()


def refresh_expires_at(days: int) -> datetime:
    return datetime.now(UTC) + timedelta(days=days)
