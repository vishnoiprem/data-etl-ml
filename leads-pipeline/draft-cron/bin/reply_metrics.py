#!/usr/bin/env python3
"""
bin/reply_metrics.py — weekly reply / conversion KPIs across all
leads-pipeline/YYYY-MM-DD/leads-tracker.csv files.

Answers the questions that drive the next 30 days of outreach:

  - "How many leads did I send this week?"
  - "What's my reply rate by channel (email vs X DM vs platform)?"
  - "Which day of the week converts best?"
  - "How many meetings → offers so far this month?"

Usage:
    python3 bin/reply_metrics.py                    # last 7 days
    python3 bin/reply_metrics.py --days 30          # last 30 days
    python3 bin/reply_metrics.py --all              # all-time
    python3 bin/reply_metrics.py --by-channel       # break down by channel
    python3 bin/reply_metrics.py --json             # machine-readable output

The script reads every leads-tracker.csv it can find under
leads-pipeline/ (one per YYYY-MM-DD/ directory) and aggregates the
reply-tracking columns. Missing columns are treated as zero, so this
is safe to run on older drops that pre-date the reply-tracking work.
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

LEADS_ROOT = HERE.parent  # leads-pipeline/ is the parent of draft-cron/


def find_trackers() -> list[Path]:
    out = []
    for d in LEADS_ROOT.iterdir():
        if re.match(r"\d{4}-\d{2}-\d{2}$", d.name):
            csv_path = d / "leads-tracker.csv"
            if csv_path.exists():
                out.append(csv_path)
    return sorted(out, key=lambda p: p.parent.name)


def load_tracker(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open() as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], []
        rows = list(reader)
    return header, rows


def col(header: list[str], name: str) -> int:
    """Return index of column `name` in header, or -1 if missing."""
    return header.index(name) if name in header else -1


def aggregate(days: int | None) -> dict:
    """Walk all trackers, filter rows by `date_sent` within the window,
    and aggregate KPIs by channel + per-day + per-source."""
    trackers = find_trackers()
    cutoff = None
    if days is not None:
        cutoff = (datetime.utcnow().date() - timedelta(days=days)).isoformat()

    by_channel = defaultdict(lambda: {"sent": 0, "replied": 0, "meetings": 0})
    by_day = defaultdict(lambda: {"sent": 0, "replied": 0, "meetings": 0})
    by_source_file = defaultdict(lambda: {"sent": 0, "replied": 0, "meetings": 0})
    overall = {"sent": 0, "replied": 0, "meetings": 0}

    for path in trackers:
        header, rows = load_tracker(path)
        if not header:
            continue
        ci_channel = col(header, "channel")
        ci_date_sent = col(header, "date_sent")
        ci_replied = col(header, "replied")
        ci_meeting = col(header, "meeting_booked")
        if ci_channel < 0 or ci_date_sent < 0:
            continue
        for row in rows:
            # Pad to header length so missing trailing cols don't IndexError
            while len(row) < len(header):
                row.append("")
            date_sent = (row[ci_date_sent] or "").strip()
            channel = (row[ci_channel] or "").strip() or "unknown"
            replied = (row[ci_replied] if ci_replied >= 0 else "").strip().lower() == "yes"
            meeting = bool((row[ci_meeting] if ci_meeting >= 0 else "").strip())
            # Window filter: if cutoff is set, require date_sent >= cutoff.
            # Rows with no date_sent are not "sent" and not counted in sent/replied.
            if not date_sent:
                continue
            if cutoff and date_sent < cutoff:
                continue
            by_channel[channel]["sent"] += 1
            by_day[date_sent]["sent"] += 1
            by_source_file[path.parent.name]["sent"] += 1
            overall["sent"] += 1
            if replied:
                by_channel[channel]["replied"] += 1
                by_day[date_sent]["replied"] += 1
                by_source_file[path.parent.name]["replied"] += 1
                overall["replied"] += 1
            if meeting:
                by_channel[channel]["meetings"] += 1
                by_day[date_sent]["meetings"] += 1
                by_source_file[path.parent.name]["meetings"] += 1
                overall["meetings"] += 1

    return {
        "window_days": days,
        "overall": overall,
        "by_channel": dict(by_channel),
        "by_day": dict(sorted(by_day.items())),
        "by_source_file": dict(by_source_file),
    }


def print_human(stats: dict, by_channel: bool) -> None:
    o = stats["overall"]
    sent, replied, meetings = o["sent"], o["replied"], o["meetings"]
    rr = (replied / sent * 100) if sent else 0.0
    mr = (meetings / replied * 100) if replied else 0.0
    window = f"last {stats['window_days']}d" if stats["window_days"] else "all-time"
    print(f"# Reply metrics — {window}")
    print(f"  sent     = {sent}")
    print(f"  replied  = {replied}  ({rr:.1f}% reply rate)")
    print(f"  meetings = {meetings}  ({mr:.1f}% meeting rate from replies)")

    if by_channel:
        print("\n## By channel")
        print(f"  {'channel':14s}  {'sent':>5s}  {'replied':>8s}  {'reply%':>7s}  {'meetings':>9s}")
        print("  " + "-" * 50)
        for ch, v in sorted(stats["by_channel"].items(), key=lambda kv: -kv[1]["sent"]):
            ch_sent, ch_rep, ch_mt = v["sent"], v["replied"], v["meetings"]
            ch_rr = (ch_rep / ch_sent * 100) if ch_sent else 0.0
            print(f"  {ch:14s}  {ch_sent:>5d}  {ch_rep:>8d}  {ch_rr:>6.1f}%  {ch_mt:>9d}")

    if stats["by_day"]:
        print(f"\n## By day (most recent {min(14, len(stats['by_day']))} shown)")
        print(f"  {'date':12s}  {'sent':>5s}  {'replied':>8s}  {'meetings':>9s}")
        print("  " + "-" * 40)
        for d, v in list(stats["by_day"].items())[-14:]:
            print(f"  {d:12s}  {v['sent']:>5d}  {v['replied']:>8d}  {v['meetings']:>9d}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Weekly reply / conversion KPIs.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--days", type=int, default=7, help="Window in days (default: 7).")
    g.add_argument("--all", action="store_true", help="All-time (no window filter).")
    ap.add_argument("--by-channel", action="store_true", help="Break down by channel.")
    ap.add_argument("--json", action="store_true", help="Machine-readable output.")
    args = ap.parse_args()

    days = None if args.all else args.days
    stats = aggregate(days)
    if args.json:
        print(json.dumps(stats, indent=2, default=str))
    else:
        print_human(stats, by_channel=args.by_channel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
