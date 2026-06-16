CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.users (
    user_id         BIGSERIAL PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login      TIMESTAMPTZ,
    password_reset_token TEXT,
    password_reset_expires_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS app.refresh_tokens (
    refresh_token_id    BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES app.users(user_id) ON DELETE CASCADE,
    token_hash          TEXT NOT NULL UNIQUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at          TIMESTAMPTZ NOT NULL,
    revoked_at          TIMESTAMPTZ,
    replaced_by_hash    TEXT
);

CREATE INDEX IF NOT EXISTS ix_app_refresh_tokens_user_id ON app.refresh_tokens (user_id);
CREATE INDEX IF NOT EXISTS ix_app_refresh_tokens_expires_at ON app.refresh_tokens (expires_at);
