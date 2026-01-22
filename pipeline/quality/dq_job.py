from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pipeline.config.pg_settings import PostgresSettings
from pipeline.warehouse.pg import PostgresRepository


@dataclass(frozen=True)
class DataQualityJob:
    repo: PostgresRepository

    def run(self, *, window_start: datetime, window_end: datetime) -> int:
        """
        Runs DQ checks for events in [window_start, window_end).
        Writes dq_run and dq_issue.
        Returns run_id.
        """
        issues: list[dict] = []

        with self.repo.connection() as conn:
            total_row = self.repo.query_one(
                """
                SELECT COUNT(*)
                FROM ods.fct_earthquake_event
                WHERE time >= %s AND time < %s;
                """,
                (window_start, window_end),
                conn=conn
            )
            total_rows = int(total_row[0]) if total_row else 0

            bad_geo_rows: list[tuple] = self.repo.query_all(
                """
                SELECT id
                FROM ods.fct_earthquake_event
                WHERE time >= %s AND time < %s
                    AND (
                        latitude IS NULL OR longitude IS NULL
                        OR latitude < -90 OR latitude > 90
                        OR longitude < -180 OR longitude > 180
                    )
                """,
                (window_start, window_end),
                conn=conn
            )
            bad_geo = [elem[0] for elem in bad_geo_rows]
            if bad_geo:
                issues.append(
                    {
                        "issue_type": "INVALID_GEO",
                        "severity": "ERROR",
                        "message": "Found events with invalid latitude/longitude in the window.",
                        "sample_ids": bad_geo,
                    }
                )

            bad_updated_rows = self.repo.query_all(
                """
                SELECT id
                FROM ods.fct_earthquake_event
                WHERE time >= %s AND time < %s
                    AND updated < time;
                """,
                (window_start, window_end),
                conn=conn
            )
            bad_updated = [elem[0] for elem in bad_updated_rows]
            if bad_updated:
                issues.append(
                    {
                        "issue_type": "UPDATED_BEFORE_TIME",
                        "severity": "WARN",
                        "message": "Some events have updated < time.",
                        "sample_ids": bad_updated,
                    }
                )

            duplicate_rows = self.repo.query_all(
                """
                SELECT id
                FROM (
                    SELECT id, COUNT(*) c
                    FROM ods.fct_earthquake_event
                    WHERE time >= %s AND time < %s
                    GROUP BY id
                    HAVING count(*) > 1
                ) t
                """,
                (window_start, window_end),
                conn=conn
            )
            duplicate_ids = [elem[0] for elem in duplicate_rows]
            if duplicate_ids:
                issues.append(
                    {
                        "issue_type": "DUPLICATE_ID",
                        "severity": "ERROR",
                        "message": "Duplicate IDs detected (should not happen with PK).",
                        "sample_ids": duplicate_ids,
                    }
                )

            status = "PASS" if not any(issue["severity"] == "ERROR" for issue in issues) else "FAIL"

            run_id = self.repo.create_dq_run(
                window_start=window_start,
                window_end=window_end,
                status=status,
                total_rows=total_rows,
                issues_count=len(issues),
                conn=conn,
            )
            self.repo.insert_dq_issues(run_id=run_id, issues=issues, conn=conn)

            return run_id