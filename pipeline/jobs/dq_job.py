from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from pipeline.dq.checks import DEFAULT_DQ_CHECKS, IDQCheck
from pipeline.dq.thresholds import DQIssue, DQThresholds
from pipeline.protocols.job import BaseJob
from pipeline.warehouse.base import IDQRepository


@dataclass(frozen=True)
class DataQualityJob(BaseJob):
    """
    Runs Data Quality checks for events in a time window.
    Stores dq_run, dq_issue, and dq_metric records.
    Returns run_id.

    Pattern:
      - BaseJob (Template Method).
      - IDQRepository (Repository) — decoupled from concrete Postgres impl.
      - Chain of Responsibility — each IDQCheck is a single focused rule;
        inject custom checks for environment-specific overrides.
      - DQThresholds (Value Object) — configurable, immutable thresholds.
    """
    repo: IDQRepository
    checks: tuple[IDQCheck, ...] = field(default_factory=lambda: DEFAULT_DQ_CHECKS)
    thresholds: DQThresholds = field(default_factory=DQThresholds)

    def run(self, *, window_start: datetime, window_end: datetime) -> int:
        """Runs all DQ checks and persists results. Returns run_id."""
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)
        if window_end.tzinfo is None:
            window_end = window_end.replace(tzinfo=timezone.utc)

        with self.repo.connection() as conn:
            # 1) Fetch aggregated stats from ODS
            stats = self.repo.fetch_dq_stats(
                window_start=window_start,
                window_end=window_end,
                conn=conn,
            )

            # 2) Run Chain of Responsibility — collect all issues
            issues: list[DQIssue] = []
            for check in self.checks:
                issues.extend(check.check(stats, self.thresholds))

            # 3) Build metrics dict from stats
            metrics: dict[str, float] = {
                "ods_rows": float(stats.total_rows),
                "pct_missing_geo": stats.pct_missing_geo,
                "pct_missing_mag": stats.pct_missing_mag,
                "pct_missing_sig": stats.pct_missing_sig,
                "pct_with_alert": stats.pct_with_alert,
                "pct_with_mmi": stats.pct_with_mmi,
                "avg_update_delay_min": stats.avg_update_delay_min,
                "avg_ingest_lag_min": stats.avg_ingest_lag_min,
                "max_ingest_lag_min": stats.max_ingest_lag_min,
            }
            if stats.max_event_time is not None:
                now_utc = datetime.now(timezone.utc)
                metrics["freshness_lag_min"] = (
                    now_utc - stats.max_event_time
                ).total_seconds() / 60.0
            else:
                metrics["freshness_lag_min"] = float("nan")

            # 4) Determine overall status
            status = "PASS" if not any(i.severity == "ERROR" for i in issues) else "FAIL"

            # 5) Persist results
            issues_as_dicts = [
                {
                    "issue_type": i.issue_type,
                    "severity": i.severity,
                    "message": i.message,
                    "sample_ids": i.sample_ids,
                }
                for i in issues
            ]

            run_id = self.repo.create_dq_run(
                window_start=window_start,
                window_end=window_end,
                status=status,
                total_rows=stats.total_rows,
                issues_count=len(issues),
                conn=conn,
            )
            self.repo.insert_dq_issues(run_id=run_id, issues=issues_as_dicts, conn=conn)
            self.repo.insert_dq_metrics(run_id=run_id, metrics=metrics, conn=conn)

        return run_id

    def _execute(self, **kwargs):
        return self.run(**kwargs)