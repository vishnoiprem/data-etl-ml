"""
tests/test_dedup_key.py — verify the (company, email, role) dedup key
allows different roles at the same company to be inserted separately.

Run:  python3 -m tests.test_dedup_key
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFTS = HERE.parent
sys.path.insert(0, str(DRAFTS))


def test_dedup_keys_distinct_for_different_roles():
    """The whole point of the bug fix — make sure same (co, em) with
    different roles is treated as different dedup keys. We use a fresh
    company + email so the DB has no existing rows to collide with."""
    from find_more_leads import insert_leads
    import time
    uniq = f"test-dedup-{int(time.time())}"
    co = f"TestCo-{uniq}"
    em = f"apply@{uniq}.example.com"
    leads = [
        {"company": co, "role": "Senior ML Engineer", "contact_email": em,
         "source": "test", "source_url": "", "jd_text": ""},
        {"company": co, "role": "Staff Engineer, Ray Core", "contact_email": em,
         "source": "test", "source_url": "", "jd_text": ""},
        {"company": co, "role": "ML Infrastructure Lead", "contact_email": em,
         "source": "test", "source_url": "", "jd_text": ""},
    ]
    inserted, skipped, errs = insert_leads(leads, dry=True)
    print(f"  3 distinct roles → inserted={inserted} skipped={skipped} errs={errs}")
    assert inserted == 3, f"expected 3 inserts, got {inserted} (skipped={skipped})"
    assert skipped == 0
    assert errs == 0
    print("  ✓ different roles do not collide on (company, email)")


def test_dedup_keys_collapse_for_same_role():
    """Same (co, em, role) within a batch should be deduped to 1."""
    from find_more_leads import insert_leads

    leads = [
        {"company": "AcmeCo", "role": "Senior Engineer", "contact_email": "x@y.com",
         "source": "test", "source_url": "", "jd_text": ""},
        {"company": "AcmeCo", "role": "Senior Engineer", "contact_email": "x@y.com",
         "source": "test", "source_url": "", "jd_text": ""},
    ]
    inserted, skipped, errs = insert_leads(leads, dry=True)
    print(f"  2 duplicate (co, em, role) → inserted={inserted} skipped={skipped}")
    assert inserted == 1
    assert skipped == 1
    print("  ✓ duplicate (co, em, role) is collapsed to 1")


def test_junk_email_filtered():
    """JUNK_EMAIL_RE patterns should be rejected before dedup."""
    from find_more_leads import insert_leads, JUNK_EMAIL_RE

    # Sanity: verify JUNK regex matches what we expect
    assert JUNK_EMAIL_RE.search("careers@example.com")
    assert JUNK_EMAIL_RE.search("foo@example.org")
    assert JUNK_EMAIL_RE.search("hi@localhost")

    leads = [
        {"company": "JunkCo1", "role": "Eng", "contact_email": "careers@example.com",
         "source": "test", "source_url": "", "jd_text": ""},
        {"company": "JunkCo2", "role": "Eng", "contact_email": "foo@example.org",
         "source": "test", "source_url": "", "jd_text": ""},
    ]
    inserted, skipped, errs = insert_leads(leads, dry=True)
    print(f"  2 leads (both junk) → inserted={inserted} skipped={skipped}")
    assert inserted == 0
    assert skipped == 2
    print("  ✓ junk emails filtered out")


def test_legitimate_email_not_filtered():
    """Real recruiter emails should NOT match JUNK_EMAIL_RE."""
    from find_more_leads import insert_leads, JUNK_EMAIL_RE
    import time

    # These should not match JUNK
    for em in ["careers@anthropic.com", "talent@openai.com", "jobs@stripe.com"]:
        assert not JUNK_EMAIL_RE.search(em), f"{em} should not be junk"

    uniq = f"test-legit-{int(time.time())}"
    leads = [
        {"company": f"LegitCo-{uniq}", "role": "Eng", "contact_email": f"hr@{uniq}.com",
         "source": "test", "source_url": "", "jd_text": ""},
    ]
    inserted, skipped, errs = insert_leads(leads, dry=True)
    print(f"  1 legitimate lead → inserted={inserted} skipped={skipped}")
    assert inserted == 1
    assert skipped == 0
    print("  ✓ legitimate email passes JUNK filter")


if __name__ == "__main__":
    print("🧪 test_dedup_key")
    test_dedup_keys_distinct_for_different_roles()
    test_dedup_keys_collapse_for_same_role()
    test_junk_email_filtered()
    test_legitimate_email_not_filtered()
    print("  ✅ all passed")
