#!/usr/bin/env python3
"""
check_email_status.py — One-shot health check for the email pipeline.

Tells you, in 10 seconds:
  - how many emails were attempted in the last 24h / 7d / all-time
  - how many failed, with the actual error text
  - which leads are stuck in 'failed' and should be retried
  - SMTP account health (quota, recent auth errors)
  - last successful send timestamp
  - opt-outs, bounces, etc.

Run:
  python3 check_email_status.py            # full report
  python3 check_email_status.py --tail 20  # show last 20 send_log rows
  python3 check_email_status.py --failed   # only show failures
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from db.lead_store import get_cursor, stats  # noqa


def _hr(t):
    return f"{t:>20}  "


def _print_funnel():
    print("\n📊 FUNNEL (lifetime)")
    s = stats()
    by = s.get("by_status", {})
    order = ["pending", "sent_email", "opened_url", "replied",
             "failed", "bounced", "opted_out", "won"]
    for k in order:
        if k in by:
            print(f"  {k:15s} {by[k]:>4}")
    print(f"  {'─' * 30}")
    print(f"  {'TOTAL':15s} {sum(by.values()):>4}")
    print(f"\n  Sent (24h):     {s.get('sent_last_24h', 0)}")
    print(f"  Opt-outs:       {s.get('opt_outs', 0)}")
    print(f"  Unique companies: {s.get('unique_companies', 0)}")


def _print_recent_sends(limit=20):
    print(f"\n📬 LAST {limit} SENDS")
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, lead_id, to_email, status, error, sent_at
            FROM send_log
            ORDER BY id DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
    if not rows:
        print("  (no sends yet)")
        return
    fail = sum(1 for r in rows if r["status"] != "success")
    print(f"  ✅ {len(rows) - fail} success, ❌ {fail} failed")
    print(f"  {'id':>4} {'lead':>4} {'to':30s} {'status':10s} {'when':20s}")
    for r in rows:
        marker = "✅" if r["status"] == "success" else "❌"
        print(f"  {marker} {r['id']:>4} {r['lead_id']:>4} "
              f"{r['to_email']:30s} {r['status']:10s} {str(r['sent_at'])[:19]}")
        if r["status"] != "success" and r["error"]:
            err = (r["error"] or "")[:120]
            print(f"        ↳ {err}")


def _print_failures():
    print("\n❌ FAILED / BOUNCED LEADS")
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, company, contact_email, last_error, sent_at, send_count, status
            FROM leads
            WHERE status IN ('failed', 'bounced')
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
    if not rows:
        print("  (none — clean run)")
        print("  💡 Run `python3 check_bounces.py` to scan Gmail for new bounces.")
        return
    for r in rows:
        print(f"\n  lead #{r['id']:>3}  [{r['status']:8s}]  {r['company'][:30]}")
        print(f"     email:    {r['contact_email']}")
        print(f"     attempts: {r['send_count']}")
        print(f"     last try: {r['sent_at']}")
        err = (r["last_error"] or "")[:200]
        print(f"     error:    {err}")
    print("\n  💡 Run `python3 check_bounces.py` to refresh bounces from Gmail.")


def _print_smtp_health():
    """Check Gmail SMTP quota + recent auth errors from the log file."""
    print("\n📡 SMTP HEALTH")
    # Read the most recent log lines for any 'auth' / 'quota' red flags
    log_paths = [HERE / "autopilot.log.jsonl", HERE / "autopilot.log"]
    recent_lines = []
    for lp in log_paths:
        if lp.exists():
            try:
                with open(lp, "rb") as f:
                    # last 200 lines
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 50_000))
                    content = f.read().decode("utf-8", errors="ignore")
                recent_lines = content.splitlines()[-200:]
                break
            except OSError:
                pass
    keywords = ("SMTPAuthenticationError", "quota", "Daily user sending quota",
                "try again later", "421", "454", "recipients refused")
    flagged = [ln for ln in recent_lines
               if any(k.lower() in ln.lower() for k in keywords)]
    if flagged:
        print(f"  ⚠️  {len(flagged)} recent SMTP red flags:")
        for ln in flagged[-5:]:
            print(f"      {ln[:160]}")
    else:
        print("  ✅ No auth / quota red flags in recent log lines")
    # Last successful send
    with get_cursor() as cur:
        cur.execute("""
            SELECT MAX(sent_at) AS last_ok FROM send_log WHERE status='success'
        """)
        last_ok = cur.fetchone()["last_ok"]
    if last_ok:
        print(f"  Last success:  {last_ok}")
    else:
        print("  No successful sends yet.")


def _print_retry_candidates():
    """Failed leads that haven't been retried 3+ times — safe to re-queue."""
    print("\n🔁 RETRY CANDIDATES (failed < 3 times, older than 1h)")
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, company, contact_email, send_count, last_error
            FROM leads
            WHERE status = 'failed' AND send_count < 3
              AND (sent_at IS NULL OR sent_at < NOW() - INTERVAL '1 hour')
            ORDER BY id
        """)
        rows = cur.fetchall()
    if not rows:
        print("  (none)")
        return
    print(f"  {len(rows)} leads safe to retry:")
    for r in rows:
        err = (r["last_error"] or "")[:80]
        print(f"    #{r['id']:3d}  {r['company'][:25]:25s}  "
              f"{r['contact_email']:30s}  tries={r['send_count']}  err={err}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tail", type=int, default=10,
                    help="How many recent sends to show (default 10)")
    ap.add_argument("--failed", action="store_true",
                    help="Only show failures + retry candidates")
    args = ap.parse_args()

    print(f"\n🩺 AVILX EMAIL HEALTH CHECK — {datetime.now().isoformat()[:19]}")
    if not args.failed:
        _print_funnel()
        _print_smtp_health()
    _print_recent_sends(limit=args.tail)
    _print_failures()
    if not args.failed:
        _print_retry_candidates()
    print()


if __name__ == "__main__":
    main()
