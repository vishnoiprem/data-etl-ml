"""
tests/test_hn_headline_segments.py — unit tests for the HN "Who is
Hiring" headline classifier used by `scrape_hn_who_is_hiring`.

Run:  python3 -m tests.test_hn_headline_segments

The parser reads a headline like:

    Sift Science, San Francisco, is Hiring Machine Learning Engineers
    Kaiser Permanente Medical Informatics | Machine Learning Engineers
        and Scientists (Data Science Team) | San Diego, CA | ONSITE

and splits it into a company and a role. The order of the pipe-separated
segments varies between posts, so the classifier works on what each
segment *looks like* rather than on its position.

These cases are pinned because the historical implementation took
`parts[1]` as the company. On the very common
`Company | Location | Role` shape that put the *location* in the
company column, so every generated email said something like
"Avilx for San Francisco, CA — ...".

Every headline below is a real one from the threads the pipeline
harvests, not an invented shape.
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

from autopilot import (  # noqa: E402
    _guess_company_from_hn_comment,
    _guess_role_from_hn_comment,
)


def _parse(head):
    company = _guess_company_from_hn_comment(head)
    role = _guess_role_from_hn_comment(head, company=company)
    return company, role


# (label, headline, expected_company, expected_role)
# expected_role of None means "we don't assert on the role here".
HEADLINE_CASES = [
    (
        "no pipes, X, City, is Hiring Role",
        "Sift Science, San Francisco, is Hiring Machine Learning Engineers",
        "Sift Science",
        "Machine Learning Engineers",
    ),
    (
        "Company | Location | Role | Type",
        "MANTECH | San Diego, CA | Quantum Research Scientist | Full-time",
        "MANTECH",
        "Quantum Research Scientist",
    ),
    (
        "Company | Location | Role | Type (Seattle)",
        "Planet | San Francisco, CA or Seattle, WA | Machine Learning Engineer "
        "(and other roles) | Full-time | Onsite",
        "Planet",
        "Machine Learning Engineer (and other roles)",
    ),
    (
        "company named after the role opening",
        "Antithesis | Remote | AI Engineer | Full-time",
        "Antithesis",
        "AI Engineer",
    ),
    (
        "role segment contains a comma and a capitalised word",
        "Oscar Health | Manager, Network Contracting (Southeast Region) | Remote",
        "Oscar Health",
        "Manager, Network Contracting (Southeast Region)",
    ),
    (
        "plural role wording",
        "Nines | Software Engineers | Full-Time | Palo Alto, CA",
        "Nines",
        "Software Engineers",
    ),
    (
        "company ends in a two-letter token",
        "Aiden.ai | Early Engineer - Machine Learning Engineer | London, UK | ONSITE",
        "Aiden.ai",
        "Early Engineer - Machine Learning Engineer",
    ),
    (
        "company ends in a two-letter acronym",
        "Shield AI | San Diego, CA | Full-Time | Onsite | US Citizen",
        "Shield AI",
        None,
    ),
    (
        "comma before a legal suffix is not a city",
        "tCell.io, Inc | San Francisco and Stockholm | Full-time | DevOps, "
        "Data Platform, Test, Security Engineers | ONSITE",
        "tCell.io",
        "DevOps, Data Platform, Test, Security Engineers",
    ),
    (
        "HTML link in the headline",
        'Kensho | <a href="https:&#x2F;&#x2F;www.kensho.com&#x2F;#&#x2F;'
        'careers" rel="nofollow">https:&#x2F;&#x2F;www.kensho.com&#x2F;#'
        '&#x2F;careers</a> | Primarily: Boston',
        "Kensho",
        None,
    ),
    (
        "HTML-escaped pipes instead of real pipes",
        "Solvvy&#x2F;Palo Alto, CA&#x2F;Full-time&#x2F; Onsite&#x2F; www.solvvy.com",
        "Solvvy",
        None,
    ),
    (
        "no space before the first pipe",
        "LiveKit| http://livekit.io/ | VoiceAI | webRTC | Remote | Full Time",
        "LiveKit",
        "VoiceAI",
    ),
    (
        "role listed before the company",
        "comma.ai | engineers | San Diego | onsite | full-time",
        "comma.ai",
        "engineers",
    ),
    (
        "company repeated in the headline",
        "Vungle  | San Francisco, CA  Full-Time | ONSITE | VISA",
        "Vungle",
        "Vungle",
    ),
    (
        "long multi-role segment",
        "Kaiser Permanente Medical Informatics | Machine Learning Engineers "
        "and Scientists (Data Science Team), Backend Engineers (Applications "
        "Team) | San Diego, CA | ONSITE | Full-time",
        "Kaiser Permanente Medical Informatics",
        "Machine Learning Engineers and Scientists (Data Science Team), "
        "Backend Engineers (Applications Team)",
    ),
    (
        "visa boilerplate is not a role",
        "National Robotics Engineering Center | Software, Computer Vision, "
        "Machine Learning, UI | Pittsburgh, PA, USA | ONSITE | Full Time | "
        "H1-B VISA",
        "National Robotics Engineering Center",
        None,
    ),
    (
        "location is a well-known city",
        "Connexity | Santa Monica, CA | Full-Time | Onsite",
        "Connexity",
        None,
    ),
    (
        "two-letter role abbreviation",
        "Quora | ML Engineer | Mountain View",
        "Quora",
        "ML Engineer",
    ),
    (
        "company name ends in .com",
        "Wealthport.com | Senior Computer Science &#x2F; Machine Learning "
        "Engineer, Scala Backend Engineer | Zurich | SALARY: 100k-120k CHF | ONSITE",
        "Wealthport.com",
        "Senior Computer Science / Machine Learning Engineer, Scala Backend Engineer",
    ),
    (
        "ampersand in the role",
        "Laobot | Generalist &amp; Machine Learning Engineer | Beijing &amp; "
        "San Francisco | REMOTE",
        "Laobot",
        "Generalist & Machine Learning Engineer",
    ),
    (
        "parenthesised location inside a segment",
        "Antithesis | Washington, DC, London | Remote | Full-time",
        "Antithesis",
        None,
    ),
]


def test_headline_classification():
    print("🧪 test_headline_classification")
    fails = 0
    for label, head, want_co, want_role in HEADLINE_CASES:
        got_co, got_role = _parse(head)
        ok = got_co == want_co and (want_role is None or got_role == want_role)
        if not ok:
            fails += 1
        marker = "✅" if ok else "❌"
        print(f"  {marker} {label:48s} got=({got_co!r}, {got_role!r})")
        if not ok:
            print(f"      want=({want_co!r}, {want_role!r})")
    return fails == 0


def test_role_is_not_the_company_when_a_distinct_title_exists():
    """The company must not be returned as the role when a title exists."""
    print("🧪 test_role_is_not_the_company_when_a_distinct_title_exists")
    head = ("Postie | Machine Learning Engineer, Data Scientist, Data Engineer | "
            "Southern California or REMOTE (USA)")
    company, role = _parse(head)
    ok = company == "Postie" and role != "Postie" and "Machine Learning" in role
    print(f"  {'✅' if ok else '❌'} company={company!r} role={role!r}")
    return ok


def test_company_is_never_a_location():
    """When a headline names both, the company must win over the location."""
    print("🧪 test_company_is_never_a_location")
    cases = [
        ("Flow Commerce | Hoboken, NJ and Dublin, Ireland | Senior Backend",
         "Flow Commerce"),
        ("Human API | Redwood City, CA | Full-time | Onsite", "Human API"),
        ("WebAction | Downtown Palo Alto, CA | Big Data Platform Engineer (Java)",
         "WebAction"),
        ("NREC | Pittsburgh, PA, USA | Software Engineers", "NREC"),
    ]
    fails = 0
    for head, want in cases:
        company, _role = _parse(head)
        ok = company == want
        if not ok:
            fails += 1
        print(f"  {'✅' if ok else '❌'} got={company!r} want={want!r}")
    return fails == 0


def main():
    r1 = test_headline_classification()
    r2 = test_role_is_not_the_company_when_a_distinct_title_exists()
    r3 = test_company_is_never_a_location()
    r = r1 and r2 and r3
    print(f"\n{'✅ ALL PASS' if r else '❌ SOME FAILED'}")
    sys.exit(0 if r else 1)


if __name__ == "__main__":
    main()
