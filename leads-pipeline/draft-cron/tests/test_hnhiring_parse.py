"""
tests/test_hnhiring_parse.py — unit tests for the hnhiring.com
pipe-separated headline parser used by `scrape_hnhiring_remote`.

Run:  python3 -m tests.test_hnhiring_parse

The parser is extracted to a standalone helper
(`find_more_leads._parse_pipe_headline`) so the parsing logic can
be tested without spinning up an HTTP request. Real hnhiring.com
postings come in several flavours:

  1. "Chronograph (chronograph.pe) | Senior Engineer | FT | Remote | $120k-180k"
  2. "Location: Remote | Stack: Python, AWS | SomeCo | Senior Engineer | FT"
  3. "SomeCo | Lead ML Engineer | Remote | Apply at foo.com"
  4. "Single-line no pipes" (legacy)
  5. "Location: Remote | Stack: AWS" (only noise segments — delegates
     to the legacy `split_company_role` and is filtered out by the
     caller's bad-words list)

Each test case below maps to one of these flavours.
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

from find_more_leads import _parse_pipe_headline  # noqa


# (label, input, expected_company, expected_role)
PIPE_CASES = [
    (
        "domain-paren co + role",
        "Chronograph (chronograph.pe) | Senior Engineer | FT | Remote | $120k-180k",
        "Chronograph",
        "Senior Engineer",
    ),
    (
        "leading noise segments skipped",
        "Location: Remote | Stack: Python, AWS | SomeCo | Senior Engineer | FT",
        "SomeCo",
        "Senior Engineer",
    ),
    (
        "no domain parens",
        "SomeCo | Lead ML Engineer | Remote | Apply at foo.com",
        "SomeCo",
        "Lead ML Engineer",
    ),
    (
        "plain pipe two segments",
        "Acme Corp (acme.com) | Backend Engineer",
        "Acme Corp",
        "Backend Engineer",
    ),
    (
        "no pipe at all",
        "SingleLine NoPipes",
        "Unknown",
        "SingleLine NoPipes",
    ),
    (
        "only noise segments — delegates to split_company_role",
        # The caller (scrape_hnhiring_remote) filters out "Location"
        # from its bad-words list, so this delegation is fine in
        # practice. The test pins the current behaviour.
        "Location: Remote | Stack: AWS",
        "Location",
        "Remote | Stack: AWS",
    ),
    (
        "FT noise before role",
        "Acme | Senior Engineer | FT",
        "Acme",
        "Senior Engineer",
    ),
    (
        "Apply: noise after role",
        "Acme | Senior Engineer | Apply: foo@bar.com",
        "Acme",
        "Senior Engineer",
    ),
]


def test_pipe_parsing():
    print("🧪 test_pipe_parsing")
    fails = 0
    for label, head, want_co, want_role in PIPE_CASES:
        got_co, got_role = _parse_pipe_headline(head)
        ok = got_co == want_co and got_role == want_role
        marker = "✅" if ok else "❌"
        if not ok:
            fails += 1
        print(f"  {marker} {label:50s} got=({got_co!r}, {got_role!r})")
        if not ok:
            print(f"      want=({want_co!r}, {want_role!r})")
    return fails == 0


def main():
    r = test_pipe_parsing()
    print(f"\n{'✅ ALL PASS' if r else '❌ SOME FAILED'}")
    sys.exit(0 if r else 1)


if __name__ == "__main__":
    main()
