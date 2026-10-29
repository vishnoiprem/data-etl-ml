#!/usr/bin/env python3
"""
refine_pipeline.py — Refine and enrich pending leads without sending email.
Use during Google's 24h local cooldown period to keep the project improving.

What it does each run:
  1. Finds pending leads without a tailored cover letter → writes one
  2. Finds pending leads without a tailored resume → tailors one
  3. Updates the lead's `cover_letter_body` and `resume_file` columns
  4. Bounces: scans Gmail IMAP and marks any new bounced leads
  5. Finds more leads (job boards + clients + AI-native) and inserts them
  6. Re-derives better recruiter emails where the current one is generic

Run:  python3 refine_pipeline.py
       python3 refine_pipeline.py --enrich-only
       python3 refine_pipeline.py --leads-only
"""

import os
import re
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


def sync_bounces(verbose=True):
    try:
        from check_bounces import scan_bounces, mark_bounced
        bounce_map, _ = scan_bounces(since_days=7)
        if bounce_map:
            counts = mark_bounced(bounce_map, dry=False)
            if verbose:
                print(f"  [bounces] marked={counts.get('marked', 0)} "
                      f"already={counts.get('already_bounced', 0)} "
                      f"unknown={counts.get('unknown', 0)}")
        else:
            if verbose:
                print("  [bounces] no new bounces")
    except Exception as e:
        if verbose:
            print(f"  [bounces] error: {e}")


