"""
Pure auth helpers — no FastAPI deps here.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt


def hash_password(password: str) -> str:
    # bcrypt 4.0+ enforces 72 bytes limit. Be safe.
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode("utf-8")
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
        
    try:
        return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    user_id: int,
    email: str,
    is_active: bool,
    secret: str,
    algorithm: str,
    expires_minutes: int,
) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=expires_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "is_active": is_active,
        "type": "access",
        "iss": "pp_earthquake",
        "iat": int(now.timestamp()),
        "jti": secrets.token_hex(16),  # Unique identifier for the token
        "exp": expire,
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(token: str, secret: str, algorithm: str) -> dict:
    payload = jwt.decode(token, secret, algorithms=[algorithm])
    
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
        
    sub = payload.get("sub")
    if sub is None:
        raise JWTError("Missing sub claim")
    return payload


def create_refresh_token_plain(nbytes: int) -> str:
    return secrets.token_urlsafe(nbytes)


def hash_refresh_token(token_plain: str) -> str:
    return hashlib.sha256(token_plain.encode("utf-8")).hexdigest()


def refresh_expires_at(days: int) -> datetime:
    return datetime.now(UTC) + timedelta(days=days)
