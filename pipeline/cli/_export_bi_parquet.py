from __future__ import annotations

import argparse

from pipeline.config.pg_settings import PostgresSettings
from pipeline.config.settings import Settings
from pipeline.jobs.export_bi_to_parquet_job import ExportBIToParquetJob
from pipeline.storage.s3_storage import S3Storage
from pipeline.warehouse.pg import PostgresRepository


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30, help="Export last N days (UTC, including today). Default 30.")
    args = ap.parse_args()

    settings = Settings.from_env()
    storage = S3Storage(settings)
    repo = PostgresRepository(PostgresSettings.from_env())

    job = ExportBIToParquetJob(repo=repo, storage=storage, bucket=settings.s3_bucket)
    counts = job.run(days=int(args.days))

    print("✅ Gold export done:")
    for k, v in counts.items():
        print(f"  - {k}: {v} rows")


if __name__ == "__main__":
    main()
