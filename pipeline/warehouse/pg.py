from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import pandas as pd
import psycopg2
from psycopg2.extensions import connection as PGConnection
from psycopg2.extras import execute_values

from pipeline.config.pg_settings import PostgresSettings
from pipeline.dq.thresholds import DQStats
from pipeline.warehouse.base import IDQRepository, IEventRepository


class PostgresRepository(IEventRepository, IDQRepository):
    """
    Concrete Postgres implementation of IEventRepository + IDQRepository.

    Pattern: Repository — encapsulates all SQL; callers depend on interfaces.
    Connection management via context manager (commit on success, rollback on error).

    Note: Both interfaces are implemented here because they share the same
    connection pool and settings. For independent scaling, split into
    PostgresEventRepository + PostgresDQRepository with a shared base mixin.
    """

    def __init__(self, settings: PostgresSettings):
        self._settings = settings

    def _conn(self) -> PGConnection:
        return psycopg2.connect(
            host=self._settings.host,
            port=self._settings.port,
            dbname=self._settings.db,
            user=self._settings.user,
            password=self._settings.password,
        )

    @contextmanager
    def connection(self):
        conn = self._conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ── Generic helpers ────────────────────────────────────────────────────────

    def query_one(self, sql: str, values: tuple = (), *, conn: Optional[PGConnection] = None) -> tuple | None:
        if conn is None:
            with self.connection() as c:
                return self.query_one(sql, values, conn=c)
        with conn.cursor() as cur:
            cur.execute(sql, values)
            return cur.fetchone()

    def query_all(self, sql: str, values: tuple = (), *, conn: Optional[PGConnection] = None) -> list[tuple]:
        if conn is None:
            with self.connection() as c:
                return self.query_all(sql, values, conn=c)
        with conn.cursor() as cur:
            cur.execute(sql, values)
            return cur.fetchall()

    def execute(self, sql: str, values: tuple = (), *, conn: Optional[PGConnection] = None) -> None:
        if conn is None:
            with self.connection() as c:
                self.execute(sql, values, conn=c)
                return
        with conn.cursor() as cur:
            cur.execute(sql, values)

    # ── IEventRepository ───────────────────────────────────────────────────────

    def upsert_earthquakes(self, rows: list[dict]) -> int:
        """
        UPSERT into ods.fct_earthquake_event.
        Only updates if excluded.updated > current.updated.
        Returns number of input rows.
        """
        if not rows:
            return 0

        cols = [
            "id",
            "time", "updated",
            "latitude", "longitude", "depth",
            "mag", "mag_type",
            "place", "country", "risk_class", "event_type", "status", "net",
            "url", "detail", "tsunami",
            "alert", "sig", "felt", "mmi", "nst", "gap", "mag_error",
            "source_window_start", "source_window_end",
        ]

        values = [[row.get(col) for col in cols] for row in rows]

        sql = f"""
        INSERT INTO ods.fct_earthquake_event ({", ".join(cols)})
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
          time = EXCLUDED.time,
          updated = EXCLUDED.updated,
          latitude = EXCLUDED.latitude,
          longitude = EXCLUDED.longitude,
          depth = EXCLUDED.depth,
          mag = EXCLUDED.mag,
          mag_type = EXCLUDED.mag_type,
          place = EXCLUDED.place,
          country = EXCLUDED.country,
          risk_class = EXCLUDED.risk_class,
          event_type = EXCLUDED.event_type,
          status = EXCLUDED.status,
          net = EXCLUDED.net,
          url = EXCLUDED.url,
          detail = EXCLUDED.detail,
          tsunami = EXCLUDED.tsunami,
          alert = EXCLUDED.alert,
          sig = EXCLUDED.sig,
          felt = EXCLUDED.felt,
          mmi = EXCLUDED.mmi,
          nst = EXCLUDED.nst,
          gap = EXCLUDED.gap,
          mag_error = EXCLUDED.mag_error,
          source_window_start = EXCLUDED.source_window_start,
          source_window_end = EXCLUDED.source_window_end,
          ingested_at = now()
        WHERE ods.fct_earthquake_event.updated < EXCLUDED.updated;
        """

        with self.connection() as conn:
            with conn.cursor() as cursor:
                execute_values(cursor, sql, values, page_size=2000)

        return len(rows)

    def insert_df(
        self,
        *,
        conn,
        table: str,
        df: pd.DataFrame,
        on_conflict: str | None = None,
    ) -> None:
        """Generic bulk insert for pandas DataFrame. Columns must match table."""
        if df.empty:
            return

        df_obj = df.astype(object)
        df_clean = df_obj.where(pd.notnull(df_obj), None)

        columns = list(df_clean.columns)
        values = [tuple(x) for x in df_clean.to_numpy()]

        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s"
        if on_conflict:
            sql += f" {on_conflict}"

        with conn.cursor() as cur:
            execute_values(cur, sql, values, page_size=1000)

    # ── IDQRepository ──────────────────────────────────────────────────────────

    def fetch_dq_stats(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        conn: Optional[PGConnection] = None,
    ) -> DQStats:
        """Query ODS and return aggregated DQ statistics for a time window."""
        row = self.query_one(
            """
            SELECT
              COUNT(*)::int AS total_rows,
              AVG(CASE WHEN latitude IS NULL OR longitude IS NULL THEN 1.0 ELSE 0.0 END) AS pct_missing_geo,
              AVG(CASE WHEN mag IS NULL THEN 1.0 ELSE 0.0 END) AS pct_missing_mag,
              AVG(CASE WHEN alert IS NOT NULL THEN 1.0 ELSE 0.0 END) AS pct_with_alert,
              AVG(CASE WHEN mmi IS NOT NULL THEN 1.0 ELSE 0.0 END) AS pct_with_mmi,
              AVG(CASE WHEN sig IS NULL THEN 1.0 ELSE 0.0 END) AS pct_missing_sig,
              MIN(mag) as min_mag,
              MAX(mag) as max_mag,
              MIN(sig) as min_sig,
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

        def _f(x) -> float:
            return float(x) if x is not None else 0.0

        total_rows = int(row[0]) if row and row[0] is not None else 0
        return DQStats(
            total_rows=total_rows,
            pct_missing_geo=_f(row[1]),
            pct_missing_mag=_f(row[2]),
            pct_with_alert=_f(row[3]),
            pct_with_mmi=_f(row[4]),
            pct_missing_sig=_f(row[5]),
            val_min_mag=row[6],
            val_max_mag=row[7],
            val_min_sig=row[8],
            avg_update_delay_min=_f(row[9]),
            avg_ingest_lag_min=_f(row[10]),
            max_ingest_lag_min=_f(row[11]),
            max_event_time=row[12],
        )

    def create_dq_run(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        status: str,
        total_rows: int,
        issues_count: int,
        conn: Optional[PGConnection] = None,
    ) -> int:
        row = self.query_one(
            """
            INSERT INTO dq.dq_run (window_start, window_end, status, total_rows, issues_count)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING run_id;
            """,
            (window_start, window_end, status, total_rows, issues_count),
            conn=conn,
        )
        if row is None:
            raise RuntimeError("Failed to create dq_run (no run_id returned)")
        return int(row[0])

    def insert_dq_issues(
        self,
        *,
        run_id: int,
        issues: list[dict],
        conn: Optional[PGConnection] = None,
    ) -> None:
        if not issues:
            return
        cols = ["run_id", "issue_type", "severity", "message", "sample_ids"]
        values = [
            [run_id, i["issue_type"], i["severity"], i["message"], i.get("sample_ids")]
            for i in issues
        ]
        sql = f"INSERT INTO dq.dq_issue ({', '.join(cols)}) VALUES %s"

        if conn is None:
            with self.connection() as c:
                self.insert_dq_issues(run_id=run_id, issues=issues, conn=c)
                return

        with conn.cursor() as cur:
            execute_values(cur, sql, values, page_size=1000)

    def insert_dq_metrics(
        self,
        *,
        run_id: int,
        metrics: dict[str, float],
        conn=None,
    ) -> None:
        if not metrics:
            return

        cols = ["run_id", "metric_name", "metric_value"]
        values = [[run_id, k, float(v)] for k, v in metrics.items()]

        sql = f"""
        INSERT INTO dq.dq_metric ({", ".join(cols)})
        VALUES %s
        ON CONFLICT (run_id, metric_name) DO UPDATE
        SET metric_value = EXCLUDED.metric_value,
            created_at = now();
        """

        if conn is None:
            with self.connection() as c:
                self.insert_dq_metrics(run_id=run_id, metrics=metrics, conn=c)
                return

        with conn.cursor() as cur:
            execute_values(cur, sql, values, page_size=1000)