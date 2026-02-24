-- ============================================================
-- 006_user_features.sql
-- User-specific features: saved events & alert rules
-- ============================================================

-- ── Saved Events ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS app.saved_events (
    saved_event_id  BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES app.users(user_id) ON DELETE CASCADE,
    event_id        TEXT   NOT NULL,                 -- references ods.fct_earthquake_event(id)
    note            TEXT,                            -- optional user note / comment
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (user_id, event_id)                      -- prevent duplicate saves
);

CREATE INDEX IF NOT EXISTS ix_app_saved_events_user_id
    ON app.saved_events (user_id);

-- ── Alert Rules ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS app.alert_rules (
    alert_rule_id   BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES app.users(user_id) ON DELETE CASCADE,
    name            TEXT   NOT NULL,                 -- human-readable rule name
    min_magnitude   FLOAT,                           -- trigger when mag >= this
    max_depth_km    FLOAT,                           -- trigger when depth <= this
    region          TEXT,                             -- optional place/region keyword filter
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_app_alert_rules_user_id
    ON app.alert_rules (user_id);
