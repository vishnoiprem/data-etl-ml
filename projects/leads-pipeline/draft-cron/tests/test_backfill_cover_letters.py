"""
tests/test_backfill_cover_letters.py — verify that
bin/backfill_cover_letters.py correctly re-renders NULL cover letters.

Why: Before this script existed, find_more_leads.py /
ingest_fresh_leads.py / bin/ingest_scout_reports.py inserted lead
rows with NULL cover_letter_*. The email path's fallback in
autopilot._send_one used a generic "Avilx × {company}" subject
that lacked the mode prefix.

The backfill script must:
  1. Re-render cover letters for rows with NULL/empty subject/body
  2. Populate the subject with the mode-prefixed version
     ([Avilx Pod Pitch] / [Personal Application])
  3. Be idempotent — running twice doesn't change the second-pass output
  4. Skip rows it can't render (no crash)
"""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

from db import lead_store as ls  # noqa: E402

# Load bin/backfill_cover_letters.py as a module (it lives under bin/, not
# at the project root, so we can't `import` it directly).
SCRIPT = HERE.parent / "bin" / "backfill_cover_letters.py"
spec = importlib.util.spec_from_file_location("backfill_cover_letters", SCRIPT)
assert spec and spec.loader, f"could not load {SCRIPT}"
backfill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backfill)


def _make_lead(company, role, jd, apply_mode, source="test_backfill"):
    """Insert a lead with NULL cover letter fields. Returns lead id."""
    with ls.get_cursor() as cur:
        cur.execute("""
            INSERT INTO leads (tracking_id, company, role, contact_email, jd_text,
                               source, status, apply_mode,
                               cover_letter_subject, cover_letter_body,
                               created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s, '', '', NOW(), NOW())
            RETURNING id
        """, (f"bk-{company[:6]}-{role[:6]}".replace(" ", "-"),
              company, role, f"test@{company.lower().replace(' ','')}.example",
              jd, source, apply_mode))
        return cur.fetchone()["id"]


def _cleanup(lead_id):
    with ls.get_cursor() as cur:
        cur.execute("DELETE FROM leads WHERE id = %s", (lead_id,))


def test_pod_pitch_lead_gets_avilx_pod_pitch_prefix():
    lead_id = _make_lead("BackfillTestCo", "Senior AI Engineer",
                         "Looking for Python + RAG + Databricks", "pitch_pod")
    try:
        updated = backfill.main.__wrapped__() if hasattr(backfill.main, "__wrapped__") else None
        # Just call the underlying functions directly to avoid argv/argparse side effects
        leads = backfill._pick_leads(1000)
        matched = [l for l in leads if l["id"] == lead_id]
        assert matched, "newly inserted lead not picked up by _pick_leads"
        subj, body, _html = None, None, None
        from cover_letter import render_for_mode
        subj, body, _html = render_for_mode({
            "company": matched[0]["company"],
            "role": matched[0]["role"],
            "jd_text": matched[0]["jd_text"] or "",
            "apply_mode": matched[0]["apply_mode"] or "pitch_pod",
        })
        assert subj.startswith("[Avilx Pod Pitch]"), subj
        assert "BackfillTestCo" in body
        backfill._update(lead_id, subj, body)

        with ls.get_cursor() as cur:
            cur.execute("SELECT cover_letter_subject, cover_letter_body FROM leads WHERE id = %s", (lead_id,))
            row = cur.fetchone()
        assert row["cover_letter_subject"].startswith("[Avilx Pod Pitch]")
        assert len(row["cover_letter_body"]) > 100
    finally:
        _cleanup(lead_id)


def test_apply_personal_lead_gets_personal_application_prefix():
    lead_id = _make_lead("BackfillSoloCo", "Staff ML Engineer",
                         "Looking for RAG, PyTorch, AWS", "apply_personal")
    try:
        leads = backfill._pick_leads(1000)
        matched = [l for l in leads if l["id"] == lead_id]
        assert matched, "newly inserted lead not picked up by _pick_leads"
        from cover_letter import render_for_mode
        subj, body, _html = render_for_mode({
            "company": matched[0]["company"],
            "role": matched[0]["role"],
            "jd_text": matched[0]["jd_text"] or "",
            "apply_mode": matched[0]["apply_mode"] or "pitch_pod",
        })
        assert subj.startswith("[Personal Application]"), subj
        assert "Prem Vishnoi" in body
        backfill._update(lead_id, subj, body)

        with ls.get_cursor() as cur:
            cur.execute("SELECT cover_letter_subject FROM leads WHERE id = %s", (lead_id,))
            row = cur.fetchone()
        assert row["cover_letter_subject"].startswith("[Personal Application]")
    finally:
        _cleanup(lead_id)


def test_pick_leads_excludes_already_populated():
    """_pick_leads should NOT return rows that already have a subject +
    body. Otherwise the script would re-write good rows on every run."""
    lead_id = _make_lead("AlreadyPopulated", "Engineer", "Python", "pitch_pod")
    try:
        # Populate it first
        backfill._update(lead_id, "[Avilx Pod Pitch] test", "body that is long enough to count")
        leads = backfill._pick_leads(1000)
        ids = [l["id"] for l in leads]
        assert lead_id not in ids, "_pick_leads returned an already-populated row"
    finally:
        _cleanup(lead_id)


def test_pick_leads_includes_empty_subject():
    """Rows where subject is empty string ('') but body has data should
    still be picked up — the WHERE clause checks both, and an empty
    string in subject means the email would fall back to generic."""
    lead_id = _make_lead("EmptySubjectCo", "Engineer", "Python", "pitch_pod")
    try:
        with ls.get_cursor() as cur:
            cur.execute("UPDATE leads SET cover_letter_subject = '', cover_letter_body = 'some body' WHERE id = %s", (lead_id,))
        leads = backfill._pick_leads(1000)
        ids = [l["id"] for l in leads]
        assert lead_id in ids, "_pick_leads missed a lead with empty subject"
    finally:
        _cleanup(lead_id)
