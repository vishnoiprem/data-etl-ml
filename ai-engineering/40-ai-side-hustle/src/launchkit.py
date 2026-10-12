"""
launchkit.py — Generate a complete Gumroad launch kit for one product.

For each product in output/products/<slug>/, this creates:
  - deliverable.pdf   : the actual downloadable (eBook or printable)
  - sales-page.html   : a copy-paste-ready sales page
  - tweet-thread.txt  : 8-tweet launch thread
  - reddit-post.txt   : a value-first Reddit post (not a sales pitch)
  - email-outreach.txt: cold email to 5 targeted list builders
  - launch-checklist.md: the exact steps to publish + first 5 sales

Why a kit and not just a product file?  Because the failure mode for
99% of digital products isn't "bad content" — it's "no traffic." A
launch kit forces you to think about promotion upfront.

Usage:
  python -m launchkit output/products/the-soc2-for-solo-founders-playbook
  python -m launchkit --all  # build kits for every product
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fpdf import FPDF


# Map common unicode punctuation to ASCII so the built-in Helvetica
# font (latin-1 only) doesn't choke. Anything not in this map gets
# replaced with '?' in the latin-1 round-trip.
_UNICODE_TO_ASCII = str.maketrans({
    "\u2014": "--",   # em-dash
    "\u2013": "-",    # en-dash
    "\u2018": "'",    # left single quote
    "\u2019": "'",    # right single quote
    "\u201c": '"',    # left double quote
    "\u201d": '"',    # right double quote
    "\u2026": "...",  # ellipsis
    "\u00a0": " ",    # non-breaking space
    "\u00b7": "*",    # middle dot
    "\u2022": "*",    # bullet
    "\u2192": "->",   # right arrow
})


def _to_pdf_safe(text: str) -> str:
    """Convert unicode to ASCII for the built-in PDF font.

    The stub eBooks use mostly ASCII but the chat/email templates
    use em-dashes and curly quotes. Rather than require a TTF font
    (which needs to be bundled), normalize the text.
    """
    return text.translate(_UNICODE_TO_ASCII)


# ---------------------------------------------------------------- PDF

class _ProductPDF(FPDF):
    """Minimal markdown-aware PDF renderer."""

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, _to_pdf_safe(self.title), new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, _to_pdf_safe(f"Page {self.page_no()}"), align="C")

    def chapter_title(self, label: str) -> None:
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 10, _to_pdf_safe(label), new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def section_title(self, label: str) -> None:
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 8, _to_pdf_safe(label), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text: str) -> None:
        self.set_font("Helvetica", "", 11)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 6, _to_pdf_safe(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def list_item(self, text: str) -> None:
        self.set_font("Helvetica", "", 11)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 6, _to_pdf_safe("  -  " + text), new_x="LMARGIN", new_y="NEXT")


def _md_to_pdf(md_text: str, title: str, out_path: Path) -> Path:
    """Render a markdown string to a basic PDF.

    Handles: H1, H2, paragraphs, and "- " bulleted lists. Anything more
    complex should be edited in a real editor before upload.
    """
    pdf = _ProductPDF()
    pdf.set_title(title)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    for raw in md_text.splitlines():
        line = raw.rstrip()
        if not line:
            pdf.ln(2)
            continue
        if line.startswith("# "):
            pdf.chapter_title(line[2:].strip())
        elif line.startswith("## "):
            pdf.section_title(line[3:].strip())
        elif line.lstrip().startswith("- "):
            pdf.list_item(line.lstrip()[2:].strip())
        elif line.lstrip().startswith(tuple(f"{i}. " for i in range(1, 10))):
            # numbered list
            pdf.list_item(line.lstrip())
        else:
            pdf.body_text(line)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    return out_path


def build_pdf(product_dir: Path) -> Path | None:
    """Pick the right markdown file in `product_dir` and render it as PDF.

    Order of preference: ebook.md → printable.md → template.md.
    """
    for name in ("ebook.md", "printable.md", "template.md"):
        md = product_dir / name
        if md.exists():
            title = product_dir.name.replace("-", " ").title()
            pdf_path = product_dir / "deliverable.pdf"
            _md_to_pdf(md.read_text(), title, pdf_path)
            return pdf_path
    return None


# ---------------------------------------------------------------- Sales page

SALES_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ font: 17px/1.6 -apple-system, system-ui, sans-serif;
         max-width: 720px; margin: 40px auto; padding: 0 20px; color: #222; }}
  h1 {{ font-size: 36px; line-height: 1.2; margin-bottom: 8px; }}
  .tagline {{ font-size: 19px; color: #555; margin-bottom: 32px; }}
  .price {{ background: #f4f4f4; padding: 24px; border-radius: 8px;
           text-align: center; margin: 32px 0; }}
  .price b {{ font-size: 48px; color: #111; }}
  .cta {{ display: inline-block; background: #23a55a; color: white;
         padding: 16px 32px; border-radius: 6px; text-decoration: none;
         font-weight: 600; font-size: 18px; }}
  ul, ol {{ padding-left: 24px; }}
  li {{ margin: 8px 0; }}
  blockquote {{ border-left: 4px solid #23a55a; padding: 8px 16px;
               background: #f9f9f9; color: #444; }}
  .testimonial {{ background: #fafafa; padding: 16px; border-radius: 6px;
                 margin: 16px 0; font-style: italic; }}
</style>
</head>
<body>

<h1>{title}</h1>
<p class="tagline">{tagline}</p>

<div class="price">
  <b>${price}</b><br>
  <a class="cta" href="#buy">Buy now &rarr;</a>
  <p style="color:#666; font-size:13px; margin-top:8px;">
    Instant download. Lifetime updates. No subscription.
  </p>
</div>

{body}

<h2>What you get</h2>
<ul>
  <li>The {format} itself ({page_count} pages / components)</li>
  <li>A 1-page quick-start guide</li>
  <li>Lifetime updates (free)</li>
  <li>30-day money-back guarantee, no questions asked</li>
</ul>

<h2>Who this is for</h2>
<p>{audience}</p>

<h2>FAQ</h2>
<p><b>How do I get it?</b><br>
After purchase, you'll get an instant download link from Gumroad. The
file is yours forever.</p>

<p><b>What if I don't like it?</b><br>
Email me within 30 days for a full refund. No forms, no friction.</p>

<p><b>Is this a subscription?</b><br>
No. One-time purchase, lifetime access.</p>

<div class="price">
  <a class="cta" href="#buy">Buy for ${price} &rarr;</a>
</div>

</body>
</html>
"""


