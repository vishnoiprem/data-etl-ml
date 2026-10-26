#!/usr/bin/env python3
"""
dashboard.py — Single-screen visual summary of the Avilx leads pipeline.

Shows:
  - Lead funnel with bars
  - Key metrics (email coverage, enrichment, bounce/open rate, sends)
  - Top bounced domains
  - Top lead sources
  - Top companies by lead count
  - Recent sends + recent bounces
  - Auto-loop status (pid, uptime, current iteration)
  - Last log lines
  - Git state on the active branch

Run:  python3 dashboard.py
      python3 dashboard.py --json   # machine-readable
"""

import sys
import os
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


def bar(n, max_n=30, char="#"):
    if n <= 0:
        return ""
    return char * min(n, max_n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    from db.lead_store import get_cursor

    data = {"generated_at": datetime.now().isoformat()}

    with get_cursor() as cur:
        # Funnel
        cur.execute("SELECT status, COUNT(*) AS n FROM leads GROUP BY status ORDER BY 2 DESC")
        data["funnel"] = {r["status"]: r["n"] for r in cur.fetchall()}
        data["total"] = sum(data["funnel"].values())

        # Key metrics
        cur.execute("""
            SELECT COUNT(*) AS n FROM leads
            WHERE contact_email IS NOT NULL AND contact_email != ''
              AND status='pending'
        """)
        pe = cur.fetchone()["n"]
        data["pending_with_email"] = pe

        cur.execute("SELECT COUNT(*) AS n FROM leads WHERE status='pending'")
        pp = cur.fetchone()["n"]
        data["pending_total"] = pp

        cur.execute("""
            SELECT COUNT(*) AS n FROM leads
            WHERE status='pending' AND resume_file IS NOT NULL
              AND cover_letter_body IS NOT NULL
        """)
        data["pending_fully_enriched"] = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM leads WHERE status='bounced'")
        data["bounced"] = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM leads WHERE status='sent_email'")
        data["sent_email"] = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM leads WHERE status='opened_url'")
        data["opened_url"] = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM leads WHERE sent_at > NOW() - INTERVAL '24 hours'")
        data["sends_24h"] = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM leads WHERE sent_at > NOW() - INTERVAL '7 days'")
        data["sends_7d"] = cur.fetchone()["n"]

        # Top bounced domains
        cur.execute("""
            SELECT SPLIT_PART(contact_email, '@', 2) AS domain, COUNT(*) AS n
            FROM leads WHERE status='bounced'
            GROUP BY 1 ORDER BY 2 DESC LIMIT 8
        """)
        data["top_bounced_domains"] = [
            {"domain": r["domain"], "n": r["n"]} for r in cur.fetchall()
        ]

        # Top sources
        cur.execute("""
            SELECT COALESCE(source, '(none)') AS src, COUNT(*) AS n
            FROM leads GROUP BY 1 ORDER BY 2 DESC LIMIT 8
        """)
        data["top_sources"] = [
            {"source": r["src"], "n": r["n"]} for r in cur.fetchall()
        ]

        # Top companies
        cur.execute("""
            SELECT company, COUNT(*) AS n FROM leads
            GROUP BY 1 HAVING COUNT(*) > 1 ORDER BY 2 DESC LIMIT 8
        """)
        data["top_companies"] = [
            {"company": r["company"], "n": r["n"]} for r in cur.fetchall()
        ]

        # Recent sends
        cur.execute("""
            SELECT id, company, contact_email, sent_at FROM leads
            WHERE sent_at IS NOT NULL ORDER BY sent_at DESC LIMIT 8
        """)
        data["recent_sends"] = [
            {
                "id": r["id"],
                "company": r["company"],
                "email": r["contact_email"],
                "sent_at": r["sent_at"].isoformat() if r["sent_at"] else None,
            }
            for r in cur.fetchall()
        ]

        # Recent bounces
        cur.execute("""
            SELECT id, company, contact_email FROM leads
            WHERE status='bounced' ORDER BY id DESC LIMIT 8
        """)
        data["recent_bounces"] = [
            {
                "id": r["id"],
                "company": r["company"],
                "email": r["contact_email"],
            }
            for r in cur.fetchall()
        ]

    # Auto-loop
    pid_file = "/tmp/auto_loop.pid"
    log_file = "/tmp/auto_loop.log"
    data["auto_loop"] = {
        "running": False,
        "pid": None,
        "uptime": None,
        "command": None,
        "log_path": log_file,
    }
    if os.path.exists(pid_file):
        pid = open(pid_file).read().strip()
        try:
            out = subprocess.check_output(
                ["ps", "-p", pid, "-o", "etime,command"],
                text=True, stderr=subprocess.DEVNULL,
            )
            lines = out.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split(None, 1)
                data["auto_loop"]["running"] = True
                data["auto_loop"]["pid"] = pid
                data["auto_loop"]["uptime"] = parts[0]
                data["auto_loop"]["command"] = parts[1] if len(parts) > 1 else ""
        except Exception:
            pass

    # Last log lines
    try:
        with open(log_file) as f:
            data["log_tail"] = [l.rstrip() for l in f.readlines()[-6:]]
    except Exception:
        data["log_tail"] = []

    # Git state
    try:
        out = subprocess.check_output(
            ["git", "log", "--oneline", "-5"],
            text=True, cwd=str(HERE),
        )
        data["git"] = {
            "recent_commits": out.strip().split("\n"),
            "branch": subprocess.check_output(
                ["git", "branch", "--show-current"], text=True, cwd=str(HERE)
            ).strip(),
        }
    except Exception as e:
        data["git"] = {"error": str(e)}

    # Derived rates
    data["bounce_rate_pct"] = (
        data["bounced"] / data["sent_email"] * 100 if data["sent_email"] else 0
    )
    data["open_rate_pct"] = (
        data["opened_url"] / data["sent_email"] * 100 if data["sent_email"] else 0
    )
    data["email_coverage_pct"] = (
        data["pending_with_email"] / data["pending_total"] * 100
        if data["pending_total"] else 0
    )

    if args.json:
        print(json.dumps(data, indent=2, default=str))
        return

    # ---- Pretty print ----
    W = 78
    print("=" * W)
    print(f"  AVILX LEADS DASHBOARD  -  {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("=" * W)

    print("\n  FUNNEL")
    print(f"    total: {data['total']}")
    for status, n in data["funnel"].items():
        pct = (n / data["total"] * 100) if data["total"] else 0
        print(f"    {status:12s} {n:4d}  ({pct:5.1f}%)  {bar(int(pct / 4))}")

    print("\n  KEY METRICS")
    print(f"    pending w/ email:       {data['pending_with_email']:4d} / "
          f"{data['pending_total']:4d}  ({data['email_coverage_pct']:.0f}% email coverage)")
    print(f"    pending fully enriched: {data['pending_fully_enriched']:4d}  "
          "(resume + cover letter)")
    print(f"    bounce rate:            {data['bounce_rate_pct']:5.1f}%  "
          f"({data['bounced']}/{data['sent_email']})")
    print(f"    open rate:              {data['open_rate_pct']:5.1f}%  "
          f"({data['opened_url']}/{data['sent_email']})")
    print(f"    sends last 24h:         {data['sends_24h']:4d}")
    print(f"    sends last 7d:          {data['sends_7d']:4d}")

    if data["top_bounced_domains"]:
        print("\n  TOP BOUNCED DOMAINS")
        for r in data["top_bounced_domains"]:
            print(f"    {r['domain']:30s} {r['n']:3d}  {bar(r['n'])}")

    print("\n  TOP LEAD SOURCES")
    for r in data["top_sources"]:
        print(f"    {r['source'][:30]:30s} {r['n']:3d}  {bar(r['n'] // 3)}")

    if data["top_companies"]:
        print("\n  TOP COMPANIES (multi-role)")
        for r in data["top_companies"]:
            print(f"    {(r['company'] or '')[:30]:30s} {r['n']:3d}")

    if data["recent_sends"]:
        print("\n  RECENTLY SENT (last 8)")
        for r in data["recent_sends"]:
            d = r["sent_at"][5:16].replace("T", " ") if r["sent_at"] else "-"
            print(f"    #{r['id']:3d} {d}  {(r['company'] or '')[:25]:25s}  {r['email']}")

    if data["recent_bounces"]:
        print("\n  RECENTLY BOUNCED (last 8)")
        for r in data["recent_bounces"]:
            print(f"    #{r['id']:3d} {(r['company'] or '')[:30]:30s}  {r['email']}")

    print("\n" + "=" * W)

    # Auto-loop
    al = data["auto_loop"]
    print("\n  AUTO-LOOP")
    if al["running"]:
        print(f"    pid:           {al['pid']}")
        print(f"    uptime:        {al['uptime']}")
        print(f"    command:       {al['command']}")
        print(f"    log:           {al['log_path']}")
    else:
        print("    NOT RUNNING  (start with: ./auto_loop.sh 200)")

    if data["log_tail"]:
        print("\n  LAST 6 LOG LINES")
        for line in data["log_tail"]:
            print(f"    {line}")

    # Git
    if "recent_commits" in data.get("git", {}):
        print("\n  GIT STATE")
        for c in data["git"]["recent_commits"]:
            print(f"    {c}")
        print(f"    branch:        {data['git']['branch']}")

    print("\n" + "=" * W)


if __name__ == "__main__":
    main()
