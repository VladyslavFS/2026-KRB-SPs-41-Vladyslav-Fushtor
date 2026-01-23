from __future__ import annotations

import argparse
from dateutil import parser as dtparser

from pipeline.config.pg_settings import PostgresSettings
from pipeline.jobs.dq_job import DataQualityJob
from pipeline.warehouse.pg import PostgresRepository


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    args = ap.parse_args()

    start = dtparser.isoparse(args.start)
    end = dtparser.isoparse(args.end)

    repo = PostgresRepository(PostgresSettings.from_env())
    job = DataQualityJob(repo=repo)
    run_id = job.run(window_start=start, window_end=end)
    print(f"✅ DQ run stored: run_id={run_id}")


if __name__ == "__main__":
    main()
