const BASE = "";

async function request(method, path, { body, token } = {}) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return null;

  const data = res.ok ? await res.json() : null;
  return { ok: res.ok, status: res.status, data };
}

// ── Auth ──────────────────────────────────────────────────────

export async function apiRegister(email, password) {
  return request("POST", "/api/v1/auth/register", {
    body: { email, password },
  });
}

export async function apiLogin(email, password) {
  return request("POST", "/api/v1/auth/login", {
    body: { email, password },
  });
}

export async function apiLogout(token) {
  return request("POST", "/api/v1/auth/logout", { token });
}

export async function apiForgotPassword(email) {
  return request("POST", "/api/v1/auth/forgot-password", {
    body: { email },
  });
}

export async function apiResetPassword(token, newPassword) {
  return request("POST", "/api/v1/auth/reset-password", {
    body: { token, new_password: newPassword },
  });
}

export async function apiGetMe(token) {
  return request("GET", "/api/v1/auth/me", { token });
}

// ── Events (public) ──────────────────────────────────────────

export async function apiGetEvents(params = {}) {
  const q = new URLSearchParams();
  if (params.hours) q.set("hours", params.hours);
  if (params.mag_min > 0) q.set("mag_min", params.mag_min);
  if (params.severity && params.severity !== "ALL")
    q.set("severity", params.severity);
  q.set("limit", params.limit || 200);
  q.set("offset", params.offset || 0);

  return request("GET", `/api/v1/events?${q}`);
}

export async function apiGetEventsStats(hours = 24) {
  return request("GET", `/api/v1/events/stats?hours=${hours}`);
}

export async function apiGetTopDailyDays(limit = 30) {
  return request("GET", `/api/v1/events/top-daily?limit=${limit}`);
}

export async function apiGetTopDaily(day) {
  return request("GET", `/api/v1/events/top-daily/${day}`);
}

// ── Saved Events (auth) ──────────────────────────────────────

export async function apiGetSavedEvents(token, limit = 100) {
  return request("GET", `/api/v1/users/me/saved-events?limit=${limit}`, {
    token,
  });
}

export async function apiSaveEvent(token, eventId, note) {
  return request("POST", "/api/v1/users/me/saved-events", {
    token,
    body: { event_id: eventId, note },
  });
}

export async function apiDeleteSavedEvent(token, eventId) {
  return request("DELETE", `/api/v1/users/me/saved-events/${eventId}`, {
    token,
  });
}

// ── Alert Rules (auth) ───────────────────────────────────────

export async function apiGetAlertRules(token, limit = 100) {
  return request("GET", `/api/v1/users/me/alert-rules?limit=${limit}`, {
    token,
  });
}

export async function apiCreateAlertRule(token, rule) {
  return request("POST", "/api/v1/users/me/alert-rules", {
    token,
    body: rule,
  });
}

export async function apiUpdateAlertRule(token, ruleId, fields) {
  return request("PATCH", `/api/v1/users/me/alert-rules/${ruleId}`, {
    token,
    body: fields,
  });
}

export async function apiDeleteAlertRule(token, ruleId) {
  return request("DELETE", `/api/v1/users/me/alert-rules/${ruleId}`, {
    token,
  });
}