def build_sales_page(product_dir: Path) -> Path:
    """Render sales-page.html from listing.md + the product metadata."""
    listing = product_dir / "listing.md"
    if not listing.exists():
        # Fallback: synthesize from directory name
        body_md = f"## About this product\n\nA {product_dir.name.replace('-', ' ')} for ambitious builders."
    else:
        body_md = listing.read_text()

    # Extract title from the first # heading
    title_match = re.search(r"^# (.+)$", body_md, re.M)
    title = title_match.group(1) if title_match else product_dir.name.replace("-", " ").title()

    # Extract price from "$XX" pattern
    price_match = re.search(r"\*\*\$(\d+)\*\*", body_md)
    price = price_match.group(1) if price_match else "19"

    # Strip the title/price lines (we render them ourselves)
    cleaned = re.sub(r"^# .+$", "", body_md, count=1, flags=re.M)
    cleaned = re.sub(r"\*\*\$\d+\*\*", "", cleaned, count=1)

    # Detect format and page count from listing
    fmt_match = re.search(r"page_count[^0-9]*(\d+)", listing.read_text() if listing.exists() else "")
    page_count = fmt_match.group(1) if fmt_match else "20"
    fmt = "ebook" if (product_dir / "ebook.md").exists() else \
          "printable" if (product_dir / "printable.md").exists() else "template"

    html = SALES_PAGE_TEMPLATE.format(
        title=title,
        tagline=_derive_tagline(cleaned),
        price=price,
        format=fmt,
        page_count=page_count,
        audience=_derive_audience(cleaned),
        body=cleaned.strip(),
    )
    out = product_dir / "sales-page.html"
    out.write_text(html)
    return out


def _derive_tagline(body: str) -> str:
    """Pull the first non-empty paragraph as a tagline."""
    for para in body.split("\n\n"):
        para = para.strip().lstrip("#").strip()
        if para and len(para) < 200:
            return para
    return "A practical, no-fluff guide for builders."


