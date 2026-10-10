#!/usr/bin/env python3
"""
Open Apply URLs in Browser

For leads where there's no public email (or where the apply URL is the better path),
this script opens all the URLs in your default browser, one at a time. You then
manually apply through the platform.

Usage:
  python3 open_urls.py              # open all pending URLs
  python3 open_urls.py --lead 0     # open just lead at index 0
  python3 open_urls.py --principal  # open only principal-track leads
  python3 open_urls.py --senior     # open only senior-track leads
"""

import json
import argparse
import webbrowser
import time
from pathlib import Path

LEADS_FILE = Path(__file__).parent / "leads.json"


def load_leads():
    with open(LEADS_FILE) as f:
        return json.load(f)


def is_principal(resume_file):
    return resume_file == "PREM_2026.pdf"


def open_urls(filter_track=None, specific=None):
    leads = load_leads()
    for i, lead in enumerate(leads):
        if lead["status"] != "pending":
            continue
        if specific is not None and i != specific:
            continue
        if filter_track == "principal" and not is_principal(lead["resume_file"]):
            continue
        if filter_track == "senior" and is_principal(lead["resume_file"]):
            continue

        url = lead["url"]
        print(f"#{i+1} {lead['company']:<20} {lead['role']}")
        print(f"   URL: {url}")
        print(f"   Resume: {lead['resume_file']}")
        print(f"   Opening in browser...")

        webbrowser.open_new_tab(url)
        time.sleep(2)  # Give browser time to load

    print("\n✅ All matching URLs opened in your browser.")
    print("   Apply manually on each platform, then mark leads as 'sent' in leads.json")


def main():
    parser = argparse.ArgumentParser(description="Open lead apply URLs in browser")
    parser.add_argument("--lead", type=int, help="Specific lead index (0-based)")
    parser.add_argument("--principal", action="store_true", help="Only principal-track leads")
    parser.add_argument("--senior", action="store_true", help="Only senior-track leads")
    args = parser.parse_args()

    filter_track = "principal" if args.principal else ("senior" if args.senior else None)
    open_urls(filter_track=filter_track, specific=args.lead)


if __name__ == "__main__":
    main()
