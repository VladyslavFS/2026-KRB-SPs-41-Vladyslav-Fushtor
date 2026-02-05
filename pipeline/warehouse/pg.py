from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2.extensions import connection as PGConnection
from psycopg2.extras import execute_values

from pipeline.config.pg_settings import PostgresSettings


class PostgresRepository:
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

    def upsert_earthquakes(self, rows: list[dict]) -> int:
        """
        UPSERT into ods.fct_earthquake_event.
        Only updates if excluded.updated > current.updated.
        Returns number of input rows (Postgres doesn't easily return affected count with execute_values).
        """
        if not rows:
            return 0
        
        cols = [
            "id",
            "time", "updated",
            "latitude", "longitude", "depth",
            "mag", "mag_type",
            "place", "event_type", "status", "net",
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
    
    def create_dq_run(
            self,
            *,
            window_start: datetime,
            window_end: datetime,
            status: str,
            total_rows: int,
            issues_count: int,
            conn: Optional[PGConnection] = None
        ) -> int:
        row = self.query_one(
            """
            INSERT INTO dq.dq_run (window_start, window_end, status, total_rows, issues_count)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING run_id;
            """,
            (window_start, window_end, status, total_rows, issues_count),
            conn=conn
        )
        if row is None:
            raise RuntimeError("Failed to create dq_run (no run_id returned)")
        return int(row[0])
    
    def insert_dq_issues(self, *, run_id: int, issues: list[dict], conn: Optional[PGConnection] = None) -> None:
        if not issues:
            return
        cols = ["run_id", "issue_type", "severity", "message", "sample_ids"]
        values = [[run_id, i["issue_type"], i["severity"], i["message"], i.get("sample_ids")] for i in issues]
        sql = f"INSERT INTO dq.dq_issue ({', '.join(cols)}) VALUES %s"

        if conn is None:
            with self.connection() as c:
                self.insert_dq_issues(run_id=run_id, issues=issues, conn=c)
                return

        with conn.cursor() as cur:
            execute_values(cur, sql, values, page_size=1000)

    def insert_dq_metrics(self, *, run_id: int, metrics: dict[str, float], conn=None) -> None:
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
