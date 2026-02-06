from __future__ import annotations

import argparse

from pipeline.config.pg_settings import PostgresSettings
from pipeline.config.settings import Settings
from pipeline.jobs.build_gold_job import BuildGoldJob
from pipeline.storage.s3_storage import S3Storage
from pipeline.warehouse.pg import PostgresRepository


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30, help="Build Gold for last N days.")
    args = ap.parse_args()

    settings = Settings.from_env()
    storage = S3Storage(settings)
    repo = PostgresRepository(PostgresSettings.from_env())

    job = BuildGoldJob(repo=repo, storage=storage, bucket=settings.s3_bucket)
    counts = job.run(days=int(args.days))

    print("✓ Gold layer built successfully:")
    for k, v in counts.items():
        print(f"  - {k}: {v} rows")


if __name__ == "__main__":
    main()