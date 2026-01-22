CREATE TABLE IF NOT EXISTS ods.dq_run (
  run_id BIGSERIAL PRIMARY KEY,
  run_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  window_start TIMESTAMPTZ NOT NULL,
  window_end   TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL, -- PASS/FAIL
  total_rows INTEGER NOT NULL,
  issues_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ods.dq_issue (
  issue_id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL REFERENCES ods.dq_run(run_id) ON DELETE CASCADE,
  issue_type TEXT NOT NULL,
  severity TEXT NOT NULL, -- WARN/ERROR
  message TEXT NOT NULL,
  sample_ids TEXT[] NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_dq_issue_run_id ON ods.dq_issue(run_id);
