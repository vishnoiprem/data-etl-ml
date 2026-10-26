#!/usr/bin/env python3
"""
run_loop.py — End-to-end orchestrator: ingest → qualify → outreach → report.

One pass:
  1. Scrape every source (signals.ingest_all)
  2. Upsert into the SQLite pipeline (dedup by fingerprint)
  3. Qualify every 'new' lead via LLM (qualifier.qualify_batch)
  4. Draft outreach for leads with score >= MIN_SCORE (outreach.draft_batch)
  5. Print the dashboard

For production: also send emails + mark rows 'sent'. For the demo, we
stop at "draft" and let a human review before clicking send. That's
intentional — the consultant wants to read the email first.

Usage:
  python scripts/run_loop.py           # one pass, default settings
  python scripts/run_loop.py --loop    # run forever, sleep 1h between passes
  python scripts/run_loop.py --min-score 50 --limit 5
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Make `src/` importable when running from project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dashboard import print_dashboard  # noqa: E402
from outreach import draft, draft_batch  # noqa: E402
from pipeline import Pipeline  # noqa: E402
from qualifier import qualify_batch, top_n  # noqa: E402
from router import get_default_router  # noqa: E402
from signals import Lead, ingest_all, write_sample_data  # noqa: E402


def one_pass(db_path: str, min_score: int, limit: int, verbose: bool = True) -> dict:
    """Run one end-to-end pass. Returns a small summary dict."""
    if verbose:
        print("→ Ingesting signals...")
    write_sample_data()  # idempotent; no-op once sample_data/ exists
    leads = ingest_all()
    if verbose:
        print(f"  scraped {len(leads)} leads")

    p = Pipeline(db_path=db_path)
    p.upsert_many(leads)

    # Re-read everything currently in 'new' so we have the full row to rebuild Lead objects.
    new_opps = p.list_by_status("new", limit=500)
    if verbose:
        print(f"→ Qualifying {len(new_opps)} new leads...")

    router = get_default_router()
    if verbose:
        print(f"  router: {getattr(router, 'name', type(router).__name__)}")

    # Rebuild Lead objects + map fingerprint → opp_id in one pass.
    fp_to_id: dict[str, int] = {}
    to_qualify: list[Lead] = []
    for opp in new_opps:
        tags = json.loads(opp.get("tags") or "[]")
        to_qualify.append(Lead(
            source=opp["source"],
            company=opp["company"],
            title=opp["title"] or "",
            url=opp["url"] or "",
            text=opp["text"] or "",
            posted_at=opp["first_seen_at"],
            contact=opp.get("contact"),
            tags=tags,
        ))
        fp_to_id[lead_fingerprint(opp)] = opp["id"]

    # qualify_batch returns the same leads sorted by score desc.
    qualified_pairs = qualify_batch(to_qualify, router)

    # Persist score + reasons for every lead; draft an email only for warm/hot.
    drafted = 0
    for lead, q in qualified_pairs:
        opp_id = fp_to_id.get(lead.fingerprint)
        if opp_id is None:
            continue
        email = None
        if q.score >= min_score:
            try:
                email = draft(lead, q, router)
                drafted += 1
            except Exception as e:
                if verbose:
                    print(f"  [outreach] {lead.company}: {e}")
        p.record_qualification(opp_id, q, email=email)

    if verbose:
        n_hot = sum(1 for _, q in qualified_pairs if q.score >= 70)
        n_warm = sum(1 for _, q in qualified_pairs if 40 <= q.score < 70)
        n_cold = len(qualified_pairs) - n_hot - n_warm
        print(f"  qualified: {n_hot} hot, {n_warm} warm, {n_cold} cold")
        print(f"  drafted outreach: {drafted} emails")

    if verbose:
        top = top_n(qualified_pairs, n=limit)
        if top:
            print(f"→ Top {len(top)} (showing subject lines)...")
            for _, q, email in draft_batch(top, router):
                print(f"  • score {q.score:>3} → {email.subject[:70]}")

    if verbose:
        print()
        print_dashboard(db_path=db_path)

    return {
        "scraped": len(leads),
        "qualified": len(qualified_pairs),
        "drafted": drafted,
    }


def lead_fingerprint(opp: dict) -> str:
    """Mirror Lead.fingerprint without needing the dataclass — DB stores
    it already, but the row's fingerprint column is the source of truth
    here so we can match exactly."""
    return opp["fingerprint"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Revenue pipeline orchestrator")
    ap.add_argument("--db", default="pipeline.db", help="SQLite path")
    ap.add_argument("--min-score", type=int, default=40,
                    help="minimum score to draft outreach (default 40)")
    ap.add_argument("--limit", type=int, default=5,
                    help="max number of outreach drafts shown per pass")
    ap.add_argument("--loop", action="store_true",
                    help="run forever, sleeping 1h between passes")
    ap.add_argument("--interval", type=int, default=3600,
                    help="seconds between passes when --loop (default 3600)")
    args = ap.parse_args()

    if args.loop:
        while True:
            try:
                one_pass(args.db, args.min_score, args.limit)
            except KeyboardInterrupt:
                print("\nstopped.")
                return 0
            except Exception as e:
                print(f"[loop] pass failed: {e}", file=sys.stderr)
            print(f"\n[loop] sleeping {args.interval}s... (Ctrl-C to stop)\n")
            time.sleep(args.interval)
    else:
        one_pass(args.db, args.min_score, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
