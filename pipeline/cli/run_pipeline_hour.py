from __future__ import annotations

import argparse
from dateutil import parser as dtparser

from pipeline.cli.run_hour import main as run_hour_main
from pipeline.cli.dq_hour import main as dq_hour_main
# We replace old bi_marts/export with build_gold_layer
from pipeline.cli.build_gold_layer import main as build_gold_main


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="ISO datetime")
    ap.add_argument("--end", required=True, help="ISO datetime")

    ap.add_argument("--skip-dq", action="store_true")
    ap.add_argument("--skip-gold", action="store_true", help="Skip Gold layer generation")
    
    # Legacy flags to not break interface, but we ignore them or map them
    ap.add_argument("--skip-marts", action="store_true") 
    ap.add_argument("--skip-export", action="store_true")

    ap.add_argument("--export-days", type=int, default=30)
    args = ap.parse_args()

    _ = dtparser.isoparse(args.start)
    _ = dtparser.isoparse(args.end)

    import sys

    # 1) raw->silver->ods
    print("=== [1/3] run_hour (raw->silver->ods) ===")
    sys.argv = ["run_hour", "--start", args.start, "--end", args.end]
    run_hour_main()

    # 2) dq
    if args.skip_dq:
        print("=== [2/3] dq_hour (SKIPPED) ===")
    else:
        print("=== [2/3] dq_hour ===")
        sys.argv = ["dq_hour", "--start", args.start, "--end", args.end]
        dq_hour_main()

    # 3) Gold Layer (Python-based)
    # This replaces both 'build_bi_marts' (SQL) and 'export_bi_parquet'
    if args.skip_gold or args.skip_export:
         print("=== [3/3] build_gold_layer (SKIPPED) ===")
    else:
        print("=== [3/3] build_gold_layer ===")
        sys.argv = ["build_gold_layer", "--days", str(int(args.export_days))]
        build_gold_main()

    print("✓ pipeline hour done")


if __name__ == "__main__":
    main()