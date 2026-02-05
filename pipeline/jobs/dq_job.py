from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from pipeline.warehouse.pg import PostgresRepository


@dataclass(frozen=True)
class DataQualityJob:
    repo: PostgresRepository

    def run(self, *, window_start: datetime, window_end: datetime) -> int:
        """
        Runs DQ checks for events in [window_start, window_end).
        Stores dq_run, dq_issue and dq_metric.
        Returns run_id.
        """
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)
        if window_end.tzinfo is None:
            window_end = window_end.replace(tzinfo=timezone.utc)

        issues: list[dict] = []

        # Thresholds
        WARN_INGEST_LAG_MIN = 180.0   # 3h
        ERROR_INGEST_LAG_MIN = 720.0  # 12h

        WARN_PCT_MISSING_GEO = 0.01   # 1%
        ERROR_PCT_MISSING_GEO = 0.10  # 10%

        WARN_PCT_MISSING_MAG = 0.20   # 20%
        ERROR_PCT_MISSING_MAG = 0.60  # 60%

        # Sanity bounds
        MAX_VALID_MAG = 10.0
        MIN_VALID_MAG = -2.0

        with self.repo.connection() as conn:
            row = self.repo.query_one(
                """
                SELECT
                  COUNT(*)::int AS total_rows,

                  AVG(CASE WHEN latitude IS NULL OR longitude IS NULL THEN 1.0 ELSE 0.0 END) AS pct_missing_geo,
                  AVG(CASE WHEN mag IS NULL THEN 1.0 ELSE 0.0 END) AS pct_missing_mag,
                  
                  -- New fields stats
                  AVG(CASE WHEN alert IS NOT NULL THEN 1.0 ELSE 0.0 END) AS pct_with_alert,
                  AVG(CASE WHEN mmi IS NOT NULL THEN 1.0 ELSE 0.0 END) AS pct_with_mmi,
                  AVG(CASE WHEN sig IS NULL THEN 1.0 ELSE 0.0 END) AS pct_missing_sig,

                  -- Sanity checks aggregates
                  MIN(mag) as min_mag,
                  MAX(mag) as max_mag,
                  MIN(sig) as min_sig,

                  -- Timeliness
                  AVG(EXTRACT(EPOCH FROM (updated - time)) / 60.0) AS avg_update_delay_min,
                  AVG(EXTRACT(EPOCH FROM (ingested_at - time)) / 60.0) AS avg_ingest_lag_min,
                  MAX(EXTRACT(EPOCH FROM (ingested_at - time)) / 60.0) AS max_ingest_lag_min,

                  MAX(time) AS max_event_time
                FROM ods.fct_earthquake_event
                WHERE time >= %s AND time < %s;
                """,
                (window_start, window_end),
                conn=conn,
            )

            # Unpack safely (handle 0 rows -> None)
            total_rows = int(row[0]) if row and row[0] is not None else 0
            
            # Helper to safe float
            def f(x): return float(x) if x is not None else 0.0

            pct_missing_geo = f(row[1])
            pct_missing_mag = f(row[2])
            pct_with_alert = f(row[3])
            pct_with_mmi = f(row[4])
            pct_missing_sig = f(row[5])
            
            val_min_mag = row[6] # can be None
            val_max_mag = row[7]
            val_min_sig = row[8]

            avg_update_delay_min = f(row[9])
            avg_ingest_lag_min = f(row[10])
            max_ingest_lag_min = f(row[11])
            max_event_time = row[12]

            metrics = {
                "ods_rows": float(total_rows),
                "pct_missing_geo": pct_missing_geo,
                "pct_missing_mag": pct_missing_mag,
                "pct_missing_sig": pct_missing_sig,
                "pct_with_alert": pct_with_alert,
                "pct_with_mmi": pct_with_mmi,
                "avg_update_delay_min": avg_update_delay_min,
                "avg_ingest_lag_min": avg_ingest_lag_min,
                "max_ingest_lag_min": max_ingest_lag_min,
            }

            if max_event_time is not None:
                now_utc = datetime.now(timezone.utc)
                freshness_lag_min = (now_utc - max_event_time).total_seconds() / 60.0
                metrics["freshness_lag_min"] = float(freshness_lag_min)
            else:
                metrics["freshness_lag_min"] = float("nan")

            # ---- Checks ----

            # 1) Empty window
            if total_rows == 0:
                issues.append({
                    "issue_type": "EMPTY_WINDOW",
                    "severity": "WARN",
                    "message": "No events found in the window.",
                    "sample_ids": None,
                })

            # 2) Mag Sanity
            if val_max_mag is not None and val_max_mag > MAX_VALID_MAG:
                issues.append({
                    "issue_type": "INVALID_MAGNITUDE",
                    "severity": "ERROR",
                    "message": f"Found magnitude > {MAX_VALID_MAG} (max={val_max_mag}). Possible data error.",
                    "sample_ids": None
                })
            
            if val_min_mag is not None and val_min_mag < MIN_VALID_MAG:
                 issues.append({
                    "issue_type": "INVALID_MAGNITUDE",
                    "severity": "WARN",
                    "message": f"Found magnitude < {MIN_VALID_MAG} (min={val_min_mag}). Unusual but possible.",
                    "sample_ids": None
                })

            # 3) Sig Sanity
            if val_min_sig is not None and val_min_sig < 0:
                 issues.append({
                    "issue_type": "INVALID_SIGNIFICANCE",
                    "severity": "ERROR",
                    "message": f"Found negative significance (min={val_min_sig}).",
                    "sample_ids": None
                })

            # 4) Ingest lag SLA
            if avg_ingest_lag_min >= ERROR_INGEST_LAG_MIN:
                issues.append({
                    "issue_type": "INGEST_LAG_SLA",
                    "severity": "ERROR",
                    "message": f"Avg ingest lag: {avg_ingest_lag_min:.1f} min (>= {ERROR_INGEST_LAG_MIN}).",
                    "sample_ids": None,
                })
            elif avg_ingest_lag_min >= WARN_INGEST_LAG_MIN:
                issues.append({
                    "issue_type": "INGEST_LAG_SLA",
                    "severity": "WARN",
                    "message": f"Avg ingest lag high: {avg_ingest_lag_min:.1f} min (>= {WARN_INGEST_LAG_MIN}).",
                    "sample_ids": None,
                })

            # 5) Missingness guards
            if pct_missing_geo >= ERROR_PCT_MISSING_GEO:
                issues.append({
                    "issue_type": "MISSING_GEO",
                    "severity": "ERROR",
                    "message": f"Missing geo: {pct_missing_geo*100:.2f}% (>= {ERROR_PCT_MISSING_GEO*100:.0f}%).",
                    "sample_ids": None,
                })
            elif pct_missing_geo >= WARN_PCT_MISSING_GEO:
                issues.append({
                    "issue_type": "MISSING_GEO",
                    "severity": "WARN",
                    "message": f"Missing geo: {pct_missing_geo*100:.2f}% (>= {WARN_PCT_MISSING_GEO*100:.0f}%).",
                    "sample_ids": None,
                })

            # FIX: Added missing WARN check
            if pct_missing_mag >= ERROR_PCT_MISSING_MAG:
                issues.append({
                    "issue_type": "MISSING_MAG",
                    "severity": "ERROR",
                    "message": f"Missing mag: {pct_missing_mag*100:.2f}% (>= {ERROR_PCT_MISSING_MAG*100:.0f}%).",
                    "sample_ids": None,
                })
            elif pct_missing_mag >= WARN_PCT_MISSING_MAG:
                issues.append({
                    "issue_type": "MISSING_MAG",
                    "severity": "WARN",
                    "message": f"Missing mag: {pct_missing_mag*100:.2f}% (>= {WARN_PCT_MISSING_MAG*100:.0f}%).",
                    "sample_ids": None,
                })

            status = "PASS" if not any(i["severity"] == "ERROR" for i in issues) else "FAIL"

            run_id = self.repo.create_dq_run(
                window_start=window_start,
                window_end=window_end,
                status=status,
                total_rows=total_rows,
                issues_count=len(issues),
                conn=conn,
            )

            self.repo.insert_dq_issues(run_id=run_id, issues=issues, conn=conn)
            self.repo.insert_dq_metrics(run_id=run_id, metrics=metrics, conn=conn)

            return run_id