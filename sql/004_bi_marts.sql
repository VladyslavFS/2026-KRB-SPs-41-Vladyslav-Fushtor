CREATE SCHEMA IF NOT EXISTS bi;

DROP TABLE IF EXISTS bi.event_feed;
DROP TABLE IF EXISTS bi.top_events_daily;
DROP TABLE IF EXISTS bi.catalog_health_daily;

CREATE TABLE bi.event_feed (
    event_id TEXT PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    depth DOUBLE PRECISION,
    mag DOUBLE PRECISION,
    mag_type TEXT,
    place TEXT,
    net TEXT,
    status TEXT,
    event_type TEXT,
    tsunami INTEGER,
    url TEXT,
    detail TEXT,
    alert TEXT,
    sig INTEGER,
    felt INTEGER,
    mmi DOUBLE PRECISION,
    nst INTEGER,
    gap DOUBLE PRECISION,
    mag_error DOUBLE PRECISION,

    mag_bucket TEXT,
    depth_bucket TEXT,
    severity TEXT
);

CREATE INDEX ix_bi_event_feed_time ON bi.event_feed(time DESC);
CREATE INDEX ix_bi_event_feed_mag ON bi.event_feed(mag);
CREATE INDEX ix_bi_event_feed_severity ON bi.event_feed(severity);

CREATE TABLE bi.top_events_daily (
    day DATE NOT NULL,
    rank INTEGER NOT NULL,
    event_id TEXT NOT NULL,
    time TIMESTAMPTZ NOT NULL,
    mag DOUBLE PRECISION,
    depth DOUBLE PRECISION,
    place TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    tsunami INTEGER,
    url TEXT,
    net TEXT,
    status TEXT,
    PRIMARY KEY(day, rank)
);

CREATE TABLE bi.catalog_health_daily (
    day DATE PRIMARY KEY,
    events_cnt INTEGER,
    tsunami_cnt INTEGER,
    max_mag DOUBLE PRECISION,
    pct_missing_geo DOUBLE PRECISION,
    pct_missing_mag DOUBLE PRECISION,
    avg_update_delay_min DOUBLE PRECISION,
    p95_update_delay_min DOUBLE PRECISION,
    avg_ingest_lag_min DOUBLE PRECISION,
    max_ingest_lag_min DOUBLE PRECISION,
    dq_last_status TEXT,
    dq_last_run_at TIMESTAMPTZ,
    dq_last_issues_count INTEGER
);