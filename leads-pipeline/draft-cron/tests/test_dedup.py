"""
tests/test_dedup.py — verify find_duplicate behaves correctly.

The OLD dangerous behavior: dedup by email alone (would false-positive
when a recruiter changed companies).
The NEW safe behavior: dedup by (company, role) first, then (company, email).
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

from db.lead_store import find_duplicate, insert_lead  # noqa


# These tests assume a clean DB or unique company names per run.
# Each test uses a UUID-like suffix in the company name so they don't
# collide with prior runs.
import uuid


def _insert(company, role, email):
    return insert_lead({
        "company": company,
        "role": role,
        "contact_email": email,
        "source_url": "",
        "jd_text": "",
        "cover_letter_subject": "test",
        "cover_letter_body": "test",
    }, source="test_dedup")


def test_company_role_dedup():
    """Same company + same role → should be a duplicate."""
    print("🧪 test_company_role_dedup")
    company = f"TestCo-{uuid.uuid4().hex[:6]}"
    role = "ML Engineer"
    email1 = f"jobs1-{uuid.uuid4().hex[:4]}@example.com"
    id1 = _insert(company, role, email1)
    dup = find_duplicate(company, email1, role)
    ok = dup is not None and dup["id"] == id1
    print(f"  {'✅' if ok else '❌'} dup detected (id={id1}, found={dup and dup['id']})")
    return ok


def test_company_role_different_email():
    """Same company + same role but different email → still duplicate (the role post is a dup)."""
    print("🧪 test_company_role_different_email")
    company = f"TestCo-{uuid.uuid4().hex[:6]}"
    role = "Senior AI Engineer"
    id1 = _insert(company, role, f"a-{uuid.uuid4().hex[:4]}@example.com")
    dup = find_duplicate(company, f"b-{uuid.uuid4().hex[:4]}@example.com", role)
    ok = dup is not None and dup["id"] == id1
    print(f"  {'✅' if ok else '❌'} role-dup across different emails (found={dup and dup['id']})")
    return ok


def test_recruiter_changed_jobs():
    """Recruiter changed companies → should NOT be a duplicate (was the dangerous case)."""
    print("🧪 test_recruiter_changed_jobs")
    suffix = uuid.uuid4().hex[:6]
    company_a = f"OldCo-{suffix}"
    company_b = f"NewCo-{suffix}"
    same_email = f"recruiter-{suffix}@example.com"
    id_a = _insert(company_a, "Eng role 1", same_email)
    # Now they're at NewCo — should NOT match
    dup = find_duplicate(company_b, same_email, "Eng role 2")
    ok = dup is None
    print(f"  {'✅' if ok else '❌'} new-company same-email NOT deduped (would have wrongly matched id={id_a})")
    return ok


def test_same_company_different_role():
    """Same company, different role (e.g. re-org) → could legitimately be a new lead."""
    print("🧪 test_same_company_different_role")
    company = f"TestCo-{uuid.uuid4().hex[:6]}"
    id1 = _insert(company, "ML Engineer", f"jobs-{uuid.uuid4().hex[:4]}@example.com")
    dup = find_duplicate(company, f"jobs-other-{uuid.uuid4().hex[:4]}@example.com", "Data Engineer")
    # No (company, role) match, no (company, email) match → not a dup
    ok = dup is None
    print(f"  {'✅' if ok else '❌'} different role same company NOT deduped (would have wrongly matched id={id1})")
    return ok


def main():
    results = [
        test_company_role_dedup(),
        test_company_role_different_email(),
        test_recruiter_changed_jobs(),
        test_same_company_different_role(),
    ]
    if all(results):
        print("\n✅ ALL DEDUP TESTS PASS")
        sys.exit(0)
    print(f"\n❌ {results.count(False)}/{len(results)} FAILED")
    sys.exit(1)


if __name__ == "__main__":
    main()
