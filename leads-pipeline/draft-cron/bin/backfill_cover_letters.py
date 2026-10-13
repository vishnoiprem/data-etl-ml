#!/usr/bin/env python3
"""
bin/backfill_cover_letters.py — One-shot backfill for leads with
NULL cover_letter_subject/body.

History: before this script existed, find_more_leads.py /
ingest_fresh_leads.py / bin/ingest_scout_reports.py inserted lead
rows with NULL cover_letter_*. The email path's fallback in
autopilot._send_one used a generic "Avilx × {company}" subject
that lacked the [Avilx Pod Pitch] / [Personal Application]
mode prefix, weakening open rates and confusing recipients.

This script:
  1. Selects all leads where cover_letter_subject IS NULL OR = ''
     AND cover_letter_body IS NULL OR = ''
  2. Re-renders the cover letter using cover_letter.render_for_mode
  3. UPDATEs the row

Idempotent — running it twice is safe (no-op on second run).

Run:
    python3 bin/backfill_cover_letters.py             # live update
    python3 bin/backfill_cover_letters.py --dry       # preview only
    python3 bin/backfill_cover_letters.py --limit 50  # cap per-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from cover_letter import render_for_mode
from db.lead_store import get_cursor


def _pick_leads(limit: int) -> list[dict]:
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, company, role, jd_text, apply_mode,
                   cover_letter_subject, cover_letter_body
            FROM leads
            WHERE (cover_letter_subject IS NULL OR cover_letter_subject = ''
                   OR cover_letter_body IS NULL OR cover_letter_body = '')
            ORDER BY id
            LIMIT %s
        """, (limit,))
        return [dict(r) for r in cur.fetchall()]


def _update(lead_id: int, subj: str, body: str) -> None:
    with get_cursor() as cur:
        cur.execute("""
            UPDATE leads
            SET cover_letter_subject = %s,
                cover_letter_body    = %s
            WHERE id = %s
        """, (subj, body, lead_id))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry", action="store_true",
                   help="Preview what would be re-rendered, no UPDATEs")
    p.add_argument("--limit", type=int, default=1000,
                   help="Max leads to backfill in this run (default 1000)")
    args = p.parse_args()

    leads = _pick_leads(args.limit)
    if not leads:
        print("✅ No leads need backfill.")
        return 0

    print(f"📝 Backfilling {len(leads)} leads with NULL/empty cover letter…")
    updated = 0
    skipped = 0
    for lead in leads:
        try:
            subj, body, _html = render_for_mode({
                "company": lead.get("company") or "",
                "role": lead.get("role") or "",
                "jd_text": lead.get("jd_text") or "",
                "apply_mode": lead.get("apply_mode") or "pitch_pod",
            })
        except Exception as e:
            print(f"  ❌ id={lead['id']:4d} {lead.get('company','?')[:25]:25s} render error: {e}")
            skipped += 1
            continue

        if not subj or not body:
            print(f"  ⚠️  id={lead['id']:4d} {lead.get('company','?')[:25]:25s} empty render")
            skipped += 1
            continue

        if args.dry:
            print(f"  [dry] id={lead['id']:4d} {(lead.get('apply_mode') or '?'):15s} "
                  f"{lead.get('company','?')[:25]:25s} → {subj[:65]}")
            updated += 1
            continue

        _update(lead["id"], subj, body)
        updated += 1
        if updated <= 5 or updated % 25 == 0:
            print(f"  ✅ id={lead['id']:4d} {(lead.get('apply_mode') or '?'):15s} "
                  f"{lead.get('company','?')[:25]:25s} → {subj[:65]}")

    print(f"\n→ backfilled: {updated}  skipped: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