def _derive_audience(body: str) -> str:
    """Pull the 'Who this is for' section, or synthesize one."""
    m = re.search(r"## Who this is for\s*\n+(.+?)(?:\n\n|\Z)", body, re.S)
    if m:
        return m.group(1).strip()
    return ("Anyone who's been meaning to get started but keeps putting it off. "
            "If you have 30 minutes a day, you can finish this in a week.")


# ---------------------------------------------------------------- Tweet thread

def build_tweet_thread(product_dir: Path) -> Path:
    title = product_dir.name.replace("-", " ").title()
    thread = f"""\
1/ I wrote a {title} for the people who keep saying "I'll get to it next month."

It's 20 pages. Takes 30 minutes to read. Then 3 things to do this week.

→ https://your-gumroad-link

2/ Why I made it:

Every founder I know has the same 3 problems: not enough time, not enough clarity, not enough momentum.

This fixes the third one. You finish it and you have 3 specific actions.

3/ What's inside:

→ The Setup: minimum viable version (chapter 1)
→ The Work: 3 compounding habits (chapter 2)
→ The Payoff: 90-day plan (chapter 3)
→ Resources: books, tools, templates (appendix)

4/ Who it's for:

→ Solo founders who are tired of "someday"
→ Small teams that need one page of clarity
→ Anyone who bought 3 other products and didn't finish them

5/ What people are saying:

"I read it in one sitting and shipped my first version the next day." — early reader

"Bought 12 products like this. This is the first one I actually finished." — early reader

6/ The catch:

It's $19, not free. I'm not giving it away because free = unsubscribed in 5 minutes.

If $19 is the difference between "I shipped" and "I keep planning," it's the best money you'll spend this month.

7/ How to get it:

1. Click the link
2. Pay $19 (Gumroad, no account needed)
3. Download instantly
4. Read tonight
5. Ship tomorrow

→ https://your-gumroad-link

8/ If this isn't for you:

Email me within 30 days for a refund. No forms, no questions.

If it IS for you — what are you waiting for?

— Prem
"""
    out = product_dir / "tweet-thread.txt"
    out.write_text(thread)
    return out


# ---------------------------------------------------------------- Reddit post

def build_reddit_post(product_dir: Path) -> Path:
    title = product_dir.name.replace("-", " ").title()
    post = f"""\
Title: I wrote a 20-page {title} for solo founders — free excerpt inside

Body:

Hey r/[niche],

I posted a few weeks ago about [problem] and got a lot of DMs asking
for a writeup. I turned the answers into a 20-page guide.

The full thing is $19 on Gumroad, but here's the entire Chapter 1
free below. If it's useful, the link is at the bottom. If not, no
hard feelings.

---

## Chapter 1 — The Setup

Most people overthink the start. Here's the minimum viable version.

[... 600 words of value ...]

## Chapter 2 — The Work

Three habits that compound...

[the rest is in the paid version, but here's the gist: ...]

---

**Who this is for:** solo founders, indie hackers, small teams.

**Who this is NOT for:** if you want a 400-page textbook, look elsewhere.
This is a 20-page kick in the pants.

**Why I charge:** I gave the first version away for free. 90% of
people who downloaded it never opened it. Charging $19 filters for
people who are actually going to read it. (This is a known trick.)

Full version ($19, instant download, 30-day refund):
→ https://your-gumroad-link

— Prem
"""
    out = product_dir / "reddit-post.txt"
    out.write_text(post)
    return out


# ---------------------------------------------------------------- Email outreach

def build_email_outreach(product_dir: Path) -> Path:
    title = product_dir.name.replace("-", " ").title()
    emails = f"""\
SUBJECT: Quick guest post idea for {title} readers

Hey [first name],

I've been reading your newsletter for the past 6 months — the
[recent post on X] was particularly good.

I just shipped a 20-page {title} for solo founders. I think your
audience would get a lot out of Chapter 2 ([specific takeaway]).

Two options:

1. **Guest post:** I write a 600-word piece based on Chapter 2
   for [newsletter name]. You publish it; I include a CTA for
   the full guide at the end. I keep 100% of guide revenue.

2. **Affiliate:** I give you 30% on every sale through your link
   for the next 90 days. I write the email; you forward it.

Either way, no obligation. If neither sounds good, just say so
and I'll stop following up.

— Prem
premsemail@email.com

---

SUBJECT: Cross-promo idea ({title} ↔ your audience)

Hey [first name],

Quick one: I just launched {title} (20 pages, $19) and I'm
looking for 3 newsletter partners to cross-promote with.

You promote to your list, I promote to mine. We split any sales
50/50.

My list is [X] founders/indie hackers. Yours is [Y] [niche].
Overlap should be ~30%.

If interested, I can send over the swipe copy (it's already
written — just plug in your affiliate link).

— Prem
"""
    out = product_dir / "email-outreach.txt"
    out.write_text(emails)
    return out


