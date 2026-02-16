from pydantic import BaseModel, Field
from typing import Optional


class ErrorResponse(BaseModel):
    """Standard error response"""
    code: int
    message: str
    details: Optional[dict] = None


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None