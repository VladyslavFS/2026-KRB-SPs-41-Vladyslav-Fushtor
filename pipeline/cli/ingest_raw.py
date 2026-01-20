from __future__ import annotations

import argparse
from datetime import datetime
from dateutil import parser as dtparser

from pipeline.clients.usgs_client import USGSClient
from pipeline.config.settings import Settings
from pipeline.jobs.ingest_raw_job import RawIngestionJob
from pipeline.storage.s3_storage import S3Storage

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
    job = RawIngestionJob(
        settings=settings,
        storage=storage,
        client=client
    )

    key = job.run(window_start=start, window_end=end)
    print(f"Stored raw to: s3://{settings.s3_bucket}/{key}")


if __name__ == "__main__":
    main()