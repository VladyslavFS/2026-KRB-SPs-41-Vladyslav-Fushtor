from datetime import UTC, datetime

from fastapi import APIRouter, Cookie, Response, status

from api.auth.dependencies import CurrentUser
from api.auth.exceptions import (
    AccountDisabled,
    EmailAlreadyExists,
    InvalidCredentials,
    RefreshTokenExpired,
    RefreshTokenInvalid,
    RefreshTokenRevoked,
)
from api.auth.schemas import (
    JWTUser,
    LoginRequest,
    RegisterOut,
    RegisterRequest,
    TokenOut,
    UserOut,
)
from api.auth.service import (
    create_access_token,
    create_refresh_token_plain,
    hash_password,
    hash_refresh_token,
    refresh_expires_at,
    verify_password,
)
from api.dependencies import DBConnDep, SettingsDep

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


def _issue_tokens(user: UserOut, db, settings) -> tuple[TokenOut, str]:
    # 1) access
    access = create_access_token(
        user_id=user.user_id,
        email=user.email,
        is_active=user.is_active,
        secret=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )

    # 2) refresh (plain -> hash in DB)
    refresh_plain = create_refresh_token_plain(settings.jwt_refresh_token_bytes)
    refresh_hash = hash_refresh_token(refresh_plain)
    exp_at = refresh_expires_at(settings.jwt_refresh_token_expire_days)

    with db.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app.refresh_tokens (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user.user_id, refresh_hash, exp_at),
        )

    token_out = TokenOut(
        access_token=access,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        refresh_expires_in=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
    )
    return token_out, refresh_plain


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, settings):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,        # Set to True for max security, JS won't read it
        secure=True,
        samesite="lax",
        max_age=settings.jwt_access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,          # Ensures cookie is only sent over HTTPS
        samesite="lax",       # Protects against CSRF
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
    )


@router.post("/register", response_model=RegisterOut, status_code=201)
def register(
    body: RegisterRequest, 
    response: Response, 
    db: DBConnDep, 
    settings: SettingsDep
) -> RegisterOut:
    with db.cursor() as cur:
        cur.execute("SELECT 1 FROM app.users WHERE email = %s", (body.email,))
        if cur.fetchone():
            raise EmailAlreadyExists()

        cur.execute(
            """
            INSERT INTO app.users (email, password_hash)
            VALUES (%s, %s)
            RETURNING user_id, email, is_active, created_at, last_login
            """,
            (body.email, hash_password(body.password)),
        )
        row = cur.fetchone()

    user = UserOut(
        user_id=row[0],
        email=row[1],
        is_active=row[2],
        created_at=row[3],
        last_login=row[4],
    )
    token, refresh_plain = _issue_tokens(user, db, settings)
    _set_auth_cookies(response, token.access_token, refresh_plain, settings)
    
    return RegisterOut(user=user, token=token)


@router.post("/login", response_model=RegisterOut)
def login(
    body: LoginRequest, 
    response: Response, 
    db: DBConnDep, 
    settings: SettingsDep
) -> RegisterOut:
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT user_id, email, password_hash, is_active, created_at, last_login
            FROM app.users
            WHERE email = %s
            """,
            (body.email,),
        )
        row = cur.fetchone()

    # constant-time-ish verify
    pw_ok = verify_password(body.password, row[2]) if row else False
    if not row or not pw_ok:
        raise InvalidCredentials()

    if not row[3]:
        raise AccountDisabled()

    with db.cursor() as cur:
        cur.execute(
            "UPDATE app.users SET last_login = now() WHERE user_id = %s RETURNING last_login",
            (row[0],),
        )
        updated_login = cur.fetchone()[0]

    user = UserOut(
        user_id=row[0],
        email=row[1],
        is_active=row[3],
        created_at=row[4],
        last_login=updated_login,
    )

    token, refresh_plain = _issue_tokens(user, db, settings)
    _set_auth_cookies(response, token.access_token, refresh_plain, settings)
    
    return RegisterOut(user=user, token=token)


@router.post("/refresh", response_model=TokenOut)
def refresh(
    response: Response,
    db: DBConnDep, 
    settings: SettingsDep,
    refresh_token: str | None = Cookie(default=None)
) -> TokenOut:
    if not refresh_token:
        raise RefreshTokenInvalid()

    now = datetime.now(UTC)
    incoming_hash = hash_refresh_token(refresh_token)

    with db.cursor() as cur:
        cur.execute(
            """
            SELECT refresh_token_id, app.refresh_tokens.user_id, expires_at, revoked_at, app.users.email, app.users.is_active
            FROM app.refresh_tokens
            JOIN app.users ON app.users.user_id = app.refresh_tokens.user_id
            WHERE token_hash = %s
            """,  # noqa: E501
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

    # rotation: revoke old + issue new
    new_refresh_plain = create_refresh_token_plain(settings.jwt_refresh_token_bytes)
    new_refresh_hash = hash_refresh_token(new_refresh_plain)
    new_exp_at = refresh_expires_at(settings.jwt_refresh_token_expire_days)

    with db.cursor() as cur:
        cur.execute(
            """
            UPDATE app.refresh_tokens
            SET revoked_at = now(), replaced_by_hash = %s
            WHERE refresh_token_id = %s
            """,
            (new_refresh_hash, refresh_token_id),
        )
        cur.execute(
            """
            INSERT INTO app.refresh_tokens (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user_id, new_refresh_hash, new_exp_at),
        )

    access = create_access_token(
        user_id=user_id,
        email=email,
        is_active=is_active,
        secret=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )

    _set_auth_cookies(response, access, new_refresh_plain, settings)

    return TokenOut(
        access_token=access,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        refresh_expires_in=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: DBConnDep,
    refresh_token: str | None = Cookie(default=None)
):
    """
    Logout user by revoking their refresh token and clearing the cookie
    """
    if refresh_token:
        incoming_hash = hash_refresh_token(refresh_token)
        with db.cursor() as cur:
            cur.execute(
                """
                UPDATE app.refresh_tokens
                SET revoked_at = now()
                WHERE token_hash = %s AND revoked_at IS NULL
                """,
                (incoming_hash,),
            )
            
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return None


@router.get("/me", response_model=JWTUser)
def me(current_user: CurrentUser) -> JWTUser:
    """
    Get current user profile statelessly directly from the token payload.
    """
    return current_user
