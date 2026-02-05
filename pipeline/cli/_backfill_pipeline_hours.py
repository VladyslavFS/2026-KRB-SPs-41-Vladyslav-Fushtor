from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from dateutil import parser as dtparser

from pipeline.cli.run_pipeline_hour import main as run_pipeline_hour_main
from pipeline.config.pg_settings import PostgresSettings
from pipeline.config.settings import Settings
from pipeline.jobs.load_bi_to_serving_layer_job import BuildBIMartsJob
from pipeline.jobs.export_bi_to_parquet_job import ExportBIToParquetJob
from pipeline.storage.s3_storage import S3Storage
from pipeline.warehouse.pg import PostgresRepository


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="ISO datetime (e.g. 2026-01-01T00:00:00Z)")
    ap.add_argument("--end", required=True, help="ISO datetime (exclusive upper bound)")
    ap.add_argument("--continue-on-error", action="store_true")
    ap.add_argument("--hours-limit", type=int, default=0, help="Debug: stop after N hours (0 = no limit)")
    ap.add_argument("--export-days", type=int, default=30, help="Export last N days after backfill. Default 30.")
    args = ap.parse_args()

    start = dtparser.isoparse(args.start)
    end = dtparser.isoparse(args.end)

    cur = start
    hours_done = 0

    # ---- Hourly pipeline (NO marts, NO export) ----
    while cur < end:
        nxt = min(cur + timedelta(hours=1), end)
        print(f"➡️  window {cur.isoformat()} .. {nxt.isoformat()}")

        try:
            sys.argv = [
                "run_pipeline_hour",
                "--start",
                cur.isoformat(),
                "--end",
                nxt.isoformat(),
                "--skip-marts",
                "--skip-export",
            ]
            run_pipeline_hour_main()
        except Exception as e:
            print(f"❌ Failed window {cur.isoformat()}..{nxt.isoformat()}: {e}")
            if not args.continue_on_error:
                raise

        cur = nxt
        hours_done += 1

        if args.hours_limit and hours_done >= args.hours_limit:
            print(f"🧪 hours-limit reached: {args.hours_limit}")
            break

    print(f"✅ Backfill finished. Hours processed: {hours_done}")

    # ---- Rebuild marts + export ONCE ----
    print("🔄 Rebuilding BI marts (once after backfill)...")
    repo = PostgresRepository(PostgresSettings.from_env())
    BuildBIMartsJob(repo=repo).run()
    print("✅ BI marts rebuilt")

    print(f"📦 Exporting BI marts to gold parquet (once after backfill), days={int(args.export_days)} ...")
    settings = Settings.from_env()
    storage = S3Storage(settings)

    counts = ExportBIToParquetJob(repo=repo, storage=storage, bucket=settings.s3_bucket).run(
        days=int(args.export_days)
    )
    print("✅ Gold export done:")
    for k, v in counts.items():
        print(f"  - {k}: {v} rows")


if __name__ == "__main__":
    main()
