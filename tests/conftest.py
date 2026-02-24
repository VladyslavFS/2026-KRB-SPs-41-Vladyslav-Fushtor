"""
Shared fixtures for FastAPI unit tests.
All DB/Redis deps are mocked — no external services needed.
"""
import time
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from api.auth.dependencies import get_current_user
from api.auth.schemas import JWTUser
from api.config import Settings
from api.dependencies import get_db_conn, get_settings
from api.middleware.rate_limit import RateLimitMiddleware

# ── Test settings (no .env needed) ────────────────────────────────────────────

def _test_settings() -> Settings:
    return Settings(
        _env_file=None,
        APP_ENV="test",
        DWH_HOST="localhost",
        DWH_PORT=5432,
        DWH_DB="test_db",
        DWH_USER="test",
        DWH_PASSWORD="test",
        REDIS_URL="redis://localhost:6379/0",
        JWT_SECRET_KEY="test-secret-key-for-unit-tests",
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15,
        JWT_REFRESH_TOKEN_EXPIRE_DAYS=30,
        JWT_REFRESH_TOKEN_BYTES=32,
    )


# ── Disable rate limiter for all non-rate-limit tests ─────────────────────────

_SENTINEL = object()

@pytest.fixture(autouse=True)
def _disable_rate_limiter(monkeypatch):
    """Bypass rate limiter so tests aren't blocked by real Redis."""
    async def _allow_all(self, key, limit, window):
        return True, limit, time.time() + window

    monkeypatch.setattr(RateLimitMiddleware, "_check_rate_limit", _allow_all)


# ── Mock DB cursor ───────────────────────────────────────────────────────────

class MockCursor:
    """
    Mimics psycopg2 cursor with configurable results queue.
    Each call to fetchone()/fetchall() pops from queue.
    """

    def __init__(self):
        self._results = []
        self.description = None
        self.rowcount = 0

    def set_results(self, *results, description=_SENTINEL):
        """
        Queue up multiple cursor results.
        Pass description= to set cursor.description for column metadata.
        """
        self._results = list(results)
        if description is not _SENTINEL:
            self.description = description

    def execute(self, query, params=None):
        pass

    def fetchone(self):
        if self._results:
            return self._results.pop(0)
        return None

    def fetchall(self):
        if self._results:
            val = self._results.pop(0)
            return val if isinstance(val, list) else [val] if val else []
        return []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def close(self):
        pass


# ── Mock DB connection ────────────────────────────────────────────────────────

class MockConnection:
    def __init__(self):
        self._cursor = MockCursor()

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    """Returns a MockConnection that can be configured per test."""
    return MockConnection()


@pytest.fixture
def test_user():
    """Standard test user for auth-required endpoints."""
    return JWTUser(user_id=1, email="test@example.com", is_active=True)


@pytest.fixture
def client(mock_db):
    """Unauthenticated TestClient with mocked DB."""
    from api.main import app

    app.dependency_overrides[get_db_conn] = lambda: mock_db
    app.dependency_overrides[get_settings] = _test_settings

    yield TestClient(app, raise_server_exceptions=False)

    app.dependency_overrides.clear()


@pytest.fixture
def authed_client(mock_db, test_user):
    """Authenticated TestClient — CurrentUser is pre-set, no real JWT needed."""
    from api.main import app

    app.dependency_overrides[get_db_conn] = lambda: mock_db
    app.dependency_overrides[get_settings] = _test_settings
    app.dependency_overrides[get_current_user] = lambda: test_user

    yield TestClient(app, raise_server_exceptions=False)

    app.dependency_overrides.clear()


# ── Helpers ───────────────────────────────────────────────────────────────────

NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)

SAMPLE_EVENT_COLS = [
    ("event_id",), ("time",), ("updated",), ("latitude",), ("longitude",),
    ("depth",), ("mag",), ("mag_type",), ("place",), ("net",),
    ("status",), ("event_type",), ("tsunami",), ("url",), ("detail",),
    ("alert",), ("sig",), ("felt",), ("mmi",), ("nst",),
    ("gap",), ("mag_error",), ("mag_bucket",), ("depth_bucket",), ("severity",),
]

SAMPLE_EVENT_ROW = (
    "us2026abc", NOW, NOW, 35.6, 139.7,
    10.0, 5.5, "ml", "Tokyo, Japan", "us",
    "reviewed", "earthquake", 0, "https://usgs.gov", None,
    None, 500, 10, 4.2, 30,
    50.0, 0.1, "5.0-5.9", "0-30", "MEDIUM",
)
