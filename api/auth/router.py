"""
Auth router — pure HTTP layer. All business logic delegated to AuthService.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status

from api.auth.auth_service import AuthService
from api.auth.dependencies import CurrentUser
from api.auth.password_service import PasswordService
from api.auth.schemas import (
    ForgotPasswordRequest,
    JWTUser,
    LoginRequest,
    RegisterOut,
    RegisterRequest,
    ResetPasswordRequest,
    TokenOut,
    UserOut,
)
from api.auth.token_service import TokenService
from api.dependencies import DBConnDep, SettingsDep

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# ── Dependency factory ─────────────────────────────────────────────────────────

def get_auth_service(db: DBConnDep, settings: SettingsDep) -> AuthService:
    """FastAPI DI: creates AuthService per request."""
    return AuthService(
        db=db,
        token_svc=TokenService(settings),
        pwd_svc=PasswordService(),
        settings=settings,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


# ── Cookie helper (HTTP concern — stays in router) ─────────────────────────────

def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, settings) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.jwt_access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterOut,
    status_code=201,
    summary="Register a new user",
    responses={
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
def register(
    body: RegisterRequest,
    response: Response,
    auth_svc: AuthServiceDep,
    settings: SettingsDep,
) -> RegisterOut:
    user, token, refresh_plain = auth_svc.register(body.email, body.password)
    _set_auth_cookies(response, token.access_token, refresh_plain, settings)
    return RegisterOut(user=user, token=token)


@router.post(
    "/login",
    response_model=RegisterOut,
    summary="Login with email and password",
    responses={
        401: {"description": "Invalid credentials"},
        403: {"description": "Account disabled"},
    },
)
def login(
    body: LoginRequest,
    response: Response,
    auth_svc: AuthServiceDep,
    settings: SettingsDep,
) -> RegisterOut:
    user, token, refresh_plain = auth_svc.login(body.email, body.password)
    _set_auth_cookies(response, token.access_token, refresh_plain, settings)
    return RegisterOut(user=user, token=token)


@router.post(
    "/refresh",
    response_model=TokenOut,
    summary="Refresh access token using cookie",
    responses={401: {"description": "Invalid, expired, or revoked refresh token"}},
)
def refresh(
    response: Response,
    auth_svc: AuthServiceDep,
    settings: SettingsDep,
    refresh_token: str | None = Cookie(default=None),
) -> TokenOut:
    from api.auth.exceptions import RefreshTokenInvalid
    if not refresh_token:
        raise RefreshTokenInvalid()
    token_out, new_refresh_plain = auth_svc.refresh_token(refresh_token)
    _set_auth_cookies(response, token_out.access_token, new_refresh_plain, settings)
    return token_out


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke refresh token",
)
def logout(
    response: Response,
    auth_svc: AuthServiceDep,
    refresh_token: str | None = Cookie(default=None),
):
    auth_svc.logout(refresh_token)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return None


@router.get(
    "/me",
    response_model=JWTUser,
    summary="Get current user from token",
    responses={401: {"description": "Missing or invalid access token"}},
)
def me(current_user: CurrentUser) -> JWTUser:
    """Get current user profile statelessly from the token payload."""
    return current_user


@router.post("/forgot-password", summary="Request password reset")
def forgot_password(
    body: ForgotPasswordRequest,
    auth_svc: AuthServiceDep,
    settings: SettingsDep,
) -> dict:
    reset_plain = auth_svc.forgot_password(body.email, settings.app_env)
    response: dict = {"message": "If the email exists, a password reset link has been sent."}
    if reset_plain:
        response["reset_token_dev"] = reset_plain
    return response


@router.post("/reset-password", summary="Reset password with token")
def reset_password(body: ResetPasswordRequest, auth_svc: AuthServiceDep) -> dict:
    auth_svc.reset_password(body.token, body.new_password)
    return {"message": "Password has been reset successfully."}
