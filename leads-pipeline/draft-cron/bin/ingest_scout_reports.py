#!/usr/bin/env python3
"""
bin/ingest_scout_reports.py — Auto-ingest lead-finder-scout reports.

Scout agent writes a JSON report to /tmp/lead-scout-report.json after
each run. This script watches for that file (or any *.json in the
watch dir), parses it, and queues the leads via the same path as
ingest_fresh_leads.py — but without the manual copy/paste.

Run modes:
    python3 bin/ingest_scout_reports.py           # one-shot: ingest any pending
    python3 bin/ingest_scout_reports.py --watch   # loop, ingest new files

Source shapes accepted:
    1) {"top_leads": [{...}, {...}]}            — agent's primary output
    2) [{...}, {...}]                           — bare list
    3) {"leads": [...]}                         — wrapped list

Each lead dict must have at least: company, role.
Optional: contact_email, source_url, jd_text, source, fit_score, fit_reason
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

WATCH_DIRS = [
    Path("/tmp"),
    Path("/private/tmp"),
    HERE,  # scout might write here too
]
DONE_MARKER_SUFFIX = ".ingested"


def _normalize_payload(data) -> list[dict]:
    """Pull a list of lead dicts out of any of the 3 supported shapes."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("top_leads", "leads", "results", "hits"):
            if isinstance(data.get(k), list):
                return data[k]
    return []


def _ingest_one(path: Path) -> tuple[int, int]:
    """Ingest a single scout report. Returns (inserted, skipped_dup)."""
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        print(f"  [scout] {path.name}: parse error: {e}")
        return 0, 0
    leads = _normalize_payload(data)
    if not leads:
        print(f"  [scout] {path.name}: no leads found in payload")
        return 0, 0
    print(f"  [scout] {path.name}: {len(leads)} candidate(s)")

    from db.lead_store import get_cursor
    import re
    import secrets

    # Existing (company, email) keys for dedup
    existing = set()
    with get_cursor() as cur:
        cur.execute("""
            SELECT LOWER(company) AS co, LOWER(contact_email) AS em
            FROM leads
            WHERE contact_email IS NOT NULL
        """)
        for r in cur.fetchall():
            existing.add((r["co"] or "", r["em"] or ""))

    inserted = 0
    skipped = 0
    for ld in leads:
        co = (ld.get("company") or "").strip()
        role = (ld.get("role") or "").strip()
        em = (ld.get("contact_email") or "").strip()
        if not co or not role:
            continue
        # In-app dedup: (company, email) — same as the DB index for the
        # common case. Leads without an email are also allowed through
        # (and won't conflict at the DB level since the partial index
        # requires contact_email IS NOT NULL).
        key = (co.lower(), em.lower())
        if em and key in existing:
            skipped += 1
            continue
        # Derive short id
        slug = re.sub(r"[^a-z0-9]+", "-", co.lower())[:12].strip("-") or "lead"
        tid = f"{slug}-{secrets.token_hex(3)}"
        try:
            with get_cursor() as cur:
                cur.execute("""
                    INSERT INTO leads
                        (tracking_id, company, role, contact_email,
                         source_url, jd_text, source, apply_mode, status,
                         created_at, updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,'apply_personal','pending',
                            NOW(), NOW())
                    ON CONFLICT (LOWER(company), LOWER(contact_email), LOWER(role))
                    WHERE contact_email IS NOT NULL
                      AND role IS NOT NULL
                      AND role != ''
                    DO NOTHING
                    RETURNING id
                """, (
                    tid, co, role, em or None,
                    ld.get("source_url", ""),
                    (ld.get("jd_text", "") or "")[:500],
                    ld.get("source", "scout_agent"),
                ))
                row = cur.fetchone()
            if row:
                inserted += 1
                if em:
                    existing.add(key)
                existing.add(key)
                print(f"    ✅ {co[:30]:30s} {role[:35]:35s} {em or '(no email)'}")
        except Exception as e:
            print(f"    ❌ {co[:30]:30s} {e}")
    return inserted, skipped


def _find_pending() -> list[Path]:
    """Find scout reports that haven't been ingested yet."""
    out = []
    for d in WATCH_DIRS:
        if not d.exists():
            continue
        for p in d.glob("lead-scout-*.json"):
            if not p.name.endswith(DONE_MARKER_SUFFIX):
                out.append(p)
    return out


def _mark_done(path: Path) -> None:
    """Move/rename to mark as ingested (idempotency)."""
    done = path.with_suffix(path.suffix + DONE_MARKER_SUFFIX)
    try:
        path.rename(done)
    except Exception:
        # Cross-device or perm issue — write a sidecar marker
        done.write_text(str(time.time()))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--watch", action="store_true",
                   help="Loop forever, ingest any new scout reports")
    p.add_argument("--interval", type=int, default=60,
                   help="Watch poll interval in seconds (default 60)")
    args = p.parse_args()

    if not args.watch:
        files = _find_pending()
        if not files:
            print("No pending scout reports.")
            return 0
        total_in, total_dup = 0, 0
        for f in files:
            ins, dup = _ingest_one(f)
            total_in += ins
            total_dup += dup
            if ins or not dup:
                _mark_done(f)
        print(f"\n📊 Total: inserted={total_in}, dup={total_dup}")
        return 0

    print(f"👀 Watching for /tmp/lead-scout-*.json every {args.interval}s")
    while True:
        for f in _find_pending():
            print(f"📥 Found {f}")
            ins, dup = _ingest_one(f)
            if ins or not dup:
                _mark_done(f)
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
