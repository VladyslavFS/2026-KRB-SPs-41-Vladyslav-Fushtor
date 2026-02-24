from fastapi import APIRouter, HTTPException, Query, status

from api.dependencies import DBConnDep
from api.v1.events.schemas import EventOut, EventStats, PaginatedEvents, TopEventOut
from api.v1.events.service import (
    get_event_by_id,
    get_events,
    get_events_stats,
    get_top_daily_by_day,
    get_top_daily_days,
)

router = APIRouter(prefix="/api/v1/events", tags=["Events"])


@router.get("", response_model=PaginatedEvents, summary="List earthquake events")
def read_events(
    db: DBConnDep,
    mag_min: float | None = Query(None, description="Minimum magnitude"),
    severity: str | None = Query(None, description="Event severity classification"),
    hours: int | None = Query(None, description="Events from last N hours"),
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> PaginatedEvents:
    """
    Get a paginated feed of earthquake events with optional filtering.
    """
    return get_events(
        db=db,
        mag_min=mag_min,
        severity=severity,
        hours=hours,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=EventStats, summary="Event statistics")
def read_events_stats(
    db: DBConnDep,
    hours: int = Query(24, ge=1, description="Stats for last N hours"),
) -> EventStats:
    """
    Get aggregated statistics about events in the specified time window.
    """
    return get_events_stats(db=db, hours=hours)


@router.get("/top-daily", response_model=list[str], summary="Available top-daily dates")
def read_top_daily_days(
    db: DBConnDep,
    limit: int = Query(30, ge=1, le=365, description="Number of days to return"),
) -> list[str]:
    """
    Get available days that have top events data.
    """
    return get_top_daily_days(db=db, limit=limit)


@router.get(
    "/top-daily/{day}",
    response_model=list[TopEventOut],
    summary="Top events for a specific day",
    responses={404: {"description": "No data for requested day"}},
)
def read_top_daily(
    day: str,
    db: DBConnDep,
) -> list[TopEventOut]:
    """
    Get top earthquake events for a specific day, ranked by magnitude.
    """
    events = get_top_daily_by_day(db=db, day=day)
    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No top events found for day {day}",
        )
    return events


@router.get(
    "/{event_id}",
    response_model=EventOut,
    summary="Get event by ID",
    responses={404: {"description": "Event not found"}},
)
def read_event_by_id(event_id: str, db: DBConnDep) -> EventOut:
    """
    Get detailed information about a single specific earthquake event by ID.
    """
    event = get_event_by_id(db=db, event_id=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    return event
