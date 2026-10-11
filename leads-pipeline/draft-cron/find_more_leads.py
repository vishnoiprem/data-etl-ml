#!/usr/bin/env python3
"""
find_more_leads.py — Quick wrapper that runs the autopilot scrape+enrich+queue
phases (no email sends) to refresh the lead pool. The auto_loop calls this
every 5 iterations.

Run:  python3 find_more_leads.py
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


def main() -> int:
    import autopilot
    # Build args namespace mirroring the autopilot CLI parser
    class Args:
        scrape = True
        enrich = False
        email = False
        dry = False
        max_emails = 0
        no_lock = False
        no_bounce_sync = True
        scrape_only = True
        email_only = False

    args = Args()
    try:
        # Use the autopilot internal pipeline directly
        report = {"started_at": __import__("datetime").datetime.now().isoformat()}
        print("[find_more_leads] scraping public sources...")
        from autopilot import scrape_all, enrich_url_only_lead, queue_leads
        leads = scrape_all()
        print(f"[find_more_leads] scraped {len(leads)} candidates")
        for ld in leads:
            if not ld.get("contact_email") and ld.get("source_url"):
                try:
                    enrich_url_only_lead(ld)
                except Exception as e:
                    pass
        with_email = sum(1 for l in leads if l.get("contact_email"))
        print(f"[find_more_leads] {with_email}/{len(leads)} have email now")
        ins, skp, err = queue_leads(leads, dry=False)
        print(f"[find_more_leads] inserted {ins}, skipped {skp} dup, errored {err}")
        return 0
    except Exception as e:
        print(f"[find_more_leads] error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
