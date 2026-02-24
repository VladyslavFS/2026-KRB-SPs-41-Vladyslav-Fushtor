"""Tests for /api/v1/events endpoints."""
from datetime import date

from tests.conftest import NOW, SAMPLE_EVENT_COLS, SAMPLE_EVENT_ROW

# ── GET /api/v1/events ────────────────────────────────────────────────────────

def test_events_list(client, mock_db):
    """GET /api/v1/events → 200 with paginated items."""
    cursor = mock_db._cursor
    # 1st cursor ctx: count → (5,)
    # 2nd cursor ctx: SELECT * → [rows] (needs description for column names)
    cursor.set_results(
        (5,),
        [SAMPLE_EVENT_ROW],
        description=SAMPLE_EVENT_COLS,
    )

    res = client.get("/api/v1/events?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 5
    assert len(data["items"]) == 1
    assert data["items"][0]["event_id"] == "us2026abc"
    assert data["items"][0]["severity"] == "MEDIUM"


def test_events_empty(client, mock_db):
    """GET /api/v1/events → 200 with empty items."""
    mock_db._cursor.set_results(
        (0,), [],
        description=SAMPLE_EVENT_COLS,
    )

    res = client.get("/api/v1/events")
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_events_with_filters(client, mock_db):
    """GET /api/v1/events?mag_min=4&severity=HIGH → 200 applies filters."""
    mock_db._cursor.set_results(
        (1,), [SAMPLE_EVENT_ROW],
        description=SAMPLE_EVENT_COLS,
    )

    res = client.get("/api/v1/events?mag_min=4&severity=HIGH&hours=24")
    assert res.status_code == 200
    assert res.json()["total"] == 1


# ── GET /api/v1/events/stats ─────────────────────────────────────────────────

def test_events_stats(client, mock_db):
    """GET /api/v1/events/stats → 200 with aggregates."""
    mock_db._cursor.set_results(
        (42, 6.5, 3, 25.4),
    )

    res = client.get("/api/v1/events/stats?hours=24")
    assert res.status_code == 200
    data = res.json()
    assert data["total_events"] == 42
    assert data["max_mag"] == 6.5
    assert data["tsunami_events"] == 3
    assert data["avg_depth"] == 25.4


def test_events_stats_empty(client, mock_db):
    """GET /api/v1/events/stats → 200 with zeros when no data."""
    mock_db._cursor.set_results((0, None, 0, None))

    res = client.get("/api/v1/events/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_events"] == 0
    assert data["max_mag"] is None


# ── GET /api/v1/events/top-daily ──────────────────────────────────────────────

def test_top_daily_days(client, mock_db):
    """GET /api/v1/events/top-daily → 200 list of day strings."""
    mock_db._cursor.set_results(
        [(date(2026, 1, 15),), (date(2026, 1, 14),)],
    )

    res = client.get("/api/v1/events/top-daily?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0] == "2026-01-15"


# ── GET /api/v1/events/top-daily/{day} ────────────────────────────────────────

TOP_COLS = [
    ("day",), ("rank",), ("event_id",), ("time",), ("mag",), ("depth",),
    ("place",), ("latitude",), ("longitude",), ("tsunami",), ("url",),
    ("net",), ("status",),
]


def test_top_daily_by_day(client, mock_db):
    """GET /api/v1/events/top-daily/2026-01-15 → 200 event list."""
    mock_db._cursor.set_results(
        [(date(2026, 1, 15), 1, "us2026abc", NOW, 5.5, 10.0,
          "Tokyo", 35.6, 139.7, 0, "https://usgs.gov", "us", "reviewed")],
        description=TOP_COLS,
    )

    res = client.get("/api/v1/events/top-daily/2026-01-15")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["event_id"] == "us2026abc"
    assert data[0]["rank"] == 1


def test_top_daily_by_day_404(client, mock_db):
    """GET /api/v1/events/top-daily/9999-01-01 → 404 if no data."""
    mock_db._cursor.set_results([], description=TOP_COLS)

    res = client.get("/api/v1/events/top-daily/9999-01-01")
    assert res.status_code == 404


# ── GET /api/v1/events/{event_id} ────────────────────────────────────────────

def test_event_by_id(client, mock_db):
    """GET /api/v1/events/us2026abc → 200 with event."""
    ods_cols = list(SAMPLE_EVENT_COLS)
    ods_cols[0] = ("id",)  # ODS table uses 'id' not 'event_id'

    mock_db._cursor.set_results(
        SAMPLE_EVENT_ROW,
        description=ods_cols,
    )

    res = client.get("/api/v1/events/us2026abc")
    assert res.status_code == 200
    assert res.json()["event_id"] == "us2026abc"


def test_event_by_id_not_found(client, mock_db):
    """GET /api/v1/events/nonexistent → 404."""
    mock_db._cursor.set_results()

    res = client.get("/api/v1/events/nonexistent")
    assert res.status_code == 404
