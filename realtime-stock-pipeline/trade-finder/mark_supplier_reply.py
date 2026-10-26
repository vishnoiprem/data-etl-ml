#!/usr/bin/env python3
"""
mark_supplier_reply.py — record a reply / quote / sample outcome on
one of the top-3 shortlisted fitness-band suppliers.

This is the trade-finder-side mirror of leads-pipeline's
`bin/mark_reply.py`. Same idea: append four reply-tracking columns
to the supplier tracker markdown table, log a per-supplier row, and
print a one-line summary.

Why a separate tool, not reuse the leads-pipeline one?
- The data store is different: this side is a markdown table in
  business-plan/04b_quote_tracker.md, not a CSV.
- The schema is different: a supplier reply carries price quotes,
  sample status, and a 5-axis score, not just "replied yes/no".
- The audience is different: this is operated from
  realtime-stock-pipeline/trade-finder/, not leads-pipeline/.

Usage:
    # Mark a quote reply
    python3 mark_supplier_reply.py "Gold Star" --replied \\
        --at 2026-10-15 --via email \\
        --notes "Quoted: 500u=$8.50, 1000u=$7.80, 19d lead, T/T 30/70 OK, OEM 500u MOQ"

    # Mark a sample shipped / received / QC-pass
    python3 mark_supplier_reply.py "Gold Star" --sample-shipped --at 2026-10-17
    python3 mark_supplier_reply.py "Gold Star" --sample-received --at 2026-10-22
    python3 mark_supplier_reply.py "Gold Star" --sample-qc-pass --at 2026-10-29

    # Show current state
    python3 mark_supplier_reply.py --list

    # Revert
    python3 mark_supplier_reply.py "Gold Star" --revert
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUOTE_TRACKER = HERE / "business-plan" / "04b_quote_tracker.md"
STATE_FILE = HERE / "data" / "supplier_state.json"

# Aliases to match the supplier names in quote_tracker.md
SUPPLIER_ALIASES = {
    "gold star": "1. Shenzhen Gold Star Technology",
    "goldstar": "1. Shenzhen Gold Star Technology",
    "ocom": "2. Shenzhen OCOM Technology",
    "qiyang": "3. Shenzhen Qiyang Technology",
    "qy": "3. Shenzhen Qiyang Technology",
}

# The four outcome bits we track. Each is a (column_name, valid_values)
# pair that the tool flips to "yes" or a date.
OUTCOMES = {
    "rfq_sent": "date",
    "replied": "date",
    "via": "channel",
    "sample_ordered": "date",
    "sample_received": "date",
    "sample_qc": "enum:pass,fail,pending",
    "po_signed": "date",
    "deposit_wired": "date",
}

VALID_CHANNELS = ["email", "whatsapp", "wechat", "alibaba", "phone", "other"]


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _resolve_supplier(query: str) -> str:
    """Map a fuzzy query to the canonical supplier header in quote_tracker.md."""
    q = query.lower().strip()
    for alias, canonical in SUPPLIER_ALIASES.items():
        if alias in q or q in alias:
            return canonical
    # Fallback: try to find by short token (e.g. "Gold")
    for alias, canonical in SUPPLIER_ALIASES.items():
        if q in alias:
            return canonical
    raise ValueError(
        f"Unknown supplier {query!r}. Known aliases: {sorted(SUPPLIER_ALIASES.keys())}"
    )


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def _print_list(state: dict) -> None:
    print(f"# Supplier reply state ({_now_utc()} UTC)")
    print(f"{'#':>3}  {'Supplier':45s}  {'Sent':12s}  {'Replied':12s}  {'Sample':10s}  QC")
    print("-" * 95)
    for canonical, row in state.items():
        sent = row.get("replied_at") or row.get("rfq_sent") or "—"
        replied = row.get("replied_at") or "—"
        sample = row.get("sample_received") or "—"
        qc = row.get("sample_qc") or "—"
        print(f"     {canonical:45s}  {sent:12s}  {replied:12s}  {sample:10s}  {qc}")


def _set_outcome(state: dict, canonical: str, key: str, value: str) -> None:
    state.setdefault(canonical, {})
    state[canonical][key] = value


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Record a supplier outcome (reply, sample, QC, PO) on the RFQ tracker.",
    )
    ap.add_argument("query", nargs="?", help="Supplier name or alias (e.g. 'Gold Star', 'OCOM', 'Qiyang').")
    ap.add_argument("--replied", action="store_true", help="Mark as replied.")
    ap.add_argument("--at", help="Date in YYYY-MM-DD (defaults to today UTC).")
    ap.add_argument("--via", choices=VALID_CHANNELS, help="Reply channel.")
    ap.add_argument("--sample-ordered", action="store_true", help="Mark sample as ordered.")
    ap.add_argument("--sample-shipped", action="store_true", help="Mark sample as shipped by supplier.")
    ap.add_argument("--sample-received", action="store_true", help="Mark sample as received.")
    ap.add_argument("--sample-qc-pass", action="store_true", help="Mark sample as QC-passed.")
    ap.add_argument("--sample-qc-fail", action="store_true", help="Mark sample as QC-failed.")
    ap.add_argument("--po-signed", action="store_true", help="Mark PO as signed.")
    ap.add_argument("--deposit-wired", action="store_true", help="Mark deposit as wired.")
    ap.add_argument("--notes", help="Free-text notes (price quotes, lead time, MOQ, etc).")
    ap.add_argument("--revert", action="store_true", help="Clear the state for this supplier.")
    ap.add_argument("--list", action="store_true", help="List current state and exit.")
    args = ap.parse_args()

    if args.list:
        _print_list(_load_state())
        return 0

    if not args.query:
        ap.error("query is required (or use --list)")

    if not any([
        args.replied, args.sample_ordered, args.sample_shipped,
        args.sample_received, args.sample_qc_pass, args.sample_qc_fail,
        args.po_signed, args.deposit_wired, args.revert,
    ]):
        ap.error("at least one of --replied, --sample-*, --po-signed, --deposit-wired, or --revert is required")

    canonical = _resolve_supplier(args.query)
    state = _load_state()

    if args.revert:
        if canonical in state:
            del state[canonical]
        _save_state(state)
        print(f"✅ REVERTED: cleared state for {canonical}")
        return 0

    when = args.at or _now_utc()

    if args.replied:
        _set_outcome(state, canonical, "replied_at", when)
        if args.via:
            _set_outcome(state, canonical, "replied_via", args.via)
    if args.sample_ordered:
        _set_outcome(state, canonical, "sample_ordered", when)
    if args.sample_shipped:
        _set_outcome(state, canonical, "sample_shipped", when)
    if args.sample_received:
        _set_outcome(state, canonical, "sample_received", when)
    if args.sample_qc_pass:
        _set_outcome(state, canonical, "sample_qc", "pass")
    if args.sample_qc_fail:
        _set_outcome(state, canonical, "sample_qc", "fail")
    if args.po_signed:
        _set_outcome(state, canonical, "po_signed", when)
    if args.deposit_wired:
        _set_outcome(state, canonical, "deposit_wired", when)
    if args.notes:
        existing = state.get(canonical, {}).get("notes", "")
        ts = _now_utc()
        prefix = f"[{ts}]"
        new_note = f"{prefix} {args.notes}"
        if new_note not in existing:
            state.setdefault(canonical, {})["notes"] = (
                f"{existing}\n{new_note}" if existing else new_note
            )

    _save_state(state)

    print(f"✅ Updated {canonical}:")
    pretty = json.dumps(state[canonical], indent=2)
    print(pretty)
    print(f"\nFull state persisted to: {STATE_FILE}")
    print(f"Update quote_tracker.md table cells by hand when the quote comes back.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
