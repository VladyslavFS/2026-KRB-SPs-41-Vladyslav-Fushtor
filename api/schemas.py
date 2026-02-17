"""
Global request/response schemas.
Domain-specific schemas live in their own modules (e.g. api/auth/schemas.py).
"""
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: int
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: dict | None = None