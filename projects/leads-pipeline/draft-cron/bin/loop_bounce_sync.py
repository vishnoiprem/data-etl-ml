#!/usr/bin/env python3
"""
loop_bounce_sync.py — One-shot bounce sync, designed to be called from
auto_loop.sh. Reads Gmail IMAP for the last 7 days, marks any new
bounced leads, prints a one-line summary.

Exit codes:
  0  — no errors (regardless of whether any bounces were marked)
  1  — fatal error (DB down, IMAP down, etc.)
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).parent.parent
sys.path.insert(0, str(HERE))


def main():
    try:
        from check_bounces import scan_bounces, mark_bounced
    except Exception as e:
        print(f"  [bounce-sync] import error: {e}", file=sys.stderr)
        return 1
    since_days = int(os.getenv("AVILX_BOUNCE_SINCE_DAYS", "7"))
    try:
        bounce_map, _ = scan_bounces(since_days=since_days)
    except Exception as e:
        print(f"  [bounce-sync] scan error: {e}", file=sys.stderr)
        return 1
    if bounce_map:
        try:
            counts = mark_bounced(bounce_map, dry=False)
            print(
                f"  [bounce-sync] marked={counts.get('marked', 0)} "
                f"already={counts.get('already_bounced', 0)} "
                f"unknown={counts.get('unknown', 0)}"
            )
        except Exception as e:
            print(f"  [bounce-sync] mark error: {e}", file=sys.stderr)
            return 1
    else:
        print("  [bounce-sync] no new bounces")
    return 0


if __name__ == "__main__":
    sys.exit(main())
