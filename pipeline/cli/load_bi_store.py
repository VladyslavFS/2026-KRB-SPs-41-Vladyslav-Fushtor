from __future__ import annotations

import argparse

from pipeline.config.pg_settings import PostgresSettings
from pipeline.config.settings import Settings
from pipeline.jobs.load_bi_to_serving_layer_job import LoadBIStoreJob
from pipeline.storage.s3_storage import S3Storage
from pipeline.warehouse.pg import PostgresRepository


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30, help="Sync last N days from Gold S3 to BI Store.")
    args = ap.parse_args()

    settings = Settings.from_env()
    storage = S3Storage(settings)
    repo = PostgresRepository(PostgresSettings.from_env())

    job = LoadBIStoreJob(repo=repo, storage=storage, bucket=settings.s3_bucket)
    job.run(days=int(args.days))

    print("✓ BI Store synced successfully (S3 -> Postgres)")


if __name__ == "__main__":
    main()