"""
Users service layer — thin facade over SavedEventRepository + AlertRuleRepository.
Kept for backward compatibility with existing router.py imports.
"""
from __future__ import annotations

from psycopg2.extensions import connection

from api.v1.users.repository import AlertRuleRepository, SavedEventRepository
from api.v1.users.schemas import (
    AlertRuleOut,
    PaginatedAlertRules,
    PaginatedSavedEvents,
    SavedEventOut,
)

# ── Saved Events ───────────────────────────────────────────────────────────────

def save_event(db: connection, user_id: int, event_id: str, note: str | None) -> SavedEventOut:
    return SavedEventRepository(db).save(user_id, event_id, note)


def get_saved_events(db: connection, user_id: int, limit: int = 50, offset: int = 0) -> PaginatedSavedEvents:
    return SavedEventRepository(db).list(user_id, limit, offset)


def delete_saved_event(db: connection, user_id: int, event_id: str) -> bool:
    return SavedEventRepository(db).delete(user_id, event_id)


# ── Alert Rules ────────────────────────────────────────────────────────────────

def create_alert_rule(
    db: connection,
    user_id: int,
    name: str,
    min_magnitude: float | None,
    max_depth_km: float | None,
    region: str | None,
    is_active: bool,
) -> AlertRuleOut:
    return AlertRuleRepository(db).create(user_id, name, min_magnitude, max_depth_km, region, is_active)


def get_alert_rules(db: connection, user_id: int, limit: int = 50, offset: int = 0) -> PaginatedAlertRules:
    return AlertRuleRepository(db).list(user_id, limit, offset)


def get_alert_rule_by_id(db: connection, user_id: int, alert_rule_id: int) -> AlertRuleOut | None:
    return AlertRuleRepository(db).get_by_id(user_id, alert_rule_id)


def update_alert_rule(db: connection, user_id: int, alert_rule_id: int, **fields) -> AlertRuleOut | None:
    return AlertRuleRepository(db).update(user_id, alert_rule_id, **fields)


def delete_alert_rule(db: connection, user_id: int, alert_rule_id: int) -> bool:
    return AlertRuleRepository(db).delete(user_id, alert_rule_id)