def enrich_pending_leads(verbose=True):
    """For each pending lead:
       - tailor the resume (if not yet tailored)
       - write the cover letter (if not yet written)
       - re-derive a better recruiter email if the current one is generic
    """
    from db.lead_store import get_cursor
    from resume_tailor import tailor_resume, HAVE_DOCX

    if not HAVE_DOCX:
        if verbose:
            print("  [enrich] python-docx not available, skipping resume tailoring")
        return

    count_tailored = 0
    count_cover = 0
    count_email = 0

    with get_cursor() as cur:
        # Pending leads w/ email
        cur.execute("""
            SELECT id, company, role, contact_email, jd_text, source_url,
                   cover_letter_body, resume_file
            FROM leads
            WHERE contact_email IS NOT NULL AND contact_email != ''
              AND status = 'pending'
            ORDER BY id
        """)
        leads = cur.fetchall()

    for r in leads:
        lead = dict(r)

        # 1. Tailor resume (if not yet done)
        if not lead.get("resume_file"):
            try:
                p = tailor_resume(lead)
                if p:
                    rel = p.name
                    with get_cursor() as cur:
                        cur.execute("""
                            UPDATE leads SET resume_file = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (rel, lead["id"]))
                    count_tailored += 1
                    if verbose:
                        print(f"  [resume] #{lead['id']:3d} {lead['company'][:25]:25s} → {rel}")
            except Exception as e:
                if verbose:
                    print(f"  [resume] #{lead['id']} error: {e}")

        # 2. Write cover letter (if not yet written)
        if not lead.get("cover_letter_body"):
            try:
                body = _make_cover_letter(lead)
                with get_cursor() as cur:
                    cur.execute("""
                        UPDATE leads SET cover_letter_body = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (body, lead["id"]))
                count_cover += 1
                if verbose:
                    print(f"  [cover]  #{lead['id']:3d} {lead['company'][:25]:25s} → {len(body)} chars")
            except Exception as e:
                if verbose:
                    print(f"  [cover]  #{lead['id']} error: {e}")

        # 3. Try better email derivation (e.g. talent@ instead of careers@)
        better = _better_email(lead)
        if better and better.lower() != (lead.get("contact_email") or "").lower():
            # Skip if the new email would collide with an existing lead
            with get_cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM leads
                    WHERE LOWER(company) = LOWER(%s)
                      AND LOWER(contact_email) = LOWER(%s)
                      AND id != %s
                    LIMIT 1
                """, (lead["company"], better, lead["id"]))
                if cur.fetchone():
                    # New email already exists for this company — skip
                    continue
                cur.execute("""
                    UPDATE leads SET contact_email = %s, updated_at = NOW()
                    WHERE id = %s AND status = 'pending'
                """, (better, lead["id"]))
            count_email += 1
            if verbose:
                print(f"  [email]  #{lead['id']:3d} {lead['company'][:25]:25s} "
                      f"{lead['contact_email']} → {better}")

    if verbose:
        print(f"  [enrich] tailored={count_tailored} cover={count_cover} better_email={count_email}")


# Common company-domain → preferred email prefix map.
# If a lead has a generic careers@ but the company prefers talent@ or jobs@,
# we can swap to a higher-deliverability address.
PREFIX_HINTS = {
    # AI-native labs / model shops
    "scale.com": "ai-jobs",
    "anthropic.com": "ai-jobs",
    "openai.com": "ai-jobs",
    "deepmind.google": "research-jobs",
    "cohere.com": "talent",
    "mistral.ai": "talent",
    "lambda.ai": "talent",
    "together.ai": "talent",
    "replicate.com": "talent",
    "modal.com": "jobs",
    "perplexity.ai": "jobs",
    "huggingface.co": "jobs",
    "crossinghurdles.com": "talent",
    "deepgram.com": "jobs",
    "assemblyai.com": "jobs",
    "elevenlabs.io": "jobs",
    "play.ht": "jobs",
    "runwayml.com": "jobs",
    # Data / analytics / observability startups (all bounced on careers@)
    "datadoghq.com": "talent",
    "toptal.com": "talent",
    "montecarlodata.com": "talent",
    "hex.tech": "jobs",
    "fivetran.com": "talent",
    "getdbt.com": "talent",
    "getcensus.com": "talent",
    "hightouch.com": "talent",
    "soda.io": "talent",
    "airbyte.com": "talent",
    "dagster.io": "talent",
    "prefect.io": "talent",
    "mage.ai": "talent",
    "datafold.com": "talent",
    "starburst.io": "talent",
    "snowflake.com": "talent",
    "databricks.com": "talent",
    # Recruiting marketplaces / staffing firms (mostly bounce)
    "lemon.io": "hello",
    "stickermule.com": "hello",
    "siho.io": "hello",
    "stearnsnutrition.com": "hello",
    "edfinity.com": "hello",
    # Other known-talent
    "airbnb.com": "talent",
    "stripe.com": "talent",
    "cloudflare.com": "talent",
    "vercel.com": "talent",
    "figma.com": "talent",
    "notion.so": "talent",
    "linear.app": "talent",
    "supabase.io": "talent",
    "railway.app": "talent",
    "render.com": "talent",
    "fly.io": "talent",
    "samsara.com": "talent",
    "dremio.com": "talent",
    "anyscale.com": "talent",
    "glean.com": "talent",
    "wandb.ai": "talent",
    "weights.com": "talent",
}


def _better_email(lead):
    """If the lead's current email is a generic careers@ on a known domain
    that prefers a different prefix, suggest a better one.

    Returns None if the *target* domain is in BOUNCE_DENY or any lead at
    that domain has status='bounced' — swapping to a dead address is
    strictly worse than leaving the lead alone.
    """
    from state.bounce_deny_store import BOUNCE_DENY as _PERSISTED_DENY

    em = (lead.get("contact_email") or "").lower()
    if "@" not in em:
        return None
    prefix, _, domain = em.partition("@")
    if domain not in PREFIX_HINTS:
        return None
    new_prefix = PREFIX_HINTS[domain]
    if prefix == new_prefix:
        return None
    target = f"{new_prefix}@{domain}"

    # Hard guard: never swap to a known-bad domain
    if domain in _PERSISTED_DENY:
        return None
    # DB guard: if any lead with this domain bounced, don't recreate
    # that address. Cache the result in-process for the rest of the run.
    if not hasattr(_better_email, "_bounced_domain_cache"):
        _better_email._bounced_domain_cache = set()
    cache = _better_email._bounced_domain_cache
    if domain in cache:
        return None
    from db.lead_store import get_cursor
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT 1 FROM leads
                WHERE SPLIT_PART(LOWER(contact_email), '@', 2) = %s
                  AND status = 'bounced'
                LIMIT 1
            """, (domain,))
            if cur.fetchone():
                cache.add(domain)
                return None
    except Exception:
        # DB hiccup — be conservative and don't swap
        return None
    return target


