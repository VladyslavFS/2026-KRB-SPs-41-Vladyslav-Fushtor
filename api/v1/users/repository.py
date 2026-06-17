"""
User-domain Repository classes — Repository pattern.

SavedEventRepository: manages user's bookmarked earthquake events.
AlertRuleRepository: manages user's alert rules.

Extracted from v1/users/service.py (was a module of bare functions).
"""
from __future__ import annotations

from psycopg2.extensions import connection

from api.v1.users.schemas import (
    AlertRuleOut,
    PaginatedAlertRules,
    PaginatedSavedEvents,
    SavedEventOut,
)


# ── Saved Events ───────────────────────────────────────────────────────────────

class SavedEventRepository:
    """Encapsulates all DB operations for a user's saved events."""

    def __init__(self, db: connection) -> None:
        self._db = db

    def save(self, user_id: int, event_id: str, note: str | None) -> SavedEventOut:
        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app.saved_events (user_id, event_id, note)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, event_id)
                DO UPDATE SET note = EXCLUDED.note
                RETURNING saved_event_id, user_id, event_id, note, created_at
                """,
                (user_id, event_id, note),
            )
            row = cur.fetchone()
        return SavedEventOut(
            saved_event_id=row[0], user_id=row[1], event_id=row[2],
            note=row[3], created_at=row[4],
        )

    def list(self, user_id: int, limit: int = 50, offset: int = 0) -> PaginatedSavedEvents:
        with self._db.cursor() as cur:
            cur.execute("SELECT count(*) FROM app.saved_events WHERE user_id = %s", (user_id,))
            total = cur.fetchone()[0]
            cur.execute(
                """
                SELECT saved_event_id, user_id, event_id, note, created_at
                FROM app.saved_events
                WHERE user_id = %s
                ORDER BY created_at DESC LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )
            rows = cur.fetchall()
        items = [
            SavedEventOut(saved_event_id=r[0], user_id=r[1], event_id=r[2], note=r[3], created_at=r[4])
            for r in rows
        ]
        return PaginatedSavedEvents(items=items, total=total, limit=limit, offset=offset)

    def delete(self, user_id: int, event_id: str) -> bool:
        with self._db.cursor() as cur:
            cur.execute(
                "DELETE FROM app.saved_events WHERE user_id = %s AND event_id = %s",
                (user_id, event_id),
            )
            return cur.rowcount > 0


# ── Alert Rules ────────────────────────────────────────────────────────────────

class AlertRuleRepository:
    """Encapsulates all DB operations for a user's alert rules."""

    def __init__(self, db: connection) -> None:
        self._db = db

    def create(
        self,
        user_id: int,
        name: str,
        min_magnitude: float | None,
        max_depth_km: float | None,
        region: str | None,
        is_active: bool,
    ) -> AlertRuleOut:
        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app.alert_rules
                    (user_id, name, min_magnitude, max_depth_km, region, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING alert_rule_id, user_id, name,
                          min_magnitude, max_depth_km, region,
                          is_active, created_at, updated_at
                """,
                (user_id, name, min_magnitude, max_depth_km, region, is_active),
            )
            return self._row_to_model(cur.fetchone())

    def list(self, user_id: int, limit: int = 50, offset: int = 0) -> PaginatedAlertRules:
        with self._db.cursor() as cur:
            cur.execute("SELECT count(*) FROM app.alert_rules WHERE user_id = %s", (user_id,))
            total = cur.fetchone()[0]
            cur.execute(
                """
                SELECT alert_rule_id, user_id, name, min_magnitude, max_depth_km,
                       region, is_active, created_at, updated_at
                FROM app.alert_rules
                WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )
            rows = cur.fetchall()
        items = [self._row_to_model(r) for r in rows]
        return PaginatedAlertRules(items=items, total=total, limit=limit, offset=offset)

    def get_by_id(self, user_id: int, alert_rule_id: int) -> AlertRuleOut | None:
        with self._db.cursor() as cur:
            cur.execute(
                """
                SELECT alert_rule_id, user_id, name, min_magnitude, max_depth_km,
                       region, is_active, created_at, updated_at
                FROM app.alert_rules
                WHERE alert_rule_id = %s AND user_id = %s
                """,
                (alert_rule_id, user_id),
            )
            row = cur.fetchone()
        return self._row_to_model(row) if row else None

    def update(self, user_id: int, alert_rule_id: int, **fields) -> AlertRuleOut | None:
        if not fields:
            return self.get_by_id(user_id, alert_rule_id)

        ALLOWED_COLUMNS = {"name", "min_magnitude", "max_depth_km", "region", "is_active"}
        set_parts = []
        params = []
        for col, val in fields.items():
            if col not in ALLOWED_COLUMNS:
                raise ValueError(f"Invalid column: {col}")
            set_parts.append(f"{col} = %s")
            params.append(val)

        set_parts.append("updated_at = now()")
        params.extend([alert_rule_id, user_id])

        with self._db.cursor() as cur:
            cur.execute(
                f"""
                UPDATE app.alert_rules
                SET {', '.join(set_parts)}
                WHERE alert_rule_id = %s AND user_id = %s
                RETURNING alert_rule_id, user_id, name, min_magnitude, max_depth_km,
                          region, is_active, created_at, updated_at
                """,
                params,
            )
            row = cur.fetchone()
        return self._row_to_model(row) if row else None

    def delete(self, user_id: int, alert_rule_id: int) -> bool:
        with self._db.cursor() as cur:
            cur.execute(
                "DELETE FROM app.alert_rules WHERE alert_rule_id = %s AND user_id = %s",
                (alert_rule_id, user_id),
            )
            return cur.rowcount > 0

    @staticmethod
    def _row_to_model(row: tuple) -> AlertRuleOut:
        return AlertRuleOut(
            alert_rule_id=row[0], user_id=row[1], name=row[2],
            min_magnitude=row[3], max_depth_km=row[4], region=row[5],
            is_active=row[6], created_at=row[7], updated_at=row[8],
        )
