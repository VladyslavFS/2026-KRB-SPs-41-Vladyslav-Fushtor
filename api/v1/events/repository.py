"""
EventRepository — Repository pattern for earthquake event queries.

Extracted from v1/events/service.py (was a module of bare functions).
Pattern: Repository — separates query logic from HTTP handler code.
"""
from __future__ import annotations

from psycopg2.extensions import connection

from api.v1.events.schemas import EventOut, EventStats, PaginatedEvents, TopEventOut


class EventRepository:
    """
    Encapsulates all DB read operations for earthquake events.
    Receives a psycopg2 connection (injected per-request via FastAPI DI).
    """

    def __init__(self, db: connection) -> None:
        self._db = db

    def get_events(
        self,
        *,
        mag_min: float | None = None,
        severity: str | None = None,
        hours: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedEvents:
        base_query = "SELECT * FROM bi.event_feed WHERE 1=1"
        count_query = "SELECT count(*) FROM bi.event_feed WHERE 1=1"
        params: list = []
        conditions: list[str] = []

        if mag_min is not None:
            conditions.append("mag >= %s")
            params.append(mag_min)
        if severity is not None:
            conditions.append("severity = %s")
            params.append(severity)
        if hours is not None and hours > 0:
            conditions.append("time >= now() - interval %s")
            params.append(f"{hours} hours")

        if conditions:
            where = " AND " + " AND ".join(conditions)
            base_query += where
            count_query += where

        with self._db.cursor() as cur:
            cur.execute(count_query, params)
            total = cur.fetchone()[0]

        query = base_query + " ORDER BY time DESC LIMIT %s OFFSET %s"
        with self._db.cursor() as cur:
            cur.execute(query, params + [limit, offset])
            cols = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        items = [EventOut(**dict(zip(cols, row, strict=False))) for row in rows]
        return PaginatedEvents(items=items, total=total, limit=limit, offset=offset)

    def get_event_by_id(self, event_id: str) -> EventOut | None:
        with self._db.cursor() as cur:
            cur.execute("SELECT * FROM ods.fct_earthquake_event WHERE id = %s", (event_id,))
            row = cur.fetchone()
            if not row:
                return None
            cols = [desc[0] for desc in cur.description]
            row_dict = dict(zip(cols, row, strict=False))
            row_dict["event_id"] = row_dict.pop("id", event_id)
            return EventOut(**row_dict)

    def get_events_stats(self, hours: int = 24) -> EventStats:
        query = f"""
            SELECT
                count(*) as total_events,
                max(mag) as max_mag,
                sum(tsunami) as tsunami_events,
                avg(depth) as avg_depth
            FROM bi.event_feed
            WHERE time >= now() - interval '{hours} hours'
        """
        with self._db.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
        return EventStats(
            total_events=row[0] or 0,
            max_mag=row[1],
            tsunami_events=row[2] or 0,
            avg_depth=row[3],
        )

    def get_top_daily_days(self, limit: int = 30) -> list[str]:
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT day FROM bi.top_events_daily ORDER BY day DESC LIMIT %s",
                (limit,),
            )
            return [str(row[0]) for row in cur.fetchall()]

    def get_top_daily_by_day(self, day: str) -> list[TopEventOut]:
        with self._db.cursor() as cur:
            cur.execute(
                """
                SELECT day, rank, event_id, time, mag, depth,
                       place, latitude, longitude, tsunami, url, net, status
                FROM bi.top_events_daily
                WHERE day = %s
                ORDER BY rank ASC
                """,
                (day,),
            )
            cols = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        return [TopEventOut(**dict(zip(cols, row, strict=False))) for row in rows]
