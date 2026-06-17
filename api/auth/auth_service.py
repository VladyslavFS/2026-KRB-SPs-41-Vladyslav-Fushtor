"""
AuthService — Facade pattern over PasswordService + TokenService + DB.

Concentrates all auth business logic (registration, login, token rotation,
password reset). The router becomes a pure HTTP translation layer.

Pattern: Facade — simple interface over a complex subsystem.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from psycopg2.extensions import connection

from api.auth.exceptions import (
    AccountDisabled,
    EmailAlreadyExists,
    InvalidCredentials,
    InvalidOrExpiredResetToken,
    RefreshTokenExpired,
    RefreshTokenInvalid,
    RefreshTokenRevoked,
)
from api.auth.password_service import PasswordService
from api.auth.schemas import TokenOut, UserOut
from api.auth.token_service import TokenService
from api.config import Settings


class AuthService:
    """
    Facade for all authentication operations.
    Instantiated per-request via FastAPI DI.
    """

    def __init__(
        self,
        db: connection,
        token_svc: TokenService,
        pwd_svc: PasswordService,
        settings: Settings,
    ) -> None:
        self._db = db
        self._token = token_svc
        self._pwd = pwd_svc
        self._settings = settings

    # ── Public API ─────────────────────────────────────────────────────────────

    def register(self, email: str, password: str) -> tuple[UserOut, TokenOut, str]:
        """
        Creates a new user account and issues tokens.
        Returns (user, token_out, refresh_plain_for_cookie).
        Raises EmailAlreadyExists if e-mail is taken.
        """
        with self._db.cursor() as cur:
            cur.execute("SELECT 1 FROM app.users WHERE email = %s", (email,))
            if cur.fetchone():
                raise EmailAlreadyExists()

            cur.execute(
                """
                INSERT INTO app.users (email, password_hash)
                VALUES (%s, %s)
                RETURNING user_id, email, is_active, created_at, last_login
                """,
                (email, self._pwd.hash(password)),
            )
            row = cur.fetchone()

        user = UserOut(
            user_id=row[0], email=row[1], is_active=row[2],
            created_at=row[3], last_login=row[4],
        )
        token_out, refresh_plain = self._issue_tokens(user)
        return user, token_out, refresh_plain

    def login(self, email: str, password: str) -> tuple[UserOut, TokenOut, str]:
        """
        Authenticates user credentials and issues tokens.
        Returns (user, token_out, refresh_plain_for_cookie).
        Raises InvalidCredentials or AccountDisabled on failure.
        """
        with self._db.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, email, password_hash, is_active, created_at, last_login
                FROM app.users WHERE email = %s
                """,
                (email,),
            )
            row = cur.fetchone()

        pw_ok = self._pwd.verify(password, row[2]) if row else False
        if not row or not pw_ok:
            raise InvalidCredentials()
        if not row[3]:
            raise AccountDisabled()

        with self._db.cursor() as cur:
            cur.execute(
                "UPDATE app.users SET last_login = now() WHERE user_id = %s RETURNING last_login",
                (row[0],),
            )
            updated_login = cur.fetchone()[0]

        user = UserOut(
            user_id=row[0], email=row[1], is_active=row[3],
            created_at=row[4], last_login=updated_login,
        )
        token_out, refresh_plain = self._issue_tokens(user)
        return user, token_out, refresh_plain

    def refresh_token(self, refresh_plain: str) -> tuple[TokenOut, str]:
        """
        Validates and rotates a refresh token.
        Returns (new_token_out, new_refresh_plain_for_cookie).
        """
        now = datetime.now(UTC)
        incoming_hash = self._token.hash_token(refresh_plain)

        with self._db.cursor() as cur:
            cur.execute(
                """
                SELECT refresh_token_id, rt.user_id, expires_at, revoked_at,
                       u.email, u.is_active
                FROM app.refresh_tokens rt
                JOIN app.users u ON u.user_id = rt.user_id
                WHERE token_hash = %s
                """,
                (incoming_hash,),
            )
            row = cur.fetchone()

        if not row:
            raise RefreshTokenInvalid()

        refresh_token_id, user_id, expires_at, revoked_at, email, is_active = row

        if revoked_at is not None:
            raise RefreshTokenRevoked()
        if expires_at <= now:
            raise RefreshTokenExpired()
        if not is_active:
            raise AccountDisabled()

        # Token rotation
        new_plain, new_hash = self._token.create_refresh_token()
        new_exp_at = self._token.refresh_expires_at()

        with self._db.cursor() as cur:
            cur.execute(
                """
                UPDATE app.refresh_tokens
                SET revoked_at = now(), replaced_by_hash = %s
                WHERE refresh_token_id = %s
                """,
                (new_hash, refresh_token_id),
            )
            cur.execute(
                "INSERT INTO app.refresh_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
                (user_id, new_hash, new_exp_at),
            )

        access = self._token.create_access_token(user_id, email, is_active)
        token_out = TokenOut(
            access_token=access,
            expires_in=self._settings.jwt_access_token_expire_minutes * 60,
            refresh_expires_in=self._settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        )
        return token_out, new_plain

    def logout(self, refresh_plain: str | None) -> None:
        """Revokes the refresh token if present."""
        if not refresh_plain:
            return
        incoming_hash = self._token.hash_token(refresh_plain)
        with self._db.cursor() as cur:
            cur.execute(
                "UPDATE app.refresh_tokens SET revoked_at = now() WHERE token_hash = %s AND revoked_at IS NULL",
                (incoming_hash,),
            )

    def forgot_password(self, email: str, app_env: str) -> str | None:
        """
        Generates a reset token and saves its hash to the DB.
        Returns reset_plain only in dev/test environments (for e-mail simulation).
        """
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT user_id FROM app.users WHERE email = %s AND is_active = true",
                (email,),
            )
            row = cur.fetchone()

        if not row:
            return None

        user_id = row[0]
        reset_plain, reset_hash = self._token.create_reset_token()
        exp_at = datetime.now(UTC) + timedelta(hours=1)

        with self._db.cursor() as cur:
            cur.execute(
                """
                UPDATE app.users
                SET password_reset_token = %s, password_reset_expires_at = %s
                WHERE user_id = %s
                """,
                (reset_hash, exp_at, user_id),
            )

        print(f"PASSWORD RESET LINK: http://localhost:3001/reset-password?token={reset_plain}")
        return reset_plain if app_env in ("dev", "test") else None

    def reset_password(self, token_plain: str, new_password: str) -> None:
        """Resets the user's password using a valid reset token."""
        token_hash = self._token.hash_token(token_plain)
        now = datetime.now(UTC)

        with self._db.cursor() as cur:
            cur.execute(
                """
                SELECT user_id FROM app.users
                WHERE password_reset_token = %s
                  AND password_reset_expires_at > %s
                  AND is_active = true
                """,
                (token_hash, now),
            )
            row = cur.fetchone()

        if not row:
            raise InvalidOrExpiredResetToken()

        with self._db.cursor() as cur:
            cur.execute(
                """
                UPDATE app.users
                SET password_hash = %s,
                    password_reset_token = NULL,
                    password_reset_expires_at = NULL
                WHERE user_id = %s
                """,
                (self._pwd.hash(new_password), row[0]),
            )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _issue_tokens(self, user: UserOut) -> tuple[TokenOut, str]:
        """Creates access + refresh tokens, persists refresh hash to DB."""
        access = self._token.create_access_token(user.user_id, str(user.email), user.is_active)
        refresh_plain, refresh_hash = self._token.create_refresh_token()
        exp_at = self._token.refresh_expires_at()

        with self._db.cursor() as cur:
            cur.execute(
                "INSERT INTO app.refresh_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
                (user.user_id, refresh_hash, exp_at),
            )

        return (
            TokenOut(
                access_token=access,
                expires_in=self._settings.jwt_access_token_expire_minutes * 60,
                refresh_expires_in=self._settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
            ),
            refresh_plain,
        )
