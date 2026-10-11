#!/usr/bin/env python3
"""One-shot preview: which pending leads would PREFIX_HINTS swap?"""
import sys
sys.path.insert(0, '/Users/vishnoiprem/PycharmProjects/data-etl-ml/leads-pipeline/draft-cron')
from db.lead_store import get_cursor
from refine_pipeline import PREFIX_HINTS

domains = list(PREFIX_HINTS.keys())
with get_cursor() as cur:
    cur.execute("""
        SELECT id, company, contact_email, status FROM leads
        WHERE status IN ('pending','sent_email','bounced')
          AND contact_email LIKE 'careers@%'
          AND LOWER(SPLIT_PART(contact_email, '@', 2)) = ANY(%s)
        ORDER BY status, id
    """, (domains,))
    rows = cur.fetchall()
    print(f'{len(rows)} leads would be affected by the swap:')
    by_status = {}
    for r in rows:
        by_status.setdefault(r['status'], []).append(r)
    for st in ('pending', 'sent_email', 'bounced'):
        rs = by_status.get(st, [])
        if rs:
            print(f'  {st}: {len(rs)}')
    print()
    for r in rows:
        em = r['contact_email']
        prefix, _, dom = em.partition('@')
        new_em = f'{PREFIX_HINTS[dom]}@{dom}'
        flag = {'pending': 'P', 'sent_email': 'S', 'bounced': 'B'}[r['status']]
        print(f'  [{flag}] #{r["id"]:3d} {r["company"][:30]:30s} {em} -> {new_em}')
