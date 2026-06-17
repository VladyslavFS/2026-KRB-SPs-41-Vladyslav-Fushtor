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
class BuildGoldJob(BaseJob):
    """
    Reads ODS (Postgres), computes BI marts in memory (Pandas),
    and writes Gold Parquet partitions to S3.

    Pattern:
      - BaseJob (Template Method).
      - IEventRepository (Repository).
      - ObjectStorage (Strategy).
      - daterange from shared utils (DRY — was duplicated in 3 files).
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
            dq_df = pd.read_sql(
                """
                SELECT DISTINCT ON ((window_start AT TIME ZONE 'UTC')::date)
                    (window_start AT TIME ZONE 'UTC')::date as day,
                    status as dq_last_status,
                    run_at as dq_last_run_at,
                    issues_count as dq_last_issues_count
                FROM dq.dq_run
                WHERE window_start >= %s AND window_start < %s
                ORDER BY (window_start AT TIME ZONE 'UTC')::date, run_at DESC
                """,
                conn,
                params=(start_day, end_day_excl),
            )
            dq_df["day"] = pd.to_datetime(dq_df["day"]).dt.date

            for d in daterange(start_day, end_day_excl):
                self._process_day(conn=conn, d=d, run_ts=run_ts, dq_df=dq_df, counts=counts)

        return counts

    def _process_day(self, *, conn, d: date, run_ts: str, dq_df: pd.DataFrame, counts: dict):
        start_dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)

        df = pd.read_sql(
            """
            SELECT
              id as event_id, time, updated, ingested_at,
              latitude, longitude, depth, mag, mag_type,
              place, net, status, event_type, tsunami, url, detail,
              alert, sig, felt, mmi, nst, gap, mag_error
            FROM ods.fct_earthquake_event
            WHERE time >= %s AND time < %s
            """,
            conn,
            params=(start_dt, end_dt),
        )

        if df.empty:
            return

        df["time"] = pd.to_datetime(df["time"], utc=True)
        df["updated"] = pd.to_datetime(df["updated"], utc=True)
        df["ingested_at"] = pd.to_datetime(df["ingested_at"], utc=True)

        df["mag_bucket"] = df["mag"].apply(self._get_mag_bucket)
        df["depth_bucket"] = df["depth"].apply(self._get_depth_bucket)
        df["severity"] = df["mag"].apply(self._get_severity)

        counts["event_feed"] += self._write_partition("event_feed", d, df, run_ts)

        df_top = df.sort_values(by=["mag", "time"], ascending=[False, False]).head(10).copy()
        df_top["day"] = d
        df_top["rank"] = range(1, len(df_top) + 1)
        cols_top = ["day", "rank", "event_id", "time", "mag", "depth",
                    "place", "latitude", "longitude", "tsunami", "url", "net", "status"]
        df_top = df_top[[c for c in cols_top if c in df_top.columns]]
        counts["top_events_daily"] += self._write_partition("top_events_daily", d, df_top, run_ts)

        health_row = {
            "day": d,
            "events_cnt": len(df),
            "tsunami_cnt": df["tsunami"].fillna(0).sum(),
            "max_mag": df["mag"].max(),
            "pct_missing_geo": ((df["latitude"].isna()) | (df["longitude"].isna())).mean(),
            "pct_missing_mag": df["mag"].isna().mean(),
            "avg_update_delay_min": (df["updated"] - df["time"]).dt.total_seconds().mean() / 60.0,
            "p95_update_delay_min": (df["updated"] - df["time"]).dt.total_seconds().quantile(0.95) / 60.0,
            "avg_ingest_lag_min": (df["ingested_at"] - df["time"]).dt.total_seconds().mean() / 60.0,
            "max_ingest_lag_min": (df["ingested_at"] - df["time"]).dt.total_seconds().max() / 60.0,
        }
        df_health = pd.DataFrame([health_row])

        dq_day = dq_df[dq_df["day"] == d]
        if not dq_day.empty:
            r = dq_day.iloc[0]
            df_health["dq_last_status"] = r["dq_last_status"]
            df_health["dq_last_run_at"] = r["dq_last_run_at"]
            df_health["dq_last_issues_count"] = r["dq_last_issues_count"]
        else:
            df_health["dq_last_status"] = None
            df_health["dq_last_run_at"] = None
            df_health["dq_last_issues_count"] = None

        counts["catalog_health_daily"] += self._write_partition("catalog_health_daily", d, df_health, run_ts)

    def _write_partition(self, table_name: str, dt: date, df: pd.DataFrame, run_ts: str) -> int:
        if df.empty:
            return 0
        dt_str = dt.isoformat()
        key = f"gold/bi/{table_name}/dt={dt_str}/part-{run_ts}.parquet"
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, f"{table_name}_{dt_str}.parquet")
            df.to_parquet(local_path, index=False, engine="pyarrow")
            self.storage.upload_file(local_path=local_path, key=key, content_type="application/octet-stream")
        print(f"  -> Exported {table_name} for {dt_str} ({len(df)} rows)")
        return len(df)

    @staticmethod
    def _get_mag_bucket(mag):
        if pd.isna(mag): return "unknown"
        if mag < 2: return "lt2"
        if mag < 3: return "2_3"
        if mag < 4: return "3_4"
        if mag < 5: return "4_5"
        if mag < 6: return "5_6"
        return "ge6"

    @staticmethod
    def _get_depth_bucket(d):
        if pd.isna(d): return "unknown"
        if d < 10: return "0_10"
        if d < 30: return "10_30"
        if d < 70: return "30_70"
        if d < 300: return "70_300"
        return "ge300"

    @staticmethod
    def _get_severity(mag):
        if pd.isna(mag): return "UNKNOWN"
        if mag >= 6: return "HIGH"
        if mag >= 4: return "MEDIUM"
        return "LOW"

    def _execute(self, **kwargs):
        return self.run(**kwargs)