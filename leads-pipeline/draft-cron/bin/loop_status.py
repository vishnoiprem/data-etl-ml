#!/usr/bin/env python3
"""
loop_status.py — Print a single-line status snapshot for the auto-loop.

Output (space-separated, easy to parse from bash):
    <pending_total> <pending_with_email> <pending_fully_enriched> <bounce_rate_pct>

Retry on transient DB lock — bounded attempts to avoid hanging the loop.
"""

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent.parent
sys.path.insert(0, str(HERE))


def main():
    from db.lead_store import get_cursor
    max_attempts = int(os.getenv("AVILX_STATUS_RETRIES", "3"))
    for attempt in range(max_attempts):
        try:
            with get_cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM leads
                    WHERE contact_email IS NOT NULL AND contact_email != ''
                      AND status='pending'
                """)
                pending_email = cur.fetchone()["count"]
                cur.execute("""
                    SELECT COUNT(*) FROM leads WHERE status='pending'
                """)
                pending_total = cur.fetchone()["count"]
                cur.execute("""
                    SELECT COUNT(*) FROM leads
                    WHERE status='pending' AND resume_file IS NOT NULL
                      AND cover_letter_body IS NOT NULL
                """)
                pending_enriched = cur.fetchone()["count"]
                cur.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM leads WHERE status='bounced') AS b,
                        (SELECT COUNT(*) FROM leads WHERE status='sent_email') AS s
                """)
                row = cur.fetchone()
                bounce_pct = (
                    round(row["b"] / row["s"] * 100, 1) if row["s"] else 0
                )
            print(
                f"{pending_total} {pending_email} {pending_enriched} {bounce_pct}"
            )
            return 0
        except Exception as e:
            if attempt + 1 >= max_attempts:
                print(f"? ? ? ? (err: {e})", file=sys.stderr)
                return 1
            time.sleep(2)
    return 1


if __name__ == "__main__":
    sys.exit(main())
