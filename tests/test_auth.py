"""Tests for /api/v1/auth endpoints."""
from api.auth.service import hash_password
from tests.conftest import NOW

# ── Register ──────────────────────────────────────────────────────────────────


def test_register_success(client, mock_db):
    """POST /api/v1/auth/register → 201 with user + token."""
    cursor = mock_db._cursor

    # 1st execute: SELECT 1 FROM users WHERE email = ... → None (not exists)
    # 2nd execute: INSERT ... RETURNING → user row
    # 3rd execute: INSERT refresh_tokens
    cursor.set_results(
        None,                                              # email check
        (1, "new@test.com", True, NOW, None),              # INSERT user RETURNING
        None,                                              # INSERT refresh_token
    )

    res = client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "password": "securepass123",
    })
    assert res.status_code == 201
    data = res.json()
    assert "user" in data
    assert data["user"]["email"] == "new@test.com"
    assert "token" in data
    assert "access_token" in data["token"]


def test_register_duplicate_email(client, mock_db):
    """POST /api/v1/auth/register → 409 if email exists."""
    cursor = mock_db._cursor
    cursor.set_results((1,))  # email check → exists

    res = client.post("/api/v1/auth/register", json={
        "email": "exists@test.com",
        "password": "securepass123",
    })
    assert res.status_code == 409


def test_register_short_password(client):
    """POST /api/v1/auth/register → 422 if password < 8 chars."""
    res = client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "password": "short",
    })
    assert res.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────


def test_login_success(client, mock_db):
    """POST /api/v1/auth/login → 200 with user + token."""
    cursor = mock_db._cursor
    pw_hash = hash_password("correctpassword")

    # 1st: SELECT user row  2nd: UPDATE last_login  3rd: INSERT refresh_tokens
    cursor.set_results(
        (1, "user@test.com", pw_hash, True, NOW, None),  # SELECT user
        (NOW,),                                            # UPDATE last_login RETURNING
        None,                                              # INSERT refresh_token
    )

    res = client.post("/api/v1/auth/login", json={
        "email": "user@test.com",
        "password": "correctpassword",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["email"] == "user@test.com"
    assert "access_token" in data["token"]


def test_login_wrong_password(client, mock_db):
    """POST /api/v1/auth/login → 401 on wrong password."""
    cursor = mock_db._cursor
    pw_hash = hash_password("correctpassword")

    cursor.set_results(
        (1, "user@test.com", pw_hash, True, NOW, None),
    )

    res = client.post("/api/v1/auth/login", json={
        "email": "user@test.com",
        "password": "wrongpassword",
    })
    assert res.status_code == 401


def test_login_unknown_email(client, mock_db):
    """POST /api/v1/auth/login → 401 for unknown email."""
    mock_db._cursor.set_results(None)

    res = client.post("/api/v1/auth/login", json={
        "email": "ghost@test.com",
        "password": "anything123",
    })
    assert res.status_code == 401


# ── Me ────────────────────────────────────────────────────────────────────────


def test_me_authenticated(authed_client, test_user):
    """GET /api/v1/auth/me → 200 with user data."""
    res = authed_client.get("/api/v1/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == test_user.email
    assert data["user_id"] == test_user.user_id


def test_me_unauthenticated(client):
    """GET /api/v1/auth/me → 401 without token."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────


def test_logout(client, mock_db):
    """POST /api/v1/auth/logout → 204."""
    mock_db._cursor.set_results(None)

    res = client.post("/api/v1/auth/logout")
    assert res.status_code == 204


# ── Forgot/Reset Password ─────────────────────────────────────────────────────

def test_forgot_password_success(client, mock_db):
    """POST /api/v1/auth/forgot-password → 200 with dev reset token when user exists."""
    cursor = mock_db._cursor
    cursor.set_results(
        (1,),  # SELECT user_id FROM users
        None,  # UPDATE user reset token
    )

    res = client.post("/api/v1/auth/forgot-password", json={"email": "user@test.com"})
    assert res.status_code == 200
    data = res.json()
    assert "reset_token_dev" in data
    assert "link" in data["message"] or "sent" in data["message"]


def test_forgot_password_user_not_found(client, mock_db):
    """POST /api/v1/auth/forgot-password → 200 without dev reset token when user not found."""
    cursor = mock_db._cursor
    cursor.set_results(None)  # SELECT user_id -> not found

    res = client.post("/api/v1/auth/forgot-password", json={"email": "unknown@test.com"})
    assert res.status_code == 200
    data = res.json()
    assert "reset_token_dev" not in data


def test_reset_password_success(client, mock_db):
    """POST /api/v1/auth/reset-password → 200 when token is valid."""
    cursor = mock_db._cursor
    cursor.set_results(
        (1,),  # SELECT user_id FROM users with matching token
        None,  # UPDATE password_hash
    )

    res = client.post("/api/v1/auth/reset-password", json={
        "token": "valid_token",
        "new_password": "newsecurepassword123"
    })
    assert res.status_code == 200
    assert "reset successfully" in res.json()["message"]


def test_reset_password_invalid_token(client, mock_db):
    """POST /api/v1/auth/reset-password → 400 when token is invalid/expired."""
    cursor = mock_db._cursor
    cursor.set_results(None)  # SELECT user_id -> not found/invalid

    res = client.post("/api/v1/auth/reset-password", json={
        "token": "invalid_token",
        "new_password": "newsecurepassword123"
    })
    assert res.status_code == 400
    assert "Invalid or expired reset token" in res.json()["error"]["message"]
