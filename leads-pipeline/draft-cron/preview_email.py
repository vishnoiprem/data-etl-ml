#!/usr/bin/env python3
"""
preview_email.py — Render the exact HTML email that autopilot would send,
for a given lead (or a sample), and save it to .preview/ so you can open
in a browser.

Usage:
  python3 preview_email.py --sample
  python3 preview_email.py --lead-id 128
  python3 preview_email.py --lead-id 128 --out /tmp/preview.html
"""

import os
import sys
import argparse
from pathlib import Path
from html import escape as h

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

OUT_DIR = HERE / ".preview"
OUT_DIR.mkdir(exist_ok=True)


def _sample_lead():
    return {
        "id": 0,
        "company": "RealResponse",
        "role": "Product Engineer (AI/RAG) — Remote (US)",
        "contact_email": "jobs@realresponse.com",
        "tracking_id": "realresp-a3k9",
        "jd_text": "Looking for a Product Engineer to build production RAG pipelines on top of OpenAI and Pinecone for our healthtech customers. HIPAA-aware.",
        "cover_letter_body": (
            "Hi RealResponse team,\n\n"
            "Saw the Product Engineer (AI/RAG) — Remote (US) role — production RAG. Quick context if useful: I'm Prem, I run Avilx (avilx.com), a global Build·Deploy·Engineers pod out of Ha Noi. 6-20 senior engineers, AI/Data/ML/Cloud, **Databricks Champion** team, 7+ clouds (AWS · Azure · GCP · Tencent · Alibaba), 8+ yrs avg, regulated-industry work.\n\n"
            "Stack overlap I noticed: rag, llm, openai, anthropic, vector, python, aws.\n\n"
            "If your timeline is tight, happy to run a 4-week pilot pod or staff-aug a senior — 2-week kickoff, remote delivery, NDA + IP clean. 15-min call this week worth it?\n\n"
            "Prem Vishnoi\n"
            "Avilx — Global Build · Deploy · Engineers\n"
            "(AI · Data · ML · Cloud · Databricks · 7+ clouds)\n"
            "Delivery: China · APAC · US · EU | HQ: Ha Noi, Vietnam\n"
            "hello@avilx.com | wa.me/6592716405 | https://avilx.com"
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true",
                    help="Use a built-in sample lead")
    ap.add_argument("--lead-id", type=int,
                    help="Build preview for a specific lead from Postgres")
    ap.add_argument("--out", type=str,
                    help="Output HTML path (default: .preview/lead_<id>.html)")
    args = ap.parse_args()

    if args.sample:
        lead = _sample_lead()
    elif args.lead_id:
        from db.lead_store import get_cursor
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, company, role, contact_email, jd_text,
                       cover_letter_body, tracking_id
                FROM leads WHERE id = %s
            """, (args.lead_id,))
            row = cur.fetchone()
        if not row:
            print(f"No lead with id={args.lead_id}")
            return 1
        lead = dict(row)
    else:
        ap.print_help()
        return 1

    # Render the HTML exactly like autopilot._send_one would
    import autopilot
    html = autopilot._render_email_html(lead)

    out_path = Path(args.out) if args.out else OUT_DIR / f"lead_{lead.get('id', 'sample')}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"✅ Wrote {len(html):,} bytes to {out_path}")
    print(f"   Open: open {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
