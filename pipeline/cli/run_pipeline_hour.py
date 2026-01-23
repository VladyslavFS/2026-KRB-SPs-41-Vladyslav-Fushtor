from __future__ import annotations

import argparse
from dateutil import parser as dtparser

from pipeline.cli.run_hour import main as run_hour_main
from pipeline.cli.dq_hour import main as dq_hour_main
from pipeline.cli.build_bi_marts import main as bi_marts_main
from pipeline.cli.export_bi_parquet import main as export_bi_parquet_main


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="ISO datetime, e.g. 2026-01-20T00:00:00Z")
    ap.add_argument("--end", required=True, help="ISO datetime, e.g. 2026-01-20T01:00:00Z")

    ap.add_argument("--skip-dq", action="store_true", help="Skip data quality checks")
    ap.add_argument("--skip-marts", action="store_true", help="Skip BI marts rebuild")
    ap.add_argument("--skip-export", action="store_true", help="Skip gold parquet export")

    # For export step
    ap.add_argument("--export-days", type=int, default=30, help="Export last N days (default 30)")
    args = ap.parse_args()

    # validate timestamps
    _ = dtparser.isoparse(args.start)
    _ = dtparser.isoparse(args.end)

    # 1) raw->silver->ods
    import sys

    print("=== [1/4] run_hour (raw->silver->ods) ===")
    sys.argv = ["run_hour", "--start", args.start, "--end", args.end]
    run_hour_main()

    # 2) dq
    if args.skip_dq:
        print("=== [2/4] dq_hour (SKIPPED) ===")
    else:
        print("=== [2/4] dq_hour ===")
        sys.argv = ["dq_hour", "--start", args.start, "--end", args.end]
        dq_hour_main()

    # 3) marts
    if args.skip_marts:
        print("=== [3/4] build_bi_marts (SKIPPED) ===")
    else:
        print("=== [3/4] build_bi_marts ===")
        # days not used now, but keep for future
        sys.argv = ["build_bi_marts", "--days", "30"]
        bi_marts_main()

    # 4) export
    if args.skip_export:
        print("=== [4/4] export_bi_parquet (SKIPPED) ===")
    else:
        print("=== [4/4] export_bi_parquet ===")
        sys.argv = ["export_bi_parquet", "--days", str(int(args.export_days))]
        export_bi_parquet_main()

    print("✅ pipeline hour done")


if __name__ == "__main__":
    main()