# ---------------------------------------------------------------- Launch checklist

LAUNCH_CHECKLIST = """# Launch Checklist for {title}

## Today (Day 0)
- [ ] Upload `deliverable.pdf` to Gumroad
- [ ] Copy `sales-page.html` into the Gumroad description (or paste
      the markdown from `listing.md` if you don't want HTML)
- [ ] Set price to ${price}
- [ ] Add a cover image (use Canva, 1280x720, with the title big)
- [ ] Set the product URL slug to something memorable
- [ ] Test the purchase flow with a $0 test product first

## Day 1 — Launch
- [ ] Post the tweet thread (paste from `tweet-thread.txt`, fill in your link)
- [ ] Post the Reddit post in 2-3 relevant subreddits (use `reddit-post.txt`)
- [ ] Email 5 newsletter operators using `email-outreach.txt`
- [ ] Send a "I shipped this" DM to 10 people you know who'd care
- [ ] Pin the launch tweet

## Day 2-7 — Sustain
- [ ] Reply to every comment/DM about the product
- [ ] Post 1 follow-up per day (a tip from the book, a behind-the-scenes,
      a customer reply)
- [ ] Ship 1 small free update to the product (e.g., a new checklist)
- [ ] Re-share on LinkedIn with a 2-sentence hook + link

## Day 8+ — Compound
- [ ] Look at Gumroad analytics: where did buyers come from?
- [ ] Double down on the 1-2 channels that converted
- [ ] Build product #2 using the same template

## Targets
- Day 1-3: 1-3 sales
- Day 4-7: 5-10 sales
- Day 30: 20-50 sales (=> $380-$950 if priced at $19)
"""


def build_checklist(product_dir: Path) -> Path:
    title = product_dir.name.replace("-", " ").title()
    listing = product_dir / "listing.md"
    price_match = re.search(r"\*\*\$(\d+)\*\*", listing.read_text()) if listing.exists() else None
    price = price_match.group(1) if price_match else "19"
    out = product_dir / "launch-checklist.md"
    out.write_text(LAUNCH_CHECKLIST.format(title=title, price=price))
    return out


# ---------------------------------------------------------------- Entry point

def build_kit(product_dir: Path) -> dict:
    """Build the full launch kit for one product. Returns a summary dict."""
    outputs: dict[str, str | None] = {}
    pdf = build_pdf(product_dir)
    outputs["deliverable.pdf"] = str(pdf) if pdf else None
    outputs["sales-page.html"] = str(build_sales_page(product_dir))
    outputs["tweet-thread.txt"] = str(build_tweet_thread(product_dir))
    outputs["reddit-post.txt"] = str(build_reddit_post(product_dir))
    outputs["email-outreach.txt"] = str(build_email_outreach(product_dir))
    outputs["launch-checklist.md"] = str(build_checklist(product_dir))
    return outputs


def build_all(output_root: Path) -> list[dict]:
    """Build kits for every product under output_root/products/."""
    products_dir = output_root / "products"
    if not products_dir.exists():
        return []
    results: list[dict] = []
    for sub in sorted(products_dir.iterdir()):
        if sub.is_dir():
            try:
                kit = build_kit(sub)
                results.append({"product": sub.name, "files": kit})
            except Exception as e:
                results.append({"product": sub.name, "error": str(e)})
    return results


if __name__ == "__main__":  # pragma: no cover
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        results = build_all(Path("output"))
        for r in results:
            if "error" in r:
                print(f"  ✗ {r['product']}: {r['error']}")
            else:
                print(f"  ✓ {r['product']}: {len(r['files'])} files")
    else:
        target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
        if not target:
            print("usage: python -m launchkit <product_dir>")
            print("       python -m launchkit --all")
            raise SystemExit(1)
        kit = build_kit(target)
        for name, path in kit.items():
            print(f"  ✓ {name}  →  {path}")
