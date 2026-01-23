CREATE SCHEMA IF NOT EXISTS dq;

CREATE TABLE IF NOT EXISTS dq.dq_run (
  run_id BIGSERIAL PRIMARY KEY,
  run_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  window_start TIMESTAMPTZ NOT NULL,
  window_end   TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL, -- PASS/FAIL
  total_rows INTEGER NOT NULL,
  issues_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dq.dq_issue (
  issue_id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL REFERENCES dq.dq_run(run_id) ON DELETE CASCADE,
  issue_type TEXT NOT NULL,
  severity TEXT NOT NULL, -- WARN/ERROR
  message TEXT NOT NULL,
  sample_ids TEXT[] NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dq.dq_metric (
  metric_id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL REFERENCES dq.dq_run(run_id) ON DELETE CASCADE,

  metric_name TEXT NOT NULL,
  metric_value DOUBLE PRECISION NOT NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE(run_id, metric_name)
);

CREATE INDEX IF NOT EXISTS ix_dq_metric_run_id ON dq.dq_metric(run_id);
CREATE INDEX IF NOT EXISTS ix_dq_metric_name ON dq.dq_metric(metric_name);
CREATE INDEX IF NOT EXISTS ix_dq_issue_run_id ON dq.dq_issue(run_id);
