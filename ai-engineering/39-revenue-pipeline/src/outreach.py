"""
outreach.py — Generate a personalized cold email per qualified lead.

The LLM drafts a 4-6 sentence email that:
  1. Names the specific signal that triggered outreach (so it doesn't
     look like spam).
  2. States the consultant's relevant experience (1 sentence).
  3. Asks 1-2 qualifying questions (budget, timeline) — not a meeting.
  4. Includes a low-friction CTA (case studies, intro chat, etc.)

The stub router returns a templated email with the company name
stitched in. Good enough for `make demo`, replaceable for production.
"""

from __future__ import annotations

from dataclasses import dataclass

from qualifier import Qualification
from router import LLMRouter
from signals import Lead


@dataclass
class Email:
    subject: str
    body: str
    to: str | None = None   # contact if known


OUTREACH_SYSTEM = """You are a cold-email writer for an independent AI/data
consultant (Prem). The consultant's niche: LLM/RAG/agent engineering, ML
platform, data pipelines. Past work: Anthropic eval harness, Stripe fraud ML,
Mastra agent framework. Tone: direct, technical, no marketing fluff. Length:
under 120 words. Goal: get a 1-sentence reply confirming budget + timeline,
NOT book a meeting. No emojis. No exclamation points. No attachments. Sign as
'— Prem'."""


def draft(lead: Lead, q: Qualification, router: LLMRouter) -> Email:
    """Generate a personalized cold email for one qualified lead."""
    prompt = (
        f"Company: {lead.company}\n"
        f"Title: {lead.title}\n"
        f"Source signal: {lead.text[:500]}\n"
        f"Qualification: score={q.score}/100, est. deal ${q.deal_usd}\n"
        f"Top reasons: {'; '.join(q.reasons)}\n\n"
        f"Draft a cold email that references the specific signal and asks 1-2 "
        f"qualifying questions (budget + timeline). Output in this exact format:\n"
        f"Subject: <subject line>\n"
        f"Body:\n<body>"
    )
    text = router.complete(prompt, system=OUTREACH_SYSTEM, max_tokens=400)
    return _parse_email(text, to=lead.contact)


def _parse_email(text: str, to: str | None = None) -> Email:
    """Parse `Subject: ...\nBody:\n...` format. Falls back to a flat subject."""
    subject = ""
    body = text.strip()
    m_subj = re.search(r"^Subject:\s*(.+)$", body, re.M)
    if m_subj:
        subject = m_subj.group(1).strip()
        body = body[m_subj.end():].strip()
    # Strip leading "Body:" or "Body" line if present
    body = re.sub(r"^Body:\s*\n", "", body)
    if not subject:
        # Use the first non-empty line as the subject
        first = next((ln.strip() for ln in body.splitlines() if ln.strip()), "Quick question")
        subject = first[:80]
        body = "\n".join(body.splitlines()[1:]).strip()
    return Email(subject=subject, body=body, to=to)


# pre-compile the regex at module import so we don't re-parse on every call
import re  # noqa: E402  (deliberately at bottom for clarity)


def draft_batch(
    qualified: list[tuple[Lead, Qualification]], router: LLMRouter
) -> list[tuple[Lead, Qualification, Email]]:
    """Generate one email per qualified lead."""
    out: list[tuple[Lead, Qualification, Email]] = []
    for ld, q in qualified:
        try:
            out.append((ld, q, draft(ld, q, router)))
        except Exception as e:
            # Don't lose the lead on outreach failure; emit a placeholder
            out.append((
                ld, q,
                Email(subject=f"(outreach error) {ld.company}", body=str(e), to=ld.contact),
            ))
    return out