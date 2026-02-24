import os

import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")


class EarthquakeAPIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self._base = base_url
        self._token: str | None = None

    # ── Token management ──────────────────────────────────────────────────────

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    def set_token(self, token: str | None):
        self._token = token

    def _headers(self) -> dict:
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}

    def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        return httpx.get(
            f"{self._base}{path}",
            params=params,
            headers=self._headers(),
            timeout=15,
        )

    def _post(self, path: str, json: dict | None = None) -> httpx.Response:
        return httpx.post(
            f"{self._base}{path}",
            json=json,
            headers=self._headers(),
            timeout=15,
        )

    def _patch(self, path: str, json: dict) -> httpx.Response:
        return httpx.patch(
            f"{self._base}{path}",
            json=json,
            headers=self._headers(),
            timeout=15,
        )

    def _delete(self, path: str) -> httpx.Response:
        return httpx.delete(
            f"{self._base}{path}",
            headers=self._headers(),
            timeout=15,
        )

    # ── Auth ──────────────────────────────────────────────────────────────────

    def register(self, email: str, password: str) -> dict | None:
        r = self._post("/api/v1/auth/register", json={"email": email, "password": password})
        if r.status_code == 201:
            data = r.json()
            self._token = data["token"]["access_token"]
            return data
        return None

    def login(self, email: str, password: str) -> dict | None:
        r = self._post("/api/v1/auth/login", json={"email": email, "password": password})
        if r.status_code == 200:
            data = r.json()
            self._token = data["token"]["access_token"]
            return data
        return None

    def logout(self):
        self._post("/api/v1/auth/logout")
        self._token = None

    def get_me(self) -> dict | None:
        r = self._get("/api/v1/auth/me")
        if r.status_code == 200:
            return r.json()
        return None

    # ── Events (public) ───────────────────────────────────────────────────────

    def get_events(
        self,
        hours: int | None = None,
        mag_min: float | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        params = {"limit": limit, "offset": offset}
        if hours is not None:
            params["hours"] = hours
        if mag_min is not None and mag_min > 0:
            params["mag_min"] = mag_min
        if severity and severity != "ALL":
            params["severity"] = severity

        r = self._get("/api/v1/events", params=params)
        if r.status_code == 200:
            return r.json()
        return {"items": [], "total": 0, "limit": limit, "offset": offset}

    def get_events_stats(self, hours: int = 24) -> dict:
        r = self._get("/api/v1/events/stats", params={"hours": hours})
        if r.status_code == 200:
            return r.json()
        return {"total_events": 0, "max_mag": None, "tsunami_events": 0, "avg_depth": None}

    def get_top_daily_days(self, limit: int = 30) -> list[str]:
        r = self._get("/api/v1/events/top-daily", params={"limit": limit})
        if r.status_code == 200:
            return r.json()
        return []

    def get_top_daily(self, day: str) -> list[dict]:
        r = self._get(f"/api/v1/events/top-daily/{day}")
        if r.status_code == 200:
            return r.json()
        return []

    # ── Saved Events (auth required) ──────────────────────────────────────────

    def get_saved_events(self, limit: int = 100, offset: int = 0) -> dict:
        r = self._get(
            "/api/v1/users/me/saved-events",
            params={"limit": limit, "offset": offset},
        )
        if r.status_code == 200:
            return r.json()
        return {"items": [], "total": 0, "limit": limit, "offset": offset}

    def save_event(self, event_id: str, note: str | None = None) -> dict | None:
        r = self._post(
            "/api/v1/users/me/saved-events",
            json={"event_id": event_id, "note": note},
        )
        if r.status_code == 201:
            return r.json()
        return None

    def delete_saved_event(self, event_id: str) -> bool:
        r = self._delete(f"/api/v1/users/me/saved-events/{event_id}")
        return r.status_code == 204

    # ── Alert Rules (auth required) ───────────────────────────────────────────

    def get_alert_rules(self, limit: int = 100, offset: int = 0) -> dict:
        r = self._get(
            "/api/v1/users/me/alert-rules",
            params={"limit": limit, "offset": offset},
        )
        if r.status_code == 200:
            return r.json()
        return {"items": [], "total": 0, "limit": limit, "offset": offset}

    def create_alert_rule(
        self,
        name: str,
        min_magnitude: float | None = None,
        max_depth_km: float | None = None,
        region: str | None = None,
        is_active: bool = True,
    ) -> dict | None:
        r = self._post(
            "/api/v1/users/me/alert-rules",
            json={
                "name": name,
                "min_magnitude": min_magnitude,
                "max_depth_km": max_depth_km,
                "region": region,
                "is_active": is_active,
            },
        )
        if r.status_code == 201:
            return r.json()
        return None

    def update_alert_rule(self, rule_id: int, **fields) -> dict | None:
        r = self._patch(f"/api/v1/users/me/alert-rules/{rule_id}", json=fields)
        if r.status_code == 200:
            return r.json()
        return None

    def delete_alert_rule(self, rule_id: int) -> bool:
        r = self._delete(f"/api/v1/users/me/alert-rules/{rule_id}")
        return r.status_code == 204
