from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: int
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: dict | None = None