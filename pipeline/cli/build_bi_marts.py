from __future__ import annotations

import argparse

from pipeline.config.pg_settings import PostgresSettings
from pipeline.jobs.build_bi_marts_job import BuildBIMartsJob
from pipeline.warehouse.pg import PostgresRepository


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--days",
        type=int,
        default=30,
        help="Rebuild window (not used yet, reserved for future incremental rebuild). Default 30.",
    )
    args = ap.parse_args()

    # Note: currently SQL rebuilds ALL available days (it groups by day).
    # use --days later when we switch to incremental rebuild.
    _ = args.days

    repo = PostgresRepository(PostgresSettings.from_env())
    BuildBIMartsJob(repo=repo).run()
    print("✅ BI marts rebuilt (bi.event_feed, bi.top_events_daily, bi.catalog_health_daily)")


if __name__ == "__main__":
    main()
