"""
Service layer for events: logic for querying the database.
"""
from psycopg2.extensions import connection

from api.v1.events.schemas import EventOut, EventStats, PaginatedEvents


def get_events(
    db: connection,
    mag_min: float | None = None,
    severity: str | None = None,
    hours: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedEvents:
    base_query = "SELECT * FROM bi.event_feed WHERE 1=1"
    count_query = "SELECT count(*) FROM bi.event_feed WHERE 1=1"
    
    params = []
    conditions = []
    
    if mag_min is not None:
        conditions.append("mag >= %s")
        params.append(mag_min)
        
    if severity is not None:
        conditions.append("severity = %s")
        params.append(severity)
        
    if hours is not None:
        conditions.append(f"time >= now() - interval '{hours} hours'")
        
    if conditions:
        where_clause = " AND " + " AND ".join(conditions)
        base_query += where_clause
        count_query += where_clause
        
    # Get total count first
    with db.cursor() as cur:
        cur.execute(count_query, params)
        total = cur.fetchone()[0]
        
    # Get page items
    query = base_query + " ORDER BY time DESC LIMIT %s OFFSET %s"
    page_params = params + [limit, offset]
    
    with db.cursor() as cur:
        cur.execute(query, page_params)
        # Fetch dictionary-like format using column names
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        
    items = []
    for row in rows:
        row_dict = dict(zip(cols, row, strict=False))
        items.append(EventOut(**row_dict))
        
    return PaginatedEvents(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


def get_event_by_id(db: connection, event_id: str) -> EventOut | None:
    query = "SELECT * FROM ods.fct_earthquake_event WHERE id = %s"
    
    with db.cursor() as cur:
        cur.execute(query, (event_id,))
        row = cur.fetchone()
        if not row:
            return None
        cols = [desc[0] for desc in cur.description]
        row_dict = dict(zip(cols, row, strict=False))
        
        # Mapping differences between ods and bi if needed, 
        # but ods has similar shape. ODS uses 'id', BI uses 'event_id'
        row_dict["event_id"] = row_dict.pop("id", event_id)
        
        return EventOut(**row_dict)


def get_events_stats(db: connection, hours: int = 24) -> EventStats:
    query = f"""
        SELECT 
            count(*) as total_events,
            max(mag) as max_mag,
            sum(tsunami) as tsunami_events,
            avg(depth) as avg_depth
        FROM bi.event_feed
        WHERE time >= now() - interval '{hours} hours'
    """
    
    with db.cursor() as cur:
        cur.execute(query)
        row = cur.fetchone()
        
        return EventStats(
            total_events=row[0] or 0,
            max_mag=row[1],
            tsunami_events=row[2] or 0,
            avg_depth=row[3]
        )
