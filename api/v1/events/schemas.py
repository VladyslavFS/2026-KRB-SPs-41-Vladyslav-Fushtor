from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventBase(BaseModel):
    event_id: str
    time: datetime
    updated: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    depth: float | None = None
    mag: float | None = None
    mag_type: str | None = None
    place: str | None = None
    net: str | None = None
    status: str | None = None
    event_type: str | None = None
    tsunami: int | None = None
    url: str | None = None
    detail: str | None = None
    alert: str | None = None
    sig: int | None = None
    felt: int | None = None
    mmi: float | None = None
    nst: int | None = None
    gap: float | None = None
    mag_error: float | None = None
    mag_bucket: str | None = None
    depth_bucket: str | None = None
    severity: str | None = None

    model_config = ConfigDict(from_attributes=True)


class EventOut(EventBase):
    pass


class PaginatedEvents(BaseModel):
    items: list[EventOut]
    total: int
    limit: int
    offset: int


class EventStats(BaseModel):
    total_events: int
    max_mag: float | None = None
    tsunami_events: int
    avg_depth: float | None = None


class TopEventOut(BaseModel):
    day: str
    rank: int
    event_id: str
    time: datetime
    mag: float | None = None
    depth: float | None = None
    place: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    tsunami: int | None = None
    url: str | None = None
    net: str | None = None
    status: str | None = None