def _make_cover_letter(lead):
    """Write a 4-paragraph Avilx cover letter tailored to this lead.

    Delegates to cover_letter.py so any edit there shows up everywhere
    (autopilot, refine_pipeline, tests, preview).
    """
    from cover_letter import render_text_body
    return render_text_body(lead)


def _extract_stack_overlap(jd):
    """Pull a list of recognizable tech terms from a JD for the cover letter."""
    from cover_letter import _extract_stack_overlap as _impl
    return _impl(jd)


def find_more_leads(verbose=True):
    if verbose:
        print("  [find_more_leads] running...")
    import subprocess
    p = HERE / "find_more_leads.py"
    if not p.exists():
        return
    try:
        r = subprocess.run(
            [sys.executable, str(p)],
            cwd=str(HERE),
            capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        if verbose:
            print(f"    [find_more_leads] timeout after 180s — skipping")
        return
    if verbose and r.returncode == 0:
        # tail summary line
        for line in r.stdout.splitlines()[-3:]:
            print(f"    {line}")
    elif verbose:
        print(f"    [find_more_leads] exit={r.returncode} stderr={r.stderr[:200]}")


def find_more_clients(verbose=True):
    if verbose:
        print("  [find_clients] running...")
    import subprocess
    p = HERE / "find_clients.py"
    if not p.exists():
        return
    try:
        r = subprocess.run(
            [sys.executable, str(p)],
            cwd=str(HERE),
            capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        if verbose:
            print(f"    [find_clients] timeout after 180s — skipping")
        return
    if verbose and r.returncode == 0:
        for line in r.stdout.splitlines()[-3:]:
            print(f"    {line}")
    elif verbose:
        print(f"    [find_clients] exit={r.returncode} stderr={r.stderr[:200]}")


def dedup_and_deny(verbose=True):
    """Auto-derive the bounce deny list from actual bounces in DB and
    persist it to state/bounce_deny.json so subprocesses (find_more_leads,
    find_clients, backfill_emails) see the same denylist."""
    from db.lead_store import get_cursor
    from state.bounce_deny_store import BOUNCE_DENY, add as deny_add
    added = 0
    with get_cursor() as cur:
        cur.execute("""
            SELECT SPLIT_PART(contact_email, '@', 2) AS domain, COUNT(*)
            FROM leads
            WHERE status = 'bounced'
            GROUP BY 1 HAVING COUNT(*) >= 1
        """)
        for r in cur.fetchall():
            dom = (r["domain"] or "").lower()
            if dom and dom not in BOUNCE_DENY:
                if deny_add(dom):
                    added += 1
    # Also keep the legacy in-memory BOUNCE_DENY in find_more_leads
    # in sync so the same process doesn't have to reload.
    try:
        import find_more_leads as fml
        fml.BOUNCE_DENY |= BOUNCE_DENY
    except Exception:
        pass
    if verbose:
        print(f"  [deny] bounce deny list now has {len(BOUNCE_DENY)} domains (+{added})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--enrich-only", action="store_true",
                    help="Only enrich pending leads, no scraping")
    ap.add_argument("--leads-only", action="store_true",
                    help="Only find more leads, no enrichment")
    args = ap.parse_args()

    print(f"\n{'='*60}\n🔧 AVILX REFINE — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}\n")

    if not args.leads_only:
        print("1. Bounce sync")
        sync_bounces()
        print("\n2. Enrich pending leads (resume + cover + better email)")
        enrich_pending_leads()
        print("\n3. Update bounce-deny list")
        dedup_and_deny()

    if not args.enrich_only:
        print("\n4. Find more leads (job boards)")
        find_more_leads()
        print("\n5. Find more clients (AI-native + HN + YC + Bing)")
        find_more_clients()

    # Print report
    from daily_report import main as report
    print("\n6. Daily report")
    report()

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
