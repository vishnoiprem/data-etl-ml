"""
tests/test_bounce_deny_persistence.py — verify that bounce_deny_store
writes are visible to a fresh subprocess (the bug it was meant to fix).

Run:  python3 -m tests.test_bounce_deny_persistence
"""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFTS = HERE.parent
sys.path.insert(0, str(DRAFTS))

# Use the *current* Python interpreter for the subprocess check, not a
# hard-coded venv path. The previous code pointed at a local-only
# venv that doesn't exist on CI (the GitHub Actions Ubuntu runner
# uses /opt/hostedtoolcache/.../python instead), which made the
# subprocess calls raise FileNotFoundError and the whole test file
# exit with status 1 — failing the leads-ci job on every push.
VENV_PY = sys.executable


def _fresh_subprocess_count() -> int:
    """Start a fresh Python and ask it how many domains are in BOUNCE_DENY."""
    out = subprocess.check_output(
        [VENV_PY, "-c",
         f"import sys; sys.path.insert(0, r'{DRAFTS}'); "
         f"from state.bounce_deny_store import BOUNCE_DENY; "
         f"print(len(BOUNCE_DENY))"],
        text=True,
    ).strip()
    return int(out)


def test_add_persists_across_subprocesses():
    """Add a unique domain in process A, then read it from process B."""
    from state.bounce_deny_store import BOUNCE_DENY, add, remove

    test_domain = f"test-bounce-{int(time.time())}.example.com"
    # Sanity: it shouldn't already be in there
    assert test_domain not in BOUNCE_DENY
    # Add
    added = add(test_domain)
    assert added, "add() should return True for a new domain"
    # Read in fresh process
    fresh_count = _fresh_subprocess_count()
    print(f"  fresh subprocess count after add: {fresh_count}")
    # Verify it's in there from a fresh process
    out = subprocess.check_output(
        [VENV_PY, "-c",
         f"import sys; sys.path.insert(0, r'{DRAFTS}'); "
         f"from state.bounce_deny_store import BOUNCE_DENY; "
         f"print('{test_domain}' in BOUNCE_DENY)"],
        text=True,
    ).strip()
    assert out == "True", f"expected test domain visible from fresh process, got {out!r}"
    print(f"  ✓ {test_domain} visible from fresh subprocess")
    # Cleanup
    remove(test_domain)
    # And confirm removal propagated
    out = subprocess.check_output(
        [VENV_PY, "-c",
         f"import sys; sys.path.insert(0, r'{DRAFTS}'); "
         f"from state.bounce_deny_store import BOUNCE_DENY; "
         f"print('{test_domain}' in BOUNCE_DENY)"],
        text=True,
    ).strip()
    assert out == "False", f"expected test domain removed, got {out!r}"
    print(f"  ✓ {test_domain} removed from fresh subprocess")


def test_add_is_idempotent():
    """Adding the same domain twice should be a no-op the second time."""
    from state.bounce_deny_store import BOUNCE_DENY, add, remove

    test_domain = f"test-idem-{int(time.time())}.example.com"
    a = add(test_domain)
    b = add(test_domain)
    assert a and not b, f"first add should succeed, second should be no-op (a={a}, b={b})"
    print(f"  ✓ add() is idempotent")
    remove(test_domain)


def test_dedup_and_deny_writes_to_disk():
    """refine_pipeline.dedup_and_deny() should persist via bounce_deny_store."""
    from state.bounce_deny_store import BOUNCE_DENY, add, remove
    from refine_pipeline import dedup_and_deny

    # Add a domain via dedup_and_deny
    test_domain = f"test-dad-{int(time.time())}.example.com"
    with_ = _fresh_subprocess_count()
    # Inject a fake bounced lead, run dedup_and_deny, verify
    from db.lead_store import get_cursor
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO leads (tracking_id, company, role, contact_email, source,
                               source_url, jd_text, status, sent_at,
                               created_at, updated_at)
            VALUES ('test-dad', 'FakeDADCo', 'Eng', %s, 'test',
                    '', '', 'bounced', NOW(), NOW(), NOW())
            RETURNING id
        """, (f"x@{test_domain}",))
        fake_id = cur.fetchone()["id"]
    try:
        dedup_and_deny(verbose=False)
        # Verify it's in BOUNCE_DENY in this process
        assert test_domain in BOUNCE_DENY, f"test domain not in BOUNCE_DENY after dedup_and_deny"
        # Verify it's in BOUNCE_DENY in a fresh process
        out = subprocess.check_output(
            [VENV_PY, "-c",
             f"import sys; sys.path.insert(0, r'{DRAFTS}'); "
             f"from state.bounce_deny_store import BOUNCE_DENY; "
             f"print('{test_domain}' in BOUNCE_DENY)"],
            text=True,
        ).strip()
        assert out == "True", f"dedup_and_deny did not persist to disk (got {out!r})"
        print(f"  ✓ dedup_and_deny() persisted {test_domain} to disk")
    finally:
        with get_cursor() as cur:
            cur.execute("DELETE FROM leads WHERE id = %s", (fake_id,))
        # Don't auto-remove from BOUNCE_DENY; the next dedup_and_deny will see
        # the lead is gone and skip it. To clean, just call remove().
        remove(test_domain)


if __name__ == "__main__":
    print("🧪 test_bounce_deny_persistence")
    test_add_persists_across_subprocesses()
    test_add_is_idempotent()
    test_dedup_and_deny_writes_to_disk()
    print("  ✅ all passed")
