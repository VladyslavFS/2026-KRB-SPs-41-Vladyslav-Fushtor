from __future__ import annotations

import argparse
from dateutil import parser as dtparser

from pipeline.clients.usgs_client import USGSClient
from pipeline.config.settings import Settings
from pipeline.config.pg_settings import PostgresSettings
from pipeline.jobs.ingest_raw_job import RawIngestionJob
from pipeline.jobs.transform_silver_job import SilverTransformJob
from pipeline.storage.s3_storage import S3Storage
from pipeline.warehouse.pg import PostgresRepository


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="ISO datetime, e.g. 2026-01-20T00:00:00Z")
    ap.add_argument("--end", required=True, help="ISO datetime, e.g. 2026-01-20T01:00:00Z")
    args = ap.parse_args()

    start = dtparser.isoparse(args.start)
    end = dtparser.isoparse(args.end)

    settings = Settings.from_env()
    storage = S3Storage(settings)
    client = USGSClient()

    ingest = RawIngestionJob(
        settings=settings,
        storage=storage,
        client=client
    )

    key = ingest.run(window_start=start, window_end=end)
    print(f"Stored raw to: s3://{settings.s3_bucket}/{key}")

    raw_bytes = client.fetch_geojson(
        starttime=start.isoformat(),
        endtime=end.isoformat(),
        minmagnitude=settings.min_mag
    )

    tranform = SilverTransformJob()
    rows = tranform.run(
        raw_geojson=raw_bytes,
        source_window_start=start,
        source_window_end=end
    )
    print(f"Silver rows: {len(rows)}")

    repo = PostgresRepository(PostgresSettings.from_env())
    inserted = repo.upsert_earthquakes(rows)
    print(f"Upserted rows: {inserted}")


if __name__ == "__main__":
    main()