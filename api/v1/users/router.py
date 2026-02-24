from fastapi import APIRouter, HTTPException, Query, status

from api.auth.dependencies import CurrentUser
from api.dependencies import DBConnDep
from api.v1.users.schemas import (
    AlertRuleCreate,
    AlertRuleOut,
    AlertRuleUpdate,
    PaginatedAlertRules,
    PaginatedSavedEvents,
    SavedEventOut,
    SaveEventRequest,
)
from api.v1.users.service import (
    create_alert_rule,
    delete_alert_rule,
    delete_saved_event,
    get_alert_rule_by_id,
    get_alert_rules,
    get_saved_events,
    save_event,
    update_alert_rule,
)

router = APIRouter(prefix="/api/v1/users/me", tags=["Users"])


# ── Saved Events ──────────────────────────────────────────────────────────────

@router.post("/saved-events", response_model=SavedEventOut, status_code=201)
def create_saved_event(
    body: SaveEventRequest,
    user: CurrentUser,
    db: DBConnDep,
) -> SavedEventOut:
    """
    Save an earthquake event to the user's collection.
    If the event is already saved, its note will be updated.
    """
    return save_event(
        db=db,
        user_id=user.user_id,
        event_id=body.event_id,
        note=body.note,
    )


@router.get("/saved-events", response_model=PaginatedSavedEvents)
def read_saved_events(
    user: CurrentUser,
    db: DBConnDep,
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> PaginatedSavedEvents:
    """
    Get all saved events for the current user (paginated).
    """
    return get_saved_events(
        db=db,
        user_id=user.user_id,
        limit=limit,
        offset=offset,
    )


@router.delete(
    "/saved-events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_saved_event(
    event_id: str,
    user: CurrentUser,
    db: DBConnDep,
):
    """
    Remove a saved event from the user's collection.
    """
    deleted = delete_saved_event(db=db, user_id=user.user_id, event_id=event_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved event '{event_id}' not found",
        )
    return None


# ── Alert Rules ───────────────────────────────────────────────────────────────

@router.post("/alert-rules", response_model=AlertRuleOut, status_code=201)
def create_rule(
    body: AlertRuleCreate,
    user: CurrentUser,
    db: DBConnDep,
) -> AlertRuleOut:
    """
    Create a new alert rule for the current user.
    """
    return create_alert_rule(
        db=db,
        user_id=user.user_id,
        name=body.name,
        min_magnitude=body.min_magnitude,
        max_depth_km=body.max_depth_km,
        region=body.region,
        is_active=body.is_active,
    )


@router.get("/alert-rules", response_model=PaginatedAlertRules)
def read_rules(
    user: CurrentUser,
    db: DBConnDep,
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> PaginatedAlertRules:
    """
    Get all alert rules for the current user (paginated).
    """
    return get_alert_rules(
        db=db,
        user_id=user.user_id,
        limit=limit,
        offset=offset,
    )


@router.get("/alert-rules/{alert_rule_id}", response_model=AlertRuleOut)
def read_rule(
    alert_rule_id: int,
    user: CurrentUser,
    db: DBConnDep,
) -> AlertRuleOut:
    """
    Get a specific alert rule by ID (owned by the current user).
    """
    rule = get_alert_rule_by_id(db=db, user_id=user.user_id, alert_rule_id=alert_rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule {alert_rule_id} not found",
        )
    return rule


@router.patch("/alert-rules/{alert_rule_id}", response_model=AlertRuleOut)
def patch_rule(
    alert_rule_id: int,
    body: AlertRuleUpdate,
    user: CurrentUser,
    db: DBConnDep,
) -> AlertRuleOut:
    """
    Partially update an alert rule. Only provided fields are changed.
    """
    update_data = body.model_dump(exclude_unset=True)
    rule = update_alert_rule(
        db=db,
        user_id=user.user_id,
        alert_rule_id=alert_rule_id,
        **update_data,
    )
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule {alert_rule_id} not found",
        )
    return rule


@router.delete(
    "/alert-rules/{alert_rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_rule(
    alert_rule_id: int,
    user: CurrentUser,
    db: DBConnDep,
):
    """
    Delete an alert rule by ID (owned by the current user).
    """
    deleted = delete_alert_rule(db=db, user_id=user.user_id, alert_rule_id=alert_rule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule {alert_rule_id} not found",
        )
    return None
