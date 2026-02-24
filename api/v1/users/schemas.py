from datetime import datetime

from pydantic import BaseModel, Field

# ── Saved Events ──────────────────────────────────────────────────────────────

class SaveEventRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=255)
    note: str | None = Field(None, max_length=1000)


class SavedEventOut(BaseModel):
    saved_event_id: int
    user_id: int
    event_id: str
    note: str | None = None
    created_at: datetime


class PaginatedSavedEvents(BaseModel):
    items: list[SavedEventOut]
    total: int
    limit: int
    offset: int


# ── Alert Rules ───────────────────────────────────────────────────────────────

class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    min_magnitude: float | None = Field(None, ge=0.0, le=10.0)
    max_depth_km: float | None = Field(None, ge=0.0)
    region: str | None = Field(None, max_length=255)
    is_active: bool = True


class AlertRuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    min_magnitude: float | None = Field(None, ge=0.0, le=10.0)
    max_depth_km: float | None = Field(None, ge=0.0)
    region: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class AlertRuleOut(BaseModel):
    alert_rule_id: int
    user_id: int
    name: str
    min_magnitude: float | None = None
    max_depth_km: float | None = None
    region: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PaginatedAlertRules(BaseModel):
    items: list[AlertRuleOut]
    total: int
    limit: int
    offset: int
