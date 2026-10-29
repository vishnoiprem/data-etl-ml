"""
tests/test_parser.py — real-world snippet fixtures for the JD parser.

Run:  python3 -m tests.test_parser
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

from process_jd_inbox import DOLLAR_RE, extract_rate, _split_into_posts, parse_block  # noqa


# Each tuple: (label, input_line, expected_match_or_none)
RATE_CASES = [
    # Real formats seen in the wild
    ("usd 120-180/hr",        "Senior AI Engineer | Acme | Remote | $120-180/hr",     "$120-180/hr"),
    ("usd 120k-180k",         "ML Engineer — Fintech — NYC — $120k-$180k",            "$120k-$180k"),
    ("usd 150k",              "Senior Eng, $150K + equity, Remote",                   "$150K"),
    ("usd 80/hr",             "Contract: $80/hr, 6 months",                            "$80/hr"),
    ("usd 5,000",             "S$5,000 / month, part-time",                            "S$5,000 / month"),
    ("sgd 8k-12k",            "SGD 8K - 12K / month",                                  "SGD 8K - 12K / month"),
    ("eur 70-100",            "€70-100k",                                              "€70-100k"),
    ("usd 200k",              "Up to $200K base + bonus",                              "$200K"),
    ("usd 120-180k",          "Salary: $120-180k, Bay Area",                           "$120-180k"),
    ("usd 90-110",            "TC $90-110k + equity",                                  "$90-110k"),
    # Should NOT match — these are funding/valuation lines, not comp
    ("funding round",         "Raised $50M Series B from Sequoia",                     None),
    ("valuation",             "Post-money valuation: $1.2B",                           None),
    ("stock only",            "0.5% equity, no salary",                                None),
    # Edge cases
    ("no rate",               "Hiring: Senior Engineer\nAcme Corp\nRemote",           None),
    ("rate with parens",      "($130-160K) + bonus",                                   "$130-160K"),
]


def test_rate_extraction():
    print("🧪 test_rate_extraction")
    fails = 0
    for label, line, want in RATE_CASES:
        got = extract_rate(line)
        # Normalize whitespace for compare
        got_norm = re.sub(r"\s+", " ", got).strip() if got else None
        want_norm = re.sub(r"\s+", " ", want).strip() if want else None
        ok = got_norm == want_norm
        marker = "✅" if ok else "❌"
        if not ok:
            fails += 1
        print(f"  {marker} {label:18s} got={got_norm!r:25s} want={want_norm!r}")
    print(f"  → {len(RATE_CASES) - fails}/{len(RATE_CASES)} pass")
    return fails == 0


POST_CASES = [
    # Single post, clean
    ("single clean", """\
Hiring: Senior AI Engineer
Acme Corp
Remote
$120-180/hr
jobs@acme.com
""", 1),
    # Two posts separated by --- START PASTE ---
    ("two posts separated", """\
--- START PASTE 1 ---
Hiring: ML Engineer
ByteDance
Mountain View, CA
$200-300k
jobs@bytedance.com
--- END PASTE 1 ---

--- START PASTE 2 ---
Looking for a Founding Engineer
Genesis Therapeutics
South San Francisco
ML / Drug discovery
ben@genesis.ai
--- END PASTE 2 ---
""", 2),
    # Emoji header
    ("emoji header", """\
🚀 We're hiring a Founding Engineer
Flow Commerce
Remote, US
jhano@flow.io
""", 1),
    # No email
    ("no email", """\
Hiring: Senior AI Engineer
Acme Corp
Remote
""", 1),
]


def test_block_split():
    print("\n🧪 test_block_split")
    fails = 0
    for label, raw, expected_n in POST_CASES:
        blocks = _split_into_posts(raw)
        got_n = len(blocks)
        ok = got_n == expected_n
        marker = "✅" if ok else "❌"
        if not ok:
            fails += 1
        print(f"  {marker} {label:25s} got={got_n} blocks, want={expected_n}")
        for i, b in enumerate(blocks):
            preview = b.replace("\n", " | ")[:80]
            print(f"      [{i}] {preview}")
    return fails == 0


def main():
    r1 = test_rate_extraction()
    r2 = test_block_split()
    print(f"\n{'✅ ALL PASS' if (r1 and r2) else '❌ SOME FAILED'}")
    sys.exit(0 if (r1 and r2) else 1)


if __name__ == "__main__":
    main()
