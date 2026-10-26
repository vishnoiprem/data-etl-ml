#!/usr/bin/env python3
"""
backfill_emails.py — For pending leads with no contact_email, try to derive one
from the company name using the known-domain map in find_more_leads.py.

Idempotent. Skips companies whose domain is in BOUNCE_DENY. Respects
the (LOWER(company), LOWER(contact_email)) unique index.

Run:  python3 backfill_emails.py
       python3 backfill_emails.py --verbose
"""

import sys
import argparse
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


def backfill(verbose=False, limit=500):
    from db.lead_store import get_cursor
    from find_more_leads import derive_email_from_company, BOUNCE_DENY
    from state.bounce_deny_store import BOUNCE_DENY as PERSISTED_DENY
    from refine_pipeline import dedup_and_deny

    # First, refresh BOUNCE_DENY from current bounced leads (idempotent)
    dedup_and_deny(verbose=verbose)

    # The PERSISTED_DENY covers anything added since this process started.
    effective_deny = BOUNCE_DENY | PERSISTED_DENY

    count_updated = 0
    count_skipped_no_match = 0
    count_skipped_bounce_deny = 0
    count_skipped_collision = 0
    count_skipped_duplicate_company = 0

    # First pass: figure out which (company → email) pairs have multiple
    # pending-no-email leads. For those, only backfill the lowest id.
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, company FROM leads
            WHERE status = 'pending'
              AND (contact_email IS NULL OR contact_email = '')
            ORDER BY id
            LIMIT %s
        """, (limit,))
        leads = [dict(r) for r in cur.fetchall()]

    # Group by company; only the lowest id wins
    by_company = {}
    for lead in leads:
        by_company.setdefault(lead["company"].lower(), []).append(lead)
    eligible = set()
    for ls in by_company.values():
        ls.sort(key=lambda l: l["id"])
        eligible.add(ls[0]["id"])
        if len(ls) > 1:
            count_skipped_duplicate_company += len(ls) - 1

    if verbose:
        print(f"  [backfill] candidates: {len(leads)}  "
              f"eligible: {len(eligible)}  "
              f"skipped (dup-company): {count_skipped_duplicate_company}")

    for lead in leads:
        if lead["id"] not in eligible:
            continue
        em = derive_email_from_company(lead["company"])
        if not em:
            count_skipped_no_match += 1
            continue
        # derive_email_from_company already checks BOUNCE_DENY but
        # we double-check here just in case the map was updated.
        domain = em.split("@", 1)[1].lower()
        if domain in effective_deny:
            count_skipped_bounce_deny += 1
            continue
        # Check collision: same (company, email) on a different lead
        with get_cursor() as cur:
            cur.execute("""
                SELECT 1 FROM leads
                WHERE LOWER(company) = LOWER(%s)
                  AND LOWER(contact_email) = LOWER(%s)
                  AND id != %s
                LIMIT 1
            """, (lead["company"], em, lead["id"]))
            if cur.fetchone():
                count_skipped_collision += 1
                continue
            cur.execute("""
                UPDATE leads SET contact_email = %s, updated_at = NOW()
                WHERE id = %s AND status = 'pending'
            """, (em, lead["id"]))
        count_updated += 1
        if verbose:
            print(f"  [backfill] #{lead['id']:3d} {lead['company'][:30]:30s} → {em}")

    if verbose:
        print(f"  [backfill] updated={count_updated} "
              f"no_match={count_skipped_no_match} "
              f"deny={count_skipped_bounce_deny} "
              f"collision={count_skipped_collision} "
              f"dup_company={count_skipped_duplicate_company}")
    return count_updated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--limit", type=int, default=500)
    args = ap.parse_args()
    n = backfill(verbose=args.verbose, limit=args.limit)
    print(f"\nbackfill_emails: updated {n} leads")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
