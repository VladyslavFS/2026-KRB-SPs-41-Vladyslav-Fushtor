from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from pipeline.protocols.job import BaseJob
from pipeline.storage.storage import ObjectStorage
from pipeline.utils.date_utils import daterange
from pipeline.warehouse.base import IEventRepository


@dataclass(frozen=True)
class ExportBIToParquetJob(BaseJob):
    """
    Exports BI marts from Postgres to S3/MinIO as Parquet files (Gold layer),
    partitioned by dt=YYYY-MM-DD.

    Tables:
      - bi.event_feed (partitioned by time UTC date)
      - bi.top_events_daily (partitioned by day)
      - bi.catalog_health_daily (partitioned by day)

    Output keys:
      gold/bi/<table_name>/dt=YYYY-MM-DD/part-<run_ts>.parquet

    Pattern:
      - BaseJob (Template Method).
      - IEventRepository (Repository).
      - ObjectStorage (Strategy).
      - daterange from shared utils (DRY).
    """
    repo: IEventRepository
    storage: ObjectStorage
    bucket: str

    def run(self, *, days: int) -> dict[str, int]:
        if days <= 0:
            raise ValueError("days must be > 0")

        today = datetime.now(timezone.utc).date()
        start_day = today - timedelta(days=days - 1)
        end_day_excl = today + timedelta(days=1)
        run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        counts = {"event_feed": 0, "top_events_daily": 0, "catalog_health_daily": 0}

        with self.repo.connection() as conn:
            for d in daterange(start_day, end_day_excl):
                counts["event_feed"] += self._export_event_feed_day(conn=conn, d=d, run_ts=run_ts)
                counts["top_events_daily"] += self._export_top_events_day(conn=conn, d=d, run_ts=run_ts)
                counts["catalog_health_daily"] += self._export_catalog_health_day(conn=conn, d=d, run_ts=run_ts)

        return counts

    def _export_event_feed_day(self, *, conn, d: date, run_ts: str) -> int:
        start_dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)

        df = pd.read_sql(
            """
            SELECT event_id, time, updated, ingested_at, latitude, longitude, depth,
                   mag, mag_type, place, net, status, event_type, tsunami, url, detail,
                   mag_bucket, depth_bucket, severity
            FROM bi.event_feed
            WHERE time >= %s AND time < %s
            ORDER BY time DESC;
            """,
            conn,
            params=(start_dt, end_dt),
        )
        return self._write_partition(table_name="event_feed", dt=d, df=df, run_ts=run_ts)

    def _export_top_events_day(self, *, conn, d: date, run_ts: str) -> int:
        df = pd.read_sql(
            """
            SELECT day, rank, event_id, time, mag, depth, place,
                   latitude, longitude, tsunami, url, net, status
            FROM bi.top_events_daily
            WHERE day = %s
            ORDER BY rank ASC;
            """,
            conn,
            params=(d,),
        )
        return self._write_partition(table_name="top_events_daily", dt=d, df=df, run_ts=run_ts)

    def _export_catalog_health_day(self, *, conn, d: date, run_ts: str) -> int:
        df = pd.read_sql(
            """
            SELECT day, events_cnt, tsunami_cnt, max_mag, pct_missing_geo, pct_missing_mag,
                   avg_update_delay_min, p95_update_delay_min, avg_ingest_lag_min,
                   max_ingest_lag_min, dq_last_status, dq_last_run_at, dq_last_issues_count
            FROM bi.catalog_health_daily
            WHERE day = %s;
            """,
            conn,
            params=(d,),
        )
        return self._write_partition(table_name="catalog_health_daily", dt=d, df=df, run_ts=run_ts)

    def _write_partition(self, *, table_name: str, dt: date, df: pd.DataFrame, run_ts: str) -> int:
        if df.empty:
            return 0
        dt_str = dt.isoformat()
        key = f"gold/bi/{table_name}/dt={dt_str}/part-{run_ts}.parquet"
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, f"{table_name}_{dt_str}.parquet")
            df.to_parquet(local_path, index=False, engine="pyarrow")
            self.storage.upload_file(local_path=local_path, key=key, content_type="application/octet-stream")
        print(f"✅ exported {table_name} dt={dt_str}: rows={len(df)} -> s3://{self.bucket}/{key}")
        return int(len(df))

    def _execute(self, **kwargs):
        return self.run(**kwargs)
