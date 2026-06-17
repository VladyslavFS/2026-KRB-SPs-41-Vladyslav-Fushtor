"""
Auth-specific FastAPI dependencies.
Uses TokenService instead of bare functions.
"""
from typing import Annotated

from fastapi import Depends, Request
from jose import ExpiredSignatureError, JWTError

from api.auth.exceptions import AccountDisabled, InvalidToken, TokenExpired
from api.auth.schemas import JWTUser
from api.auth.token_service import TokenService
from api.dependencies import SettingsDep


def _extract_access_token(request: Request) -> str:
    """
    Extracts access token from Authorization header,
    falling back to an 'access_token' cookie if present.
    """
    from fastapi import HTTPException, status

    header = request.headers.get("authorization")
    if header and header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing access token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    request: Request,
    settings: SettingsDep,
) -> JWTUser:
    token = _extract_access_token(request)
    token_svc = TokenService(settings)

    try:
        payload = token_svc.decode_access_token(token)
    except ExpiredSignatureError as e:
        raise TokenExpired() from e
    except JWTError as e:
        raise InvalidToken() from e

    is_active = payload.get("is_active", True)
    if not is_active:
        raise AccountDisabled()

    return JWTUser(
        user_id=int(payload["sub"]),
        email=payload.get("email"),
        is_active=is_active,
    )


CurrentUser = Annotated[JWTUser, Depends(get_current_user)]
