#!/usr/bin/env python3
"""
bin/apply_mode_report.py — Daily report splitting sent/bounced/replied
by apply_mode (pitch_pod vs apply_personal).

Helps answer: "Are Prem's personal applications converting better
than Avilx pod pitches, or worse?"

Run:
    python3 bin/apply_mode_report.py
    python3 bin/apply_mode_report.py --days 7
    python3 bin/apply_mode_report.py --json
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import db.lead_store as ls


def stats_for_mode(mode: str, days: int) -> dict:
    """Pull all stats for one mode in the last N days."""
    with ls.get_cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'sent_email')             AS sent,
                COUNT(*) FILTER (WHERE status = 'bounced')                AS bounced,
                COUNT(*) FILTER (WHERE status = 'replied')                AS replied,
                COUNT(*) FILTER (WHERE status = 'failed')                 AS failed,
                COUNT(*)                                                  AS total,
                COUNT(*) FILTER (WHERE status = 'pending')                AS pending
            FROM leads
            WHERE apply_mode = %s
              AND created_at > NOW() - INTERVAL %s
        """, (mode, f"{days} days"))
        row = dict(cur.fetchone())
        # Top companies by sent count
        cur.execute("""
            SELECT company, COUNT(*) AS n
            FROM leads
            WHERE apply_mode = %s
              AND status = 'sent_email'
              AND created_at > NOW() - INTERVAL %s
            GROUP BY company ORDER BY n DESC LIMIT 5
        """, (mode, f"{days} days"))
        row["top_companies"] = [(r["company"], r["n"]) for r in cur.fetchall()]
    sent = row["sent"] or 0
    bounced = row["bounced"] or 0
    replied = row["replied"] or 0
    row["bounce_rate_pct"] = round(100 * bounced / max(sent + bounced, 1), 1)
    row["reply_rate_pct"] = round(100 * replied / max(sent, 1), 1)
    return row


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=1,
                   help="Look back N days (default 1)")
    p.add_argument("--json", action="store_true",
                   help="Output JSON instead of formatted text")
    args = p.parse_args()

    pod = stats_for_mode("pitch_pod", args.days)
    personal = stats_for_mode("apply_personal", args.days)

    if args.json:
        print(json.dumps({
            "window_days": args.days,
            "pitch_pod": pod,
            "apply_personal": personal,
        }, indent=2))
        return 0

    print(f"📊 Avilx outreach — last {args.days} day(s)")
    print()
    print(f"{'Mode':<18} {'Sent':>5} {'Bounced':>9} {'Replied':>9} "
          f"{'Pending':>9} {'Bounce%':>8} {'Reply%':>7}")
    print("─" * 70)
    for label, s in (("pitch_pod", pod), ("apply_personal", personal)):
        print(f"{label:<18} {s['sent']:>5} {s['bounced']:>9} {s['replied']:>9} "
              f"{s['pending']:>9} {s['bounce_rate_pct']:>7}% {s['reply_rate_pct']:>6}%")
    # Top 5 per mode (only if there's data)
    for label, s in (("pitch_pod", pod), ("apply_personal", personal)):
        if s["top_companies"]:
            print()
            print(f"Top {label} targets ({s['sent']} sent):")
            for co, n in s["top_companies"]:
                print(f"  {n:>3}  {co}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
