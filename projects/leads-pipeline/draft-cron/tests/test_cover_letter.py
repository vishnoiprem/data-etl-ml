"""
tests/test_cover_letter.py — verify the cover-letter renderer is safe with
lead values that contain literal `{` or `}` (which would otherwise raise
KeyError in str.format).
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import cover_letter  # noqa: E402


# ============================================================
# Brace escape — the original bug: cover_letter._render_template
# (or str.format on the HTML template) raised KeyError when the JD
# or company name contained `{` or `}`.
# ============================================================

def test_html_body_preserves_braces_in_company():
    """A company name with literal `{}` must not crash and must be
    preserved verbatim in the rendered HTML."""
    html = cover_letter.render_html_body({
        "company": "Acme {Corp}",
        "role": "Senior Engineer",
        "jd_text": "",
        "apply_mode": "pitch_pod",
    })
    assert "Acme {Corp}" in html, f"company braces lost: {html!r}"


def test_html_body_preserves_braces_in_role():
    """Same for the role field — `{{}}` in a role is unusual but legal."""
    html = cover_letter.render_html_body({
        "company": "Anyscale",
        "role": "Senior {Engineer}",
        "jd_text": "",
        "apply_mode": "pitch_pod",
    })
    assert "Senior {Engineer}" in html


def test_solo_html_body_preserves_braces():
    """apply_personal / solo path must also be brace-safe."""
    html = cover_letter.render_solo_html_body({
        "company": "Acme {Corp}",
        "role": "Senior {Engineer}",
        "jd_text": "Some text",
        "apply_mode": "apply_personal",
    })
    assert "Acme {Corp}" in html
    assert "Senior {Engineer}" in html


def test_render_template_leaves_unknown_placeholders_alone():
    """A typo in the template (e.g. {naem} instead of {name}) should be
    visible in the output, not raise KeyError."""
    out = cover_letter._render_template("hello {naem}!", {"name": "world"})
    assert out == "hello {naem}!", (
        "missing keys should be left as-is so typos are visible"
    )


# ============================================================
# Stack overlap — hard cap so monster JDs don't produce unbounded lists
# ============================================================

def test_extract_stack_overlap_capped_at_16():
    """A JD mentioning every term in STACK_TERMS twice should still
    return <= 16 unique terms (the cap)."""
    # Build a JD that contains all ~60 STACK_TERMS at least once
    big_jd = " ".join(cover_letter.STACK_TERMS * 3)
    terms = cover_letter._extract_stack_overlap(big_jd)
    assert len(terms) <= 16, f"stack overlap not capped: got {len(terms)}"
    # And it should be > 0 (sanity — the regex actually matched something)
    assert len(terms) > 0


# ============================================================
# render_for_mode dispatch
# ============================================================

def test_render_for_mode_dispatches_to_solo():
    """apply_personal must route to the solo renderer (subject line
    starts with [Personal Application])."""
    subj, _txt, _html = cover_letter.render_for_mode({
        "company": "X",
        "role": "Y",
        "apply_mode": "apply_personal",
    })
    assert subj.startswith("[Personal Application]"), subj


def test_render_for_mode_default_is_pod():
    """Missing or unknown apply_mode falls through to pod pitch."""
    subj, _txt, _html = cover_letter.render_for_mode({
        "company": "X",
        "role": "Y",
        # no apply_mode
    })
    assert subj.startswith("[Avilx Pod Pitch]"), subj
