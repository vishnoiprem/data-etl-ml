"""
backfill_to_pg.py — One-time script to migrate leads.json leads into Postgres.
Run once after setting up the DB. Idempotent (won't duplicate by email).
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from db.lead_store import insert_lead, find_duplicate, update_status, stats  # noqa


def main():
    leads_path = HERE / "leads.json"
    if not leads_path.exists():
        print("No leads.json found")
        return

    leads = json.load(open(leads_path))
    print(f"Migrating {len(leads)} leads from leads.json to Postgres...\n")

    added = 0
    skipped = 0
    failed = 0
    for lead in leads:
        company = lead.get("company") or "Unknown"
        email = lead.get("contact_email") or f"unknown-{company.lower().replace(' ', '')}@placeholder"
        # Dedup
        dup = find_duplicate(company, email, lead.get("role", ""))
        if dup:
            skipped += 1
            # Update status from leads.json if newer
            status = lead.get("status", "pending")
            if status in ("sent_email", "failed", "replied") and dup.get("status") == "pending":
                update_status(dup["id"], status)
            continue
        try:
            pg_id = insert_lead(lead, source="backfill_from_leads_json")
            # Update status if not pending
            status = lead.get("status", "pending")
            if status and status != "pending":
                update_status(pg_id, status)
            added += 1
            print(f"  + {company} ({lead.get('role', '?')}) → pg_id={pg_id}")
        except Exception as e:
            failed += 1
            print(f"  ! {company} ({lead.get('role', '?')}) failed: {e}")

    print(f"\nDone: added={added}, skipped={skipped}, failed={failed}")
    print(f"\n📊 Final DB stats: {stats()}")


if __name__ == "__main__":
    main()
