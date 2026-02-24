"""
Tests for rate limiting middleware.
Uses in-memory FakeRedis — no real Redis needed.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.rate_limit import RateLimitMiddleware

# Save the real method BEFORE conftest's autouse fixture patches it
_original_check_rate_limit = RateLimitMiddleware._check_rate_limit


@pytest.fixture(autouse=True)
def _restore_rate_limiter(monkeypatch):
    """Re-set the original _check_rate_limit so FakeRedis tests work."""
    monkeypatch.setattr(
        RateLimitMiddleware, "_check_rate_limit", _original_check_rate_limit
    )

# ── In-memory Redis fake ──────────────────────────────────────────────────────

class FakeRedisPipeline:
    """Mimics redis.Pipeline for sorted-set ops used by rate limiter."""

    def __init__(self, store):
        self._store = store
        self._ops = []

    def zremrangebyscore(self, key, min_score, max_score):
        self._ops.append(("zremrangebyscore", key, min_score, max_score))
        return self

    def zadd(self, key, mapping):
        self._ops.append(("zadd", key, mapping))
        return self

    def zcard(self, key):
        self._ops.append(("zcard", key))
        return self

    def expire(self, key, ttl):
        self._ops.append(("expire", key, ttl))
        return self

    def execute(self):
        results = []
        for op in self._ops:
            if op[0] == "zremrangebyscore":
                _, key, min_s, max_s = op
                if key in self._store:
                    self._store[key] = {
                        k: v for k, v in self._store[key].items()
                        if not (min_s <= v <= max_s)
                    }
                results.append(0)

            elif op[0] == "zadd":
                _, key, mapping = op
                if key not in self._store:
                    self._store[key] = {}
                self._store[key].update(mapping)
                results.append(len(mapping))

            elif op[0] == "zcard":
                _, key = op
                results.append(len(self._store.get(key, {})))

            elif op[0] == "expire":
                results.append(True)

        self._ops.clear()
        return results


class FakeRedis:
    """Minimal Redis fake supporting pipeline() for sorted sets."""

    def __init__(self):
        self._store = {}

    def pipeline(self):
        return FakeRedisPipeline(self._store)


# ── Test app with rate limiter ────────────────────────────────────────────────

def _make_app(anonymous_limit=3, authenticated_limit=10, window=60):
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        redis_client=FakeRedis(),
        anonymous_limit=anonymous_limit,
        authenticated_limit=authenticated_limit,
        window_seconds=window,
    )

    @app.get("/")
    def root():
        return {"ok": True}

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    return app


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_requests_within_limit():
    """Requests within limit should succeed with rate-limit headers."""
    client = TestClient(_make_app(anonymous_limit=5))

    for i in range(5):
        res = client.get("/")
        assert res.status_code == 200, f"Request {i+1} should succeed"
        assert "X-RateLimit-Limit" in res.headers
        assert "X-RateLimit-Remaining" in res.headers


def test_rate_limit_exceeded():
    """Request beyond limit should return 429."""
    client = TestClient(_make_app(anonymous_limit=3))

    # Make 3 allowed requests
    for _ in range(3):
        res = client.get("/")
        assert res.status_code == 200

    # 4th should be blocked
    res = client.get("/")
    assert res.status_code == 429
    body = res.json()
    assert body["error"]["code"] == 429
    assert "Rate limit exceeded" in body["error"]["message"]
    assert "Retry-After" in res.headers


def test_health_excluded_from_rate_limit():
    """Health endpoint should never be rate limited."""
    client = TestClient(_make_app(anonymous_limit=2))

    # Exhaust limit on /
    for _ in range(2):
        client.get("/")

    # /health should still work
    for _ in range(10):
        res = client.get("/health")
        assert res.status_code == 200


def test_authenticated_higher_limit():
    """Bearer token requests get higher limit."""
    client = TestClient(_make_app(anonymous_limit=2, authenticated_limit=5))
    headers = {"Authorization": "Bearer test-token-12345678901234567890"}

    # Anonymous limit is 2 — but with token, limit is 5
    for i in range(5):
        res = client.get("/", headers=headers)
        assert res.status_code == 200, f"Authed request {i+1} should succeed"

    # 6th should be blocked
    res = client.get("/", headers=headers)
    assert res.status_code == 429


def test_rate_limit_headers_format():
    """Rate limit headers should contain valid numeric values."""
    client = TestClient(_make_app(anonymous_limit=10))

    res = client.get("/")
    assert res.status_code == 200
    assert int(res.headers["X-RateLimit-Limit"]) == 10
    assert int(res.headers["X-RateLimit-Remaining"]) >= 0
    assert int(res.headers["X-RateLimit-Reset"]) > 0


def test_separate_keys_per_token():
    """Different tokens should have separate rate limit counters."""
    client = TestClient(_make_app(anonymous_limit=2, authenticated_limit=2))

    headers_a = {"Authorization": "Bearer token-aaaaaaaaaaaaaaaaaaaaaaaaa"}
    headers_b = {"Authorization": "Bearer token-bbbbbbbbbbbbbbbbbbbbbbbbb"}

    # Each token gets 2 requests
    for _ in range(2):
        assert client.get("/", headers=headers_a).status_code == 200
        assert client.get("/", headers=headers_b).status_code == 200

    # Both should be blocked now
    assert client.get("/", headers=headers_a).status_code == 429
    assert client.get("/", headers=headers_b).status_code == 429