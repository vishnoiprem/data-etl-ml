#!/usr/bin/env python3
"""
bin/mark_reply.py — record a reply / meeting outcome on a lead in
leads-pipeline/<date>/leads-tracker.csv.

Adds the four reply-tracking columns to the CSV (idempotent — safe to
re-run) and lets you record, in one CLI call:

  - "Tailscale replied on 2026-10-12 via email"
  - "Perform.AI booked a meeting on 2026-10-14"

Usage:
    python3 bin/mark_reply.py "Tailscale" --replied --at 2026-10-12 --via email
    python3 bin/mark_reply.py "Perform.AI" --meeting --at 2026-10-14
    python3 bin/mark_reply.py "Acme Co" --replied --at 2026-10-12 --via x_dm --notes "asked for case studies"
    python3 bin/mark_reply.py "Tailscale" --revert          # clear the reply
    python3 bin/mark_reply.py --list                         # show current reply state

Search is by company name (case-insensitive substring) OR by the
numeric # field (1-based index in the STATUS section).

The script:
  1. Finds the latest leads-pipeline/YYYY-MM-DD/leads-tracker.csv.
  2. Ensures the four reply columns exist (adds them if missing).
  3. Updates the matching row in-place, preserving all other fields.
  4. Prints a one-line summary so you can sanity-check the result.
"""
import argparse
import csv
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

# The four reply-tracking columns. If the CSV is missing any of these,
# the script will add them (idempotent migration).
REPLY_COLS = ["replied", "replied_at", "reply_channel", "meeting_booked"]

VALID_CHANNELS = ["email", "x_dm", "linkedin", "platform", "inbound", "other"]


def find_latest_tracker() -> Path:
    """Return the most recent leads-pipeline/YYYY-MM-DD/leads-tracker.csv."""
    leads_root = HERE.parent  # bin/ is one level deep; leads-pipeline/ is the parent of draft-cron/
    candidates = []
    for d in leads_root.iterdir():
        if re.match(r"\d{4}-\d{2}-\d{2}$", d.name):
            csv_path = d / "leads-tracker.csv"
            if csv_path.exists():
                candidates.append(csv_path)
    if not candidates:
        raise FileNotFoundError(
            f"No leads-tracker.csv found under {leads_root}. "
            f"Expected at least one YYYY-MM-DD/ directory."
        )
    return max(candidates, key=lambda p: p.parent.name)


def ensure_reply_columns(header: list[str]) -> list[str]:
    """Add any missing REPLY_COLS to the header (idempotent)."""
    new_header = list(header)
    for col in REPLY_COLS:
        if col not in new_header:
            new_header.append(col)
    return new_header


def find_row(rows: list[list[str]], header: list[str], query: str) -> tuple[int, list[str]]:
    """Return (index, row) for a query matching company (case-insensitive substring)
    or numeric index (1-based) of the company column."""
    company_idx = header.index("company")
    for i, row in enumerate(rows):
        if len(row) <= company_idx:
            continue
        company = row[company_idx] or ""
        if query.lower() in company.lower():
            return i, row
    raise ValueError(f"No lead matches query {query!r}.")


