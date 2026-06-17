"""
TokenService — encapsulates all JWT and token operations.

Pattern: Service Object (single responsibility — tokens only).
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from api.config import Settings


class TokenService:
    """
    Creates, decodes, and hashes JWT access tokens and opaque refresh tokens.
    All token settings (secret, algorithm, expiry) are injected via Settings.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # ── Access tokens ──────────────────────────────────────────────────────────

    def create_access_token(self, user_id: int, email: str, is_active: bool) -> str:
        """Creates a signed JWT access token."""
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=self._settings.jwt_access_token_expire_minutes)
        payload = {
            "sub": str(user_id),
            "email": email,
            "is_active": is_active,
            "type": "access",
            "iss": "pp_earthquake",
            "iat": int(now.timestamp()),
            "jti": secrets.token_hex(16),
            "exp": expire,
        }
        return jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )

    def decode_access_token(self, token: str) -> dict:
        """Decodes and validates a JWT. Raises JWTError on failure."""
        payload = jwt.decode(
            token,
            self._settings.jwt_secret_key,
            algorithms=[self._settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise JWTError("Invalid token type")
        if payload.get("sub") is None:
            raise JWTError("Missing sub claim")
        return payload

    # ── Refresh tokens ─────────────────────────────────────────────────────────

    def create_refresh_token(self) -> tuple[str, str]:
        """
        Generates a cryptographically secure refresh token.
        Returns (plain_token, sha256_hash) — store the hash, send the plain.
        """
        plain = secrets.token_urlsafe(self._settings.jwt_refresh_token_bytes)
        hashed = self._hash(plain)
        return plain, hashed

    def hash_token(self, plain: str) -> str:
        """SHA-256 hash of an opaque token string."""
        return self._hash(plain)

    def refresh_expires_at(self) -> datetime:
        """Returns the UTC expiry datetime for a new refresh token."""
        return datetime.now(UTC) + timedelta(days=self._settings.jwt_refresh_token_expire_days)

    # ── Reset tokens ───────────────────────────────────────────────────────────

    def create_reset_token(self) -> tuple[str, str]:
        """
        Generates a password reset token.
        Returns (plain_token, sha256_hash).
        """
        plain = secrets.token_urlsafe(32)
        return plain, self._hash(plain)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
