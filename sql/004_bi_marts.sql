CREATE SCHEMA IF NOT EXISTS bi;

CREATE TABLE IF NOT EXISTS bi.event_feed AS
SELECT
  id AS event_id,
  time,
  updated,
  ingested_at,
  latitude,
  longitude,
  depth,
  mag,
  mag_type,
  place,
  net,
  status,
  event_type,
  tsunami,
  url,
  detail,

  CASE
    WHEN mag IS NULL THEN 'unknown'
    WHEN mag < 2 THEN 'lt2'
    WHEN mag < 3 THEN '2_3'
    WHEN mag < 4 THEN '3_4'
    WHEN mag < 5 THEN '4_5'
    WHEN mag < 6 THEN '5_6'
    ELSE 'ge6'
  END AS mag_bucket,

  CASE
    WHEN depth IS NULL THEN 'unknown'
    WHEN depth < 10 THEN '0_10'
    WHEN depth < 30 THEN '10_30'
    WHEN depth < 70 THEN '30_70'
    WHEN depth < 300 THEN '70_300'
    ELSE 'ge300'
  END AS depth_bucket,

  CASE
    WHEN mag IS NULL THEN 'UNKNOWN'
    WHEN mag >= 6 THEN 'HIGH'
    WHEN mag >= 4 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS severity

FROM ods.fct_earthquake_event;


TRUNCATE bi.event_feed;
INSERT INTO bi.event_feed
SELECT
  id AS event_id,
  time,
  updated,
  ingested_at,
  latitude,
  longitude,
  depth,
  mag,
  mag_type,
  place,
  net,
  status,
  event_type,
  tsunami,
  url,
  detail,

  CASE
    WHEN mag IS NULL THEN 'unknown'
    WHEN mag < 2 THEN 'lt2'
    WHEN mag < 3 THEN '2_3'
    WHEN mag < 4 THEN '3_4'
    WHEN mag < 5 THEN '4_5'
    WHEN mag < 6 THEN '5_6'
    ELSE 'ge6'
  END AS mag_bucket,

  CASE
    WHEN depth IS NULL THEN 'unknown'
    WHEN depth < 10 THEN '0_10'
    WHEN depth < 30 THEN '10_30'
    WHEN depth < 70 THEN '30_70'
    WHEN depth < 300 THEN '70_300'
    ELSE 'ge300'
  END AS depth_bucket,

  CASE
    WHEN mag IS NULL THEN 'UNKNOWN'
    WHEN mag >= 6 THEN 'HIGH'
    WHEN mag >= 4 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS severity
FROM ods.fct_earthquake_event;

CREATE INDEX IF NOT EXISTS ix_bi_event_feed_time ON bi.event_feed(time DESC);
CREATE INDEX IF NOT EXISTS ix_bi_event_feed_mag ON bi.event_feed(mag);
CREATE INDEX IF NOT EXISTS ix_bi_event_feed_severity ON bi.event_feed(severity);

-- 2) top_events_daily
CREATE TABLE IF NOT EXISTS bi.top_events_daily (
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

TRUNCATE bi.top_events_daily;

INSERT INTO bi.top_events_daily
SELECT
  (time AT TIME ZONE 'UTC')::date AS day,
  rank,
  event_id,
  time,
  mag,
  depth,
  place,
  latitude,
  longitude,
  tsunami,
  url,
  net,
  status
FROM (
  SELECT
    event_id,
    time,
    mag,
    depth,
    place,
    latitude,
    longitude,
    tsunami,
    url,
    net,
    status,
    ROW_NUMBER() OVER (
      PARTITION BY (time AT TIME ZONE 'UTC')::date
      ORDER BY mag DESC NULLS LAST, time DESC
    ) AS rank
  FROM bi.event_feed
  WHERE mag IS NOT NULL
) t
WHERE rank <= 10;

CREATE INDEX IF NOT EXISTS ix_bi_top_events_day ON bi.top_events_daily(day DESC);

-- 3) catalog_health_daily
CREATE TABLE IF NOT EXISTS bi.catalog_health_daily (
  day DATE PRIMARY KEY,

  events_cnt INTEGER NOT NULL,
  tsunami_cnt INTEGER NOT NULL,
  max_mag DOUBLE PRECISION,

  pct_missing_geo DOUBLE PRECISION NOT NULL,
  pct_missing_mag DOUBLE PRECISION NOT NULL,

  avg_update_delay_min DOUBLE PRECISION,
  p95_update_delay_min DOUBLE PRECISION,

  avg_ingest_lag_min DOUBLE PRECISION,
  max_ingest_lag_min DOUBLE PRECISION,

  dq_last_status TEXT,
  dq_last_run_at TIMESTAMPTZ,
  dq_last_issues_count INTEGER
);

TRUNCATE bi.catalog_health_daily;

INSERT INTO bi.catalog_health_daily
WITH base AS (
  SELECT
    (time AT TIME ZONE 'UTC')::date AS day,
    COUNT(*) AS events_cnt,
    COUNT(*) FILTER (WHERE tsunami = 1) AS tsunami_cnt,
    MAX(mag) AS max_mag,

    AVG(CASE WHEN latitude IS NULL OR longitude IS NULL THEN 1.0 ELSE 0.0 END) AS pct_missing_geo,
    AVG(CASE WHEN mag IS NULL THEN 1.0 ELSE 0.0 END) AS pct_missing_mag,

    AVG(EXTRACT(EPOCH FROM (updated - time)) / 60.0) AS avg_update_delay_min,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY (EXTRACT(EPOCH FROM (updated - time)) / 60.0)) AS p95_update_delay_min,

    AVG(EXTRACT(EPOCH FROM (ingested_at - time)) / 60.0) AS avg_ingest_lag_min,
    MAX(EXTRACT(EPOCH FROM (ingested_at - time)) / 60.0) AS max_ingest_lag_min
  FROM bi.event_feed
  GROUP BY 1
),
dq_last AS (
  SELECT DISTINCT ON ((window_start AT TIME ZONE 'UTC')::date)
    (window_start AT TIME ZONE 'UTC')::date AS day,
    status AS dq_last_status,
    run_at  AS dq_last_run_at,
    issues_count AS dq_last_issues_count
  FROM dq.dq_run
  ORDER BY (window_start AT TIME ZONE 'UTC')::date, run_at DESC
)
SELECT
  b.day,
  b.events_cnt,
  b.tsunami_cnt,
  b.max_mag,
  b.pct_missing_geo,
  b.pct_missing_mag,
  b.avg_update_delay_min,
  b.p95_update_delay_min,
  b.avg_ingest_lag_min,
  b.max_ingest_lag_min,
  d.dq_last_status,
  d.dq_last_run_at,
  d.dq_last_issues_count
FROM base b
LEFT JOIN dq_last d ON d.day = b.day
ORDER BY b.day DESC;

CREATE INDEX IF NOT EXISTS ix_bi_catalog_health_day ON bi.catalog_health_daily(day DESC);
