from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ── Requests ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=100)

# ── Responses ─────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    user_id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None


class JWTUser(BaseModel):
    user_id: int
    email: EmailStr
    is_active: bool


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int               # access seconds
    refresh_expires_in: int       # refresh seconds


class RegisterOut(BaseModel):
    user: UserOut
    token: TokenOut
