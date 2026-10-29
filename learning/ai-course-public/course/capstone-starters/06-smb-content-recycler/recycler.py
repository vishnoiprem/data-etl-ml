"""Content recycler — turn 1 long-form markdown file into 30 social posts.

Run:
    export OPENAI_API_KEY=sk-...
    python recycler.py newsletter.md "Mei's Bakery" posts.csv

This is the optional Tier 2 of the SMB Content Recycler capstone
(capstone-starters/06-smb-content-recycler). The Tier 1 version is the
no-code copy-paste prompt in the README; this script is for SMB owners
who want to automate the API call.

Cost: $0.01-0.05 per long-form (gpt-4o-mini).
Time: 60-90 seconds end-to-end.
"""
from __future__ import annotations
import argparse
import csv
import os
import sys
from typing import List, Tuple

try:
    import openai
except ImportError:
    print("openai not installed. run: pip install openai", file=sys.stderr)
    sys.exit(1)


MASTER_PROMPT = """\
You are a social media manager for {business}. Your job is to turn 1
long-form piece (article, blog post, transcript, podcast notes, customer
case study) into 30 social posts: 10 LinkedIn, 10 Facebook, 10 Instagram.
Each post has a hook (first line), a body (2-4 sentences), and a CTA
(last line). Each post stands alone — no "continued in comments".

Output: 30 posts, numbered 1-30, each labeled [LinkedIn] / [Facebook] /
[Instagram]. For each post, give the hook on its own line, then the
body, then the CTA.

The long-form piece:
---
{long_form}
---"""


def parse_posts(raw: str) -> List[Tuple[str, int, str]]:
    """Parse the AI's 30-post output into (platform, n, text) tuples.

    Accepts lines like:
        1. [LinkedIn] hook...
           body
           CTA
        2. [Facebook] ...

    The "n" is the post number; the "text" is everything after the
    platform tag (including the body and CTA on subsequent lines).
    """
    posts: List[Tuple[str, int, str]] = []
    current: List[str] = []
    current_platform = None
    current_n = None

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Header line: "1. [LinkedIn] ..." or "1) [Facebook] ..."
        if current_platform is None and "[" in stripped and "]" in stripped:
            try:
                n_part, rest = stripped.split(".", 1)
                current_n = int(n_part.strip())
                current_platform = rest.strip().split("]")[0].strip("[")
                first_text = rest.split("]", 1)[1].strip()
                current = [first_text]
            except (ValueError, IndexError):
                # Couldn't parse — skip this line
                continue
        elif current_platform is not None:
            # Continuation of the current post
            if stripped.startswith(tuple(f"{i}." for i in range(1, 31))):
                # New post starting; flush current first
                posts.append((current_platform, current_n, "\n".join(current).strip()))
                try:
                    n_part, rest = stripped.split(".", 1)
                    current_n = int(n_part.strip())
                    current_platform = rest.strip().split("]")[0].strip("[")
                    first_text = rest.split("]", 1)[1].strip()
                    current = [first_text]
                except (ValueError, IndexError):
                    current_platform = None
                    current = []
            else:
                current.append(stripped)

    # Flush the last post
    if current_platform is not None and current:
        posts.append((current_platform, current_n, "\n".join(current).strip()))

    return posts


def recycle(long_form_path: str, business: str, output_csv: str) -> int:
    """Run the master prompt on the long-form file and write posts to CSV.

    Returns the number of posts written. Exits with a clear error if
    the OPENAI_API_KEY is missing or the file is empty.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. export OPENAI_API_KEY=sk-...", file=sys.stderr)
        sys.exit(1)
    with open(long_form_path) as f:
        long_form = f.read().strip()
    if not long_form:
        print(f"{long_form_path} is empty", file=sys.stderr)
        sys.exit(1)
    prompt = MASTER_PROMPT.format(business=business, long_form=long_form)
    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.choices[0].message.content or ""
    posts = parse_posts(raw)
    if not posts:
        print("could not parse any posts from the AI response", file=sys.stderr)
        print("---raw response---", file=sys.stderr)
        print(raw[:2000], file=sys.stderr)
        sys.exit(1)
    with open(output_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["platform", "n", "text"])
        for platform, n, text in posts:
            w.writerow([platform, n, text])
    print(f"wrote {len(posts)} posts to {output_csv}")
    return len(posts)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Turn 1 long-form markdown file into 30 social posts (CSV)."
    )
    p.add_argument("long_form", help="path to the long-form markdown file")
    p.add_argument("business", help="your business name (used in the prompt)")
    p.add_argument("output_csv", help="path to write the 30-post CSV")
    args = p.parse_args()
    recycle(args.long_form, args.business, args.output_csv)


if __name__ == "__main__":
    main()
