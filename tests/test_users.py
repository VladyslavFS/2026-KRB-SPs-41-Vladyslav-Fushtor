"""Tests for /api/v1/users/me endpoints (saved events + alert rules)."""
from tests.conftest import NOW

# ══════════════════════════════════════════════════════════════════════════════
#  SAVED EVENTS
# ══════════════════════════════════════════════════════════════════════════════


def test_save_event_success(authed_client, mock_db):
    """POST /api/v1/users/me/saved-events → 201."""
    mock_db._cursor.set_results(
        (1, 1, "us2026abc", "interesting", NOW),  # RETURNING row
    )

    res = authed_client.post("/api/v1/users/me/saved-events", json={
        "event_id": "us2026abc",
        "note": "interesting",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["event_id"] == "us2026abc"
    assert data["note"] == "interesting"
    assert data["user_id"] == 1


def test_save_event_no_note(authed_client, mock_db):
    """POST /api/v1/users/me/saved-events → 201 without note."""
    mock_db._cursor.set_results(
        (2, 1, "us2026xyz", None, NOW),
    )

    res = authed_client.post("/api/v1/users/me/saved-events", json={
        "event_id": "us2026xyz",
    })
    assert res.status_code == 201
    assert res.json()["note"] is None


def test_save_event_unauthenticated(client):
    """POST /api/v1/users/me/saved-events → 401 without auth."""
    res = client.post("/api/v1/users/me/saved-events", json={
        "event_id": "us2026abc",
    })
    assert res.status_code == 401


def test_get_saved_events(authed_client, mock_db):
    """GET /api/v1/users/me/saved-events → 200 paginated."""
    mock_db._cursor.set_results(
        (2,),  # count
        [
            (1, 1, "us2026abc", "note1", NOW),
            (2, 1, "us2026xyz", None, NOW),
        ],
    )

    res = authed_client.get("/api/v1/users/me/saved-events")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_get_saved_events_empty(authed_client, mock_db):
    """GET /api/v1/users/me/saved-events → 200 empty list."""
    mock_db._cursor.set_results((0,), [])

    res = authed_client.get("/api/v1/users/me/saved-events")
    assert res.status_code == 200
    assert res.json()["items"] == []


def test_delete_saved_event(authed_client, mock_db):
    """DELETE /api/v1/users/me/saved-events/us2026abc → 204."""
    mock_db._cursor.rowcount = 1

    res = authed_client.delete("/api/v1/users/me/saved-events/us2026abc")
    assert res.status_code == 204


def test_delete_saved_event_not_found(authed_client, mock_db):
    """DELETE /api/v1/users/me/saved-events/ghost → 404."""
    mock_db._cursor.rowcount = 0

    res = authed_client.delete("/api/v1/users/me/saved-events/ghost")
    assert res.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
#  ALERT RULES
# ══════════════════════════════════════════════════════════════════════════════


def test_create_alert_rule(authed_client, mock_db):
    """POST /api/v1/users/me/alert-rules → 201."""
    mock_db._cursor.set_results(
        (1, 1, "Strong quakes", 5.0, 100.0, "Japan", True, NOW, NOW),
    )

    res = authed_client.post("/api/v1/users/me/alert-rules", json={
        "name": "Strong quakes",
        "min_magnitude": 5.0,
        "max_depth_km": 100.0,
        "region": "Japan",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Strong quakes"
    assert data["min_magnitude"] == 5.0
    assert data["is_active"] is True


def test_create_alert_rule_unauthenticated(client):
    """POST /api/v1/users/me/alert-rules → 401 without auth."""
    res = client.post("/api/v1/users/me/alert-rules", json={
        "name": "Test",
    })
    assert res.status_code == 401


def test_get_alert_rules(authed_client, mock_db):
    """GET /api/v1/users/me/alert-rules → 200 paginated."""
    mock_db._cursor.set_results(
        (1,),  # count
        [
            (1, 1, "Strong quakes", 5.0, 100.0, "Japan", True, NOW, NOW),
        ],
    )

    res = authed_client.get("/api/v1/users/me/alert-rules")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_get_alert_rule_by_id(authed_client, mock_db):
    """GET /api/v1/users/me/alert-rules/1 → 200."""
    mock_db._cursor.set_results(
        (1, 1, "Strong quakes", 5.0, 100.0, "Japan", True, NOW, NOW),
    )

    res = authed_client.get("/api/v1/users/me/alert-rules/1")
    assert res.status_code == 200
    assert res.json()["alert_rule_id"] == 1


def test_get_alert_rule_not_found(authed_client, mock_db):
    """GET /api/v1/users/me/alert-rules/999 → 404."""
    mock_db._cursor.set_results(None)

    res = authed_client.get("/api/v1/users/me/alert-rules/999")
    assert res.status_code == 404


def test_patch_alert_rule(authed_client, mock_db):
    """PATCH /api/v1/users/me/alert-rules/1 → 200 updated."""
    mock_db._cursor.set_results(
        (1, 1, "Updated name", 5.0, 100.0, "Japan", False, NOW, NOW),
    )

    res = authed_client.patch("/api/v1/users/me/alert-rules/1", json={
        "name": "Updated name",
        "is_active": False,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Updated name"
    assert data["is_active"] is False


def test_patch_alert_rule_not_found(authed_client, mock_db):
    """PATCH /api/v1/users/me/alert-rules/999 → 404."""
    mock_db._cursor.set_results(None)

    res = authed_client.patch("/api/v1/users/me/alert-rules/999", json={
        "name": "Ghost",
    })
    assert res.status_code == 404


def test_delete_alert_rule(authed_client, mock_db):
    """DELETE /api/v1/users/me/alert-rules/1 → 204."""
    mock_db._cursor.rowcount = 1

    res = authed_client.delete("/api/v1/users/me/alert-rules/1")
    assert res.status_code == 204


def test_delete_alert_rule_not_found(authed_client, mock_db):
    """DELETE /api/v1/users/me/alert-rules/999 → 404."""
    mock_db._cursor.rowcount = 0

    res = authed_client.delete("/api/v1/users/me/alert-rules/999")
    assert res.status_code == 404
