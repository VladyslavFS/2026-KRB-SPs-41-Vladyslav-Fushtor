CREATE SCHEMA IF NOT EXISTS ods;

CREATE TABLE IF NOT EXISTS ods.fct_earthquake_event (
  id TEXT PRIMARY KEY,

  time TIMESTAMPTZ NOT NULL,
  updated TIMESTAMPTZ NOT NULL,

  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  depth DOUBLE PRECISION,

  mag DOUBLE PRECISION,
  mag_type TEXT,

  place TEXT,
  event_type TEXT,
  status TEXT,
  net TEXT,

  url TEXT,
  detail TEXT,
  tsunami INTEGER,

  source_window_start TIMESTAMPTZ NOT NULL,
  source_window_end   TIMESTAMPTZ NOT NULL,
  ingested_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_earthquake_time ON ods.fct_earthquake_event (time);
CREATE INDEX IF NOT EXISTS ix_earthquake_mag  ON ods.fct_earthquake_event (mag);
CREATE INDEX IF NOT EXISTS ix_earthquake_updated ON ods.fct_earthquake_event (updated);
