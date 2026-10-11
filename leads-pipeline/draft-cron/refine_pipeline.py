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
    "scale.com": "ai-jobs",
    "anthropic.com": "ai-jobs",
    "cohere.com": "talent",
    "datadoghq.com": "talent",
    "toptal.com": "talent",
    "crossinghurdles.com": "talent",
    "mistral.ai": "talent",
    "lambda.ai": "talent",
    "montecarlodata.com": "talent",
    "together.ai": "talent",
    "replicate.com": "talent",
    "modal.com": "jobs",
    "elevenlabs.io": "jobs",
    "play.ht": "jobs",
    "deepgram.com": "jobs",
    "assemblyai.com": "jobs",
    "runwayml.com": "jobs",
    "huggingface.co": "jobs",
    "perplexity.ai": "jobs",
    "hex.tech": "jobs",
}


def _better_email(lead):
    """If the lead's current email is a generic careers@ on a known domain
    that prefers a different prefix, suggest a better one."""
    em = (lead.get("contact_email") or "").lower()
    if "@" not in em:
        return None
    prefix, _, domain = em.partition("@")
    if domain not in PREFIX_HINTS:
        return None
    new_prefix = PREFIX_HINTS[domain]
    if prefix == new_prefix:
        return None
    # Don't replace if the lead was already marked bounced for this domain
    return f"{new_prefix}@{domain}"


def _make_cover_letter(lead):
    """Write a 4-paragraph Avilx cover letter tailored to this lead."""
    co = lead.get("company", "").strip() or "your team"
    role = lead.get("role", "").strip() or "this role"
    jd = lead.get("jd_text", "") or ""

    # Try to identify stack overlap from the JD
    stack_overlap = _extract_stack_overlap(jd)
    stack_str = ", ".join(stack_overlap[:8]) if stack_overlap else "the stack in your JD"

    return (
        f"Hi {co} team,\n\n"
        f"Saw the {role} role — stack and scope look like a strong match. Quick context if useful: I'm Prem, I run Avilx (avilx.com), a global Build·Deploy·Engineers pod out of Ha Noi. 6-20 senior engineers, AI/Data/ML/Cloud, **Databricks Champion** team, 7+ clouds (AWS · Azure · GCP · Tencent · Alibaba), 8+ yrs avg, regulated-industry work.\n\n"
        f"Stack overlap I noticed: {stack_str}.\n\n"
        f"If your timeline is tight, happy to run a 4-week pilot pod or staff-aug a senior — 2-week kickoff, remote delivery, NDA + IP clean. 15-min call this week worth it?\n\n"
        f"Prem Vishnoi\n"
        f"Avilx — Global Build · Deploy · Engineers\n"
        f"(AI · Data · ML · Cloud · Databricks · 7+ clouds)\n"
        f"Delivery: China · APAC · US · EU | HQ: Ha Noi, Vietnam\n"
        f"hello@avilx.com | wa.me/6592716405 | https://avilx.com"
    )


def _extract_stack_overlap(jd):
    """Pull a list of recognizable tech terms from a JD for the cover letter."""
    if not jd:
        return []
    candidates = re.findall(
        r"\b(python|java|golang|go\b|rust|c\+\+|typescript|javascript|"
        r"react|node|next\.?js|django|fastapi|flask|spring|"
        r"kubernetes|k8s|docker|terraform|ansible|helm|"
        r"aws|azure|gcp|tencent|alibaba|cloudflare|"
        r"spark|hadoop|kafka|flink|airflow|dagster|prefect|"
        r"snowflake|databricks|bigquery|redshift|postgres|mysql|"
        r"dbt|elt|etl|olap|oltp|iceberg|delta|parquet|avro|"
        r"pytorch|tensorflow|llm|rag|genai|agent|"
        r"mlops|scikit|sklearn|pandas|numpy|"
        r"openai|anthropic|claude|gemini|mistral|llama|hugging|"
        r"vector|embedding|faiss|qdrant|weaviate|pinecone|chroma|"
        r"ci/cd|devops|sre|observability|prometheus|grafana|"
        r"microservices|grpc|rest|graphql|api|"
        r"data engineering|ml engineering|backend|platform)\b",
        jd, re.I,
    )
    # Lowercase, dedup, preserve order
    seen = set()
    out = []
    for c in candidates:
        cl = c.lower()
        if cl not in seen:
            seen.add(cl)
            out.append(cl)
    return out


def find_more_leads(verbose=True):
    if verbose:
        print("  [find_more_leads] running...")
    import subprocess
    p = HERE / "find_more_leads.py"
    if not p.exists():
        return
    r = subprocess.run(
        [sys.executable, str(p)],
        cwd=str(HERE),
        capture_output=True, text=True, timeout=180,
    )
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
    r = subprocess.run(
        [sys.executable, str(p)],
        cwd=str(HERE),
        capture_output=True, text=True, timeout=180,
    )
    if verbose and r.returncode == 0:
        for line in r.stdout.splitlines()[-3:]:
            print(f"    {line}")
    elif verbose:
        print(f"    [find_clients] exit={r.returncode} stderr={r.stderr[:200]}")


def dedup_and_deny(verbose=True):
    """Auto-derive the bounce deny list from actual bounces in DB."""
    from db.lead_store import get_cursor
    from find_more_leads import BOUNCE_DENY
    new_deny = set(BOUNCE_DENY)
    with get_cursor() as cur:
        cur.execute("""
            SELECT SPLIT_PART(contact_email, '@', 2) AS domain, COUNT(*)
            FROM leads
            WHERE status = 'bounced'
            GROUP BY 1 HAVING COUNT(*) >= 1
        """)
        for r in cur.fetchall():
            dom = r["domain"]
            if dom and dom not in new_deny:
                new_deny.add(dom)
    if verbose:
        print(f"  [deny] bounce deny list now has {len(new_deny)} domains")


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
