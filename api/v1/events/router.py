from fastapi import APIRouter, HTTPException, Query, status

from api.dependencies import DBConnDep
from api.v1.events.schemas import EventOut, EventStats, PaginatedEvents
from api.v1.events.service import get_event_by_id, get_events, get_events_stats

router = APIRouter(prefix="/api/v1/events", tags=["Events"])


@router.get("", response_model=PaginatedEvents)
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


@router.get("/stats", response_model=EventStats)
def read_events_stats(
    db: DBConnDep,
    hours: int = Query(24, ge=1, description="Stats for last N hours"),
) -> EventStats:
    """
    Get aggregated statistics about events in the specified time window.
    """
    return get_events_stats(db=db, hours=hours)


@router.get("/{event_id}", response_model=EventOut)
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
