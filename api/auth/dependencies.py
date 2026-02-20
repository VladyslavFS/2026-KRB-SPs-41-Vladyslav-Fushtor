"""
Auth-specific FastAPI dependencies.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from jose import ExpiredSignatureError, JWTError

from api.auth.exceptions import AccountDisabled, InvalidToken, TokenExpired
from api.auth.schemas import JWTUser
from api.auth.service import decode_access_token
from api.dependencies import SettingsDep


def _extract_access_token(request: Request) -> str:
    """
    Extracts access token from Authorization header, 
    falling back to an 'access_token' cookie if present.
    """
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
    
    try:
        payload = decode_access_token(
            token,
            settings.jwt_secret_key,
            settings.jwt_algorithm,
        )
    except ExpiredSignatureError as e:
        raise TokenExpired() from e
    except JWTError as e:
        raise InvalidToken() from e

    user_id = int(payload["sub"])
    email = payload.get("email")
    is_active = payload.get("is_active", True)

    if not is_active:
        raise AccountDisabled()

    return JWTUser(
        user_id=user_id,
        email=email,
        is_active=is_active,
    )


CurrentUser = Annotated[JWTUser, Depends(get_current_user)]
