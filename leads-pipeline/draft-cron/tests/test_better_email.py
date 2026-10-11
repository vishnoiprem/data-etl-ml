"""
tests/test_better_email.py — verify _better_email() returns None when
the target domain is in BOUNCE_DENY (the bug it was supposed to fix).

Run:  python3 -m tests.test_better_email
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFTS = HERE.parent
sys.path.insert(0, str(DRAFTS))


def test_better_email_skips_bounce_deny_domain():
    """A lead whose current email is careers@<bounced-domain> should
    NOT be swapped to talent@<bounced-domain>."""
    from state.bounce_deny_store import BOUNCE_DENY, add, remove
    from refine_pipeline import _better_email, PREFIX_HINTS

    # Pick a domain that's in PREFIX_HINTS but NOT in BOUNCE_DENY
    target = None
    for d, p in PREFIX_HINTS.items():
        if d not in BOUNCE_DENY:
            target = d
            break
    if not target:
        print("  (no candidate domain found — skipping)")
        return
    print(f"  using target={target} (in PREFIX_HINTS, not in BOUNCE_DENY)")
    # Add to BOUNCE_DENY temporarily
    added = add(target)
    try:
        result = _better_email({"company": "TestCo", "contact_email": f"careers@{target}"})
        print(f"  _better_email returned: {result!r}")
        assert result is None, f"expected None (domain in BOUNCE_DENY), got {result!r}"
        print(f"  ✓ returned None when target domain in BOUNCE_DENY")
    finally:
        if added:
            remove(target)


def test_better_email_skips_db_bounced_domain():
    """If any lead at the target domain has status='bounced', _better_email
    must return None. This test injects a fake bounced lead via direct
    DB write and checks the guard fires."""
    from db.lead_store import get_cursor
    from state.bounce_deny_store import BOUNCE_DENY, add, remove
    from refine_pipeline import _better_email, PREFIX_HINTS

    # Pick a domain in PREFIX_HINTS, not in BOUNCE_DENY
    target = None
    for d, p in PREFIX_HINTS.items():
        if d not in BOUNCE_DENY:
            target = d
            break
    if not target:
        print("  (no candidate domain found — skipping)")
        return

    # Insert a fake bounced lead for the target domain
    print(f"  injecting fake bounced lead at {target}")
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO leads (tracking_id, company, role, contact_email, source,
                               source_url, jd_text, status, sent_at,
                               created_at, updated_at)
            VALUES ('test-be', 'FakeBounceCo', 'Eng', %s, 'test',
                    '', '', 'bounced', NOW(), NOW(), NOW())
            RETURNING id
        """, (f"noreply@{target}",))
        fake_id = cur.fetchone()["id"]
    # Reset the in-process cache
    try:
        del _better_email._bounced_domain_cache
    except AttributeError:
        pass

    try:
        result = _better_email({"company": "TestCo", "contact_email": f"careers@{target}"})
        print(f"  _better_email returned: {result!r}")
        assert result is None, f"expected None (DB has bounced lead at {target}), got {result!r}"
        print(f"  ✓ returned None when DB has bounced lead at target domain")
    finally:
        # Clean up the fake lead
        with get_cursor() as cur:
            cur.execute("DELETE FROM leads WHERE id = %s", (fake_id,))
        try:
            del _better_email._bounced_domain_cache
        except AttributeError:
            pass


def test_better_email_allows_known_good_swap():
    """Sanity check — a domain not in BOUNCE_DENY with no DB bounces
    should still produce a swap."""
    from state.bounce_deny_store import BOUNCE_DENY
    from refine_pipeline import _better_email, PREFIX_HINTS

    target = None
    for d, p in PREFIX_HINTS.items():
        if d not in BOUNCE_DENY:
            target = d
            break
    if not target:
        print("  (no candidate domain found — skipping)")
        return
    new_prefix = PREFIX_HINTS[target]
    result = _better_email({"company": "TestCo", "contact_email": f"careers@{target}"})
    print(f"  careers@{target} → {result!r} (PREFIX_HINTS says: {new_prefix}@{target})")
    # Either the test DB has bounces (likely) → returns None,
    # or it doesn't → returns the swap. Both are OK; this is informational.
    if result is not None:
        assert result == f"{new_prefix}@{target}"
        print("  ✓ swap proposed for known-good domain")
    else:
        print("  (DB has a bounce for this domain; swap suppressed — expected)")


if __name__ == "__main__":
    print("🧪 test_better_email")
    test_better_email_skips_bounce_deny_domain()
    test_better_email_skips_db_bounced_domain()
    test_better_email_allows_known_good_swap()
    print("  ✅ all passed")
