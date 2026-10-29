"""publish_checklist.py — print a copy-paste-ready table for Gumroad upload.

I can't open a browser or log in for you, but I can dump every field
you'll need into one place so the actual upload takes ~5 min.

Usage:
  python3 scripts/publish_checklist.py
  make publish-checklist

Output:
  - prints a per-product table to stdout
  - writes output/publish.md with the same data + full descriptions,
    so you can copy-paste straight from one file.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / "output" / "products"
URL_MAP = ROOT / "output" / "url-map.json"
OUT = ROOT / "output" / "publish.md"


def _load_url_map() -> dict[str, str]:
    if not URL_MAP.exists():
        return {}
    return json.loads(URL_MAP.read_text())


def _read_listing(p: Path) -> dict:
    """Pull title, price, hook, audience, what-you-get from listing.md."""
    listing = p / "listing.md"
    if not listing.exists():
        return {"title": p.name, "price": "?", "hook": ""}
    text = listing.read_text()
    title_m = re.search(r"^# (.+)$", text, re.M)
    price_m = re.search(r"\*\*\$(\d+)\*\*", text)
    return {
        "title": title_m.group(1) if title_m else p.name,
        "price": price_m.group(1) if price_m else "?",
        "text": text,
    }


def _product_rows() -> list[dict]:
    if not PRODUCTS.exists():
        return []
    url_map = _load_url_map()
    rows = []
    for p in sorted(PRODUCTS.iterdir()):
        if not p.is_dir():
            continue
        info = _read_listing(p)
        info["slug"] = p.name
        info["url"] = url_map.get(p.name, "— not set —")
        info["pdf"] = p / "deliverable.pdf"
        info["pdf_exists"] = info["pdf"].exists()
        info["pdf_size_kb"] = (
            round(info["pdf"].stat().st_size / 1024, 1) if info["pdf_exists"] else 0
        )
        rows.append(info)
    return rows


def _print_terminal(rows: list[dict]) -> None:
    print("=" * 72)
    print("  PUBLISH CHECKLIST — vishnoiprem.gumroad.com")
    print("=" * 72)
    print()
    print(f"  Found {len(rows)} product(s) ready to publish.\n")
    for i, r in enumerate(rows, 1):
        print(f"--- Product {i}/{len(rows)} ---")
        print(f"  Title:        {r['title']}")
        print(f"  Price:        ${r['price']}")
        print(f"  URL slug:     {r['url']}")
        print(f"  PDF file:     {r['pdf']}  ({r['pdf_size_kb']} KB)")
        if not r["pdf_exists"]:
            print("  *** WARNING: deliverable.pdf missing — run `make launchkit-map` first")
        print(f"  Description:  {r['pdf'].parent / 'gumroad-description.md'}")
        print()
    print("=" * 72)
    print("  Step-by-step:")
    print("=" * 72)
    print("  1. Open https://vishnoiprem.gumroad.com/products/new")
    print("  2. For each product above:")
    print("     a. Copy the Title into the Name field")
    print("     b. Set the Price")
    print("     c. Set the URL slug (the part after /l/)")
    print("     d. Open the gumroad-description.md, copy all, paste as Description")
    print("     e. Upload the deliverable.pdf as the file")
    print("     f. Click Publish")
    print()
    print("  3. After publishing, run `make launchkit-map MAP=output/url-map.json`")
    print("     to refresh all marketing assets with the real /l/<slug> URLs.")
    print()
    print(f"  Full data also written to: {OUT}")


def _write_markdown(rows: list[dict]) -> None:
    """Write the same data + full descriptions to output/publish.md."""
    lines: list[str] = []
    lines.append("# Publish Checklist — vishnoiprem.gumroad.com")
    lines.append("")
    lines.append(f"_{len(rows)} product(s) ready. Open this file and copy each section into Gumroad._")
    lines.append("")
    for i, r in enumerate(rows, 1):
        lines.append("---")
        lines.append("")
        lines.append(f"## Product {i}: {r['title']}")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|---|---|")
        lines.append(f"| **Name** | `{r['title']}` |")
        lines.append(f"| **Price** | `${r['price']}` |")
        lines.append(f"| **URL slug** | `{r['url'].rsplit('/', 1)[-1] if '/' in r['url'] else r['url']}` |")
        lines.append(f"| **PDF file** | `{r['pdf']}` ({r['pdf_size_kb']} KB) |")
        lines.append("")
        if r["pdf_exists"]:
            lines.append("### Description (copy everything below this line into the Description field)")
            lines.append("")
            lines.append("```markdown")
            lines.append(r["text"].rstrip())
            lines.append("```")
        else:
            lines.append("> ⚠️ **PDF missing** — run `make launchkit-map` first.")
        lines.append("")
        lines.append("### Suggested launch sequence (Day 1)")
        lines.append("")
        lines.append(f"- Open `output/products/{r['slug']}/tweet-thread.txt` → post the 8 tweets")
        lines.append(f"- Open `output/products/{r['slug']}/reddit-post.txt` → post in 2-3 subreddits")
        lines.append(f"- Open `output/products/{r['slug']}/email-outreach.txt` → send 5 cold emails")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Day 2-7 — follow the per-product `launch-checklist.md`")
    lines.append("")
    OUT.write_text("\n".join(lines))


def main() -> int:
    rows = _product_rows()
    if not rows:
        print("  ✗ No products found. Run `make launchkit-map` first.", file=sys.stderr)
        return 1
    _print_terminal(rows)
    _write_markdown(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
