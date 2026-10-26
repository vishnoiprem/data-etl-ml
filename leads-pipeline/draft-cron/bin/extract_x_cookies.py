#!/usr/bin/env python3
"""
bin/extract_x_cookies.py — interactive helper to capture X.com auth cookies.

How it works:
  1. Opens a real Chromium window via Playwright (headed, not headless)
  2. Navigates to x.com/login
  3. Waits for you to log in (any 2FA / captcha / etc.)
  4. Once you're logged in, exports auth_token + ct0 cookies to
     state/x_cookies.json

This avoids having to manually fish the cookies out of DevTools.

Run:  /Users/vishnoiprem/PycharmProjects/data-etl-ml/.venv/bin/python bin/extract_x_cookies.py
"""

import json
import os
import sys
import time
from pathlib import Path

DRAFTS = Path(__file__).resolve().parent.parent
STATE = DRAFTS / "state"
OUT = STATE / "x_cookies.json"
EXAMPLE = STATE / "x_cookies.example.json"


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed. Run:")
        print("  pip install playwright && playwright install chromium")
        return 1
    if not OUT.exists():
        # Start from the example template
        if EXAMPLE.exists():
            with open(EXAMPLE) as f:
                template = f.read()
        else:
            template = "[]"
        OUT.write_text(template)
        # Restrict permissions — the file will soon contain session tokens.
        # 0o600 = owner read/write only. (No-op on Windows but harmless.)
        try:
            os.chmod(OUT, 0o600)
        except OSError:
            pass
        print(f"created {OUT} from template (chmod 0o600)")
    print("Opening Chromium (headed) — log into x.com in the new window.")
    print("When you see your timeline, come back here and press Enter.")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto("https://x.com/login", wait_until="domcontentloaded")
        input("Press Enter after you have successfully logged in...")
        # Confirm we're logged in
        page.goto("https://x.com/home", wait_until="domcontentloaded",
                  timeout=30000)
        time.sleep(2)
        url = page.url
        if "/login" in url or "/i/flow" in url:
            print(f"still on login page ({url}). Aborting.")
            browser.close()
            return 1
        # Extract cookies
        cookies = ctx.cookies("https://x.com")
        auth = next((c for c in cookies if c["name"] == "auth_token"), None)
        ct0 = next((c for c in cookies if c["name"] == "ct0"), None)
        if not auth or not ct0:
            print(f"missing required cookies: auth={'yes' if auth else 'no'}, "
                  f"ct0={'yes' if ct0 else 'no'}")
            print("found:", [c["name"] for c in cookies])
            browser.close()
            return 1
        # Save as Playwright-format JSON (compatible with our loader)
        out_cookies = [
            {
                "name": "auth_token",
                "value": auth["value"],
                "domain": ".x.com",
                "path": "/",
                "expires": auth.get("expires", -1),
                "httpOnly": auth.get("httpOnly", True),
                "secure": auth.get("secure", True),
                "sameSite": auth.get("sameSite", "None"),
            },
            {
                "name": "ct0",
                "value": ct0["value"],
                "domain": ".x.com",
                "path": "/",
                "expires": ct0.get("expires", -1),
                "httpOnly": ct0.get("httpOnly", False),
                "secure": ct0.get("secure", True),
                "sameSite": ct0.get("sameSite", "Lax"),
            },
        ]
        OUT.write_text(json.dumps(out_cookies, indent=2))
        # auth_token is a long-lived X.com session token. Owner-only.
        try:
            os.chmod(OUT, 0o600)
        except OSError:
            pass
        print(f"wrote {OUT} (chmod 0o600)")
        print(f"  auth_token: {auth['value'][:20]}... (length {len(auth['value'])})")
        print(f"  ct0: {ct0['value'][:20]}... (length {len(ct0['value'])})")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