def list_state(tracker: Path) -> None:
    with tracker.open() as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    company_idx = header.index("company")
    replied_idx = header.index("replied") if "replied" in header else None
    replied_at_idx = header.index("replied_at") if "replied_at" in header else None
    channel_idx = header.index("reply_channel") if "reply_channel" in header else None
    meeting_idx = header.index("meeting_booked") if "meeting_booked" in header else None

    print(f"# Reply state in {tracker}")
    print(f"{'#':>3}  {'Company':30s}  {'Replied':8s}  {'When':12s}  {'Channel':10s}  Meeting")
    print("-" * 80)
    for i, row in enumerate(rows, start=1):
        company = row[company_idx] if len(row) > company_idx else ""
        replied = (row[replied_idx] if replied_idx is not None and len(row) > replied_idx else "") or "—"
        when = (row[replied_at_idx] if replied_at_idx is not None and len(row) > replied_at_idx else "") or "—"
        channel = (row[channel_idx] if channel_idx is not None and len(row) > channel_idx else "") or "—"
        meeting = (row[meeting_idx] if meeting_idx is not None and len(row) > meeting_idx else "") or "—"
        print(f"{i:>3}  {company:30s}  {replied:8s}  {when:12s}  {channel:10s}  {meeting}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Record a reply / meeting on a lead in leads-tracker.csv.",
    )
    ap.add_argument("query", nargs="?", help="Company name (substring) or numeric #. Optional with --list.")
    ap.add_argument("--replied", action="store_true", help="Mark this lead as replied.")
    ap.add_argument("--meeting", action="store_true", help="Mark this lead as meeting-booked.")
    ap.add_argument("--at", help="Date in YYYY-MM-DD (defaults to today UTC).")
    ap.add_argument("--via", choices=VALID_CHANNELS, help="Reply channel.")
    ap.add_argument("--notes", help="Free-text note to record alongside the reply.")
    ap.add_argument("--revert", action="store_true", help="Clear the reply state for this row.")
    ap.add_argument("--list", action="store_true", help="List current reply state and exit.")
    args = ap.parse_args()

    tracker = find_latest_tracker()

    if args.list:
        list_state(tracker)
        return 0

    if not args.query:
        ap.error("query is required (or use --list)")

    if not (args.replied or args.meeting or args.revert):
        ap.error("one of --replied, --meeting, or --revert is required")

    # Load + migrate header
    with tracker.open() as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    new_header = ensure_reply_columns(header)
    header_changed = new_header != header

    # Find the row
    idx, row = find_row(rows, new_header, args.query)
    # Pad row to match new header
    while len(row) < len(new_header):
        row.append("")
    # If header changed, we need to re-lookup (because column indices shifted)
    if header_changed:
        # The four new columns are appended at the end; existing column indices are stable.
        pass

    replied_idx = new_header.index("replied")
    replied_at_idx = new_header.index("replied_at")
    channel_idx = new_header.index("reply_channel")
    meeting_idx = new_header.index("meeting_booked")

    if args.revert:
        row[replied_idx] = ""
        row[replied_at_idx] = ""
        row[channel_idx] = ""
        row[meeting_idx] = ""
        action = "REVERTED"
    else:
        when = args.at or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if args.replied:
            row[replied_idx] = "yes"
            row[replied_at_idx] = when
            if args.via:
                row[channel_idx] = args.via
        if args.meeting:
            row[meeting_idx] = when
        action_bits = []
        if args.replied:
            action_bits.append("REPLIED")
        if args.meeting:
            action_bits.append("MEETING")
        action = "+".join(action_bits)

    # Optional notes: append to existing notes column (index 13 in the
    # standard header; we look it up by name to be migration-safe).
    if args.notes and "notes" in new_header:
        notes_idx = new_header.index("notes")
        existing = row[notes_idx] or ""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        prefix = f"[{ts} reply]"
        if prefix not in existing:
            row[notes_idx] = f"{existing} | {prefix} {args.notes}" if existing else f"{prefix} {args.notes}"

    # Pad every row in the file to the new header length, not just the
    # matched one. Otherwise rows that don't match the query stay at
    # their original width and the CSV ends up ragged.
    for r in rows:
        while len(r) < len(new_header):
            r.append("")
    rows[idx] = row
    with tracker.open("w", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(new_header)
        writer.writerows(rows)

    company = row[new_header.index("company")]
    print(f"✅ {action}: row {idx + 1} ({company}) in {tracker.parent.name}/leads-tracker.csv")
    if row[replied_idx]:
        print(f"   replied=yes  at={row[replied_at_idx]}  via={row[channel_idx] or '?'}")
    if row[meeting_idx]:
        print(f"   meeting={row[meeting_idx]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
