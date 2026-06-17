"""
Events service layer — thin facade over EventRepository.
Kept for backward compatibility with existing router.py imports.
"""
from __future__ import annotations

from psycopg2.extensions import connection

from api.v1.events.repository import EventRepository
from api.v1.events.schemas import EventOut, EventStats, PaginatedEvents, TopEventOut


def get_events(
    db: connection,
    mag_min: float | None = None,
    severity: str | None = None,
    hours: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedEvents:
    return EventRepository(db).get_events(
        mag_min=mag_min, severity=severity, hours=hours, limit=limit, offset=offset,
    )


def get_event_by_id(db: connection, event_id: str) -> EventOut | None:
    return EventRepository(db).get_event_by_id(event_id)


def get_events_stats(db: connection, hours: int = 24) -> EventStats:
    return EventRepository(db).get_events_stats(hours)


def get_top_daily_days(db: connection, limit: int = 30) -> list[str]:
    return EventRepository(db).get_top_daily_days(limit)


def get_top_daily_by_day(db: connection, day: str) -> list[TopEventOut]:
    return EventRepository(db).get_top_daily_by_day(day)
