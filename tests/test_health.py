"""Tests for /health and / endpoints."""


def test_root(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "Earthquake Platform API"
    assert "version" in data
    assert "docs" in data


def test_health_returns_200(client):
    """Health check returns 200 even when DB/Redis are unreachable (degraded)."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in ("healthy", "degraded")
    assert "checks" in data
    assert "api" in data["checks"]
    assert data["checks"]["api"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
