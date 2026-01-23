from __future__ import annotations

import argparse
from datetime import timedelta
from dateutil import parser as dtparser

from pipeline.cli.run_hour import main as run_hour_main


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="ISO datetime")
    ap.add_argument("--end", required=True, help="ISO datetime")
    ap.add_argument("--continue-on-error", action="store_true")
    args = ap.parse_args()

    start = dtparser.isoparse(args.start)
    end = dtparser.isoparse(args.end)

    cur = start
    while cur < end:
        nxt = min(cur + timedelta(hours=1), end)
        try:
            import sys

            sys.argv = ["run_hour", "--start", cur.isoformat(), "--end", nxt.isoformat()]
            run_hour_main()
        except Exception as e:
            print(f"❌ Failed window {cur.isoformat()}..{nxt.isoformat()}: {e}")
            if not args.continue_on_error:
                raise
        cur = nxt


if __name__ == "__main__":
    main()
