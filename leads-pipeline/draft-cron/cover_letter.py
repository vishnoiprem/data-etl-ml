"""
cover_letter.py — Single source of truth for the Avilx cold-email template.

Three functions:
    render_subject(lead)   -> str  (≤70 chars, Gmail-safe)
    render_text_body(lead) -> str  (plain text)
    render_html_body(lead) -> str  (inline-CSS HTML for SMTP)

Used by:
    - autopilot._build_cover_letter / _render_email_html
    - refine_pipeline._make_cover_letter (DB store, for tracking preview)

Env overrides:
    AVILX_NAME        default "Avilx"
    AVILX_TAGLINE     default "Global Build · Deploy · Engineers"
    AVILX_WEBSITE     default "avilx.com"
    AVILX_EMAIL       default "hello@avilx.com"
    AVILX_WHATSAPP    default "+6592716405"   (no leading + required)
    AVILX_FOUNDER     default "Prem Vishnoi"
    AVILX_HQ          default "Ha Noi, Vietnam"
"""

from __future__ import annotations

import os
import re
from typing import Tuple

# Env-overridable so the same template can be used for white-label sub-brands.
NAME = os.getenv("AVILX_NAME", "Avilx")
TAGLINE = os.getenv("AVILX_TAGLINE", "Global Build · Deploy · Engineers")
WEBSITE = os.getenv("AVILX_WEBSITE", "avilx.com").lstrip("https://").lstrip("http://")
EMAIL = os.getenv("AVILX_EMAIL", "hello@avilx.com")
WHATSAPP = os.getenv("AVILX_WHATSAPP", "+6592716405").lstrip("+")
FOUNDER = os.getenv("AVILX_FOUNDER", "Prem Vishnoi")
HQ = os.getenv("AVILX_HQ", "Ha Noi, Vietnam")
CLOUD_LIST = "AWS · Azure · GCP · Tencent · Alibaba"

# Stack terms lifted from the JD for the "Stack overlap I noticed:" line.
# Order is significant — first 8 are used.
STACK_TERMS = [
    "python", "java", "golang", "rust", "c++", "typescript", "javascript",
    "react", "node", "next.js", "django", "fastapi", "flask", "spring",
    "kubernetes", "k8s", "docker", "terraform", "ansible", "helm",
    "aws", "azure", "gcp", "tencent", "alibaba", "cloudflare",
    "spark", "hadoop", "kafka", "flink", "airflow", "dagster", "prefect",
    "snowflake", "databricks", "bigquery", "redshift", "postgres", "mysql",
    "dbt", "elt", "etl", "iceberg", "delta", "parquet", "avro",
    "pytorch", "tensorflow", "llm", "rag", "genai", "agent",
    "mlops", "scikit", "sklearn", "pandas", "numpy",
    "openai", "anthropic", "claude", "gemini", "mistral", "llama", "hugging",
    "vector", "embedding", "faiss", "qdrant", "weaviate", "pinecone", "chroma",
    "ci/cd", "devops", "sre", "observability", "prometheus", "grafana",
    "microservices", "grpc", "rest", "graphql", "api",
    "data engineering", "ml engineering", "backend", "platform",
]
STACK_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in STACK_TERMS) + r")\b",
    re.IGNORECASE,
)


def _extract_stack_overlap(jd: str) -> list[str]:
    """Pull a list of recognizable tech terms from a JD, in order, dedup."""
    if not jd:
        return []
    seen = set()
    out = []
    for m in STACK_RE.finditer(jd):
        term = m.group(1).lower()
        if term not in seen:
            seen.add(term)
            out.append(term)
    return out


def _trim(s: str, n: int) -> str:
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


def render_subject(lead: dict) -> str:
    """Subject line — Avilx for {company} — {role}, trimmed to ≤70 chars."""
    co = (lead.get("company") or "").strip() or "your team"
    role = (lead.get("role") or "this role").strip()
    co_short = co if len(co) <= 25 else co[:22] + "…"
    role_short = role if len(role) <= 30 else role[:27] + "…"
    subj = f"{NAME} for {co_short} — {role_short}"
    if len(subj) > 70:
        subj = subj[:67] + "…"
    return subj


def render_text_body(lead: dict) -> str:
    """Plain-text cover letter. Stored in `leads.cover_letter_body`."""
    co = (lead.get("company") or "").strip() or "your team"
    role = (lead.get("role") or "this role").strip()
    jd = lead.get("jd_text") or ""
    stack = _extract_stack_overlap(jd)
    stack_str = ", ".join(stack[:8]) if stack else "the stack in your JD"

    return (
        f"Hi {co} team,\n\n"
        f"Saw the {role} role — stack and scope look like a strong match. "
        f"Quick context if useful: I'm {FOUNDER}, I run {NAME} ({WEBSITE}), a "
        f"global {TAGLINE} pod out of {HQ}. 6-20 senior engineers, "
        f"AI/Data/ML/Cloud, **Databricks Champion** team, 7+ clouds ({CLOUD_LIST}), "
        f"8+ yrs avg, regulated-industry work.\n\n"
        f"Stack overlap I noticed: {stack_str}.\n\n"
        f"If your timeline is tight, happy to run a 4-week pilot pod or staff-aug "
        f"a senior — 2-week kickoff, remote delivery, NDA + IP clean. "
        f"15-min call this week worth it?\n\n"
        f"{FOUNDER}\n"
        f"{NAME} — {TAGLINE}\n"
        f"(AI · Data · ML · Cloud · Databricks · 7+ clouds)\n"
        f"Delivery: China · APAC · US · EU | HQ: {HQ}\n"
        f"{EMAIL} | wa.me/{WHATSAPP} | https://{WEBSITE}"
    )


# Minimal inline-CSS for the SMTP HTML body. The real HTML template lives in
# autopilot._render_email_html — this function is a fallback for leads that
# were enriched offline (e.g. refine_pipeline) where we just need a presentable
# preview stored alongside the lead.
_HTML_TEMPLATE = """\
<html><body style="font-family:Helvetica,Arial,sans-serif;color:#111;line-height:1.55;">
  <div style="max-width:600px;margin:0 auto;padding:24px;">
    <div style="background:linear-gradient(135deg,#0f172a,#1e3a8a);color:#fff;
                padding:18px 20px;border-radius:10px 10px 0 0;">
      <div style="font-size:20px;font-weight:600;">{name}.</div>
      <div style="opacity:.85;font-size:13px;margin-top:2px;">{tagline}</div>
    </div>
    <div style="background:#fff;border:1px solid #e5e7eb;border-top:0;padding:24px;border-radius:0 0 10px 10px;">
      <p>Hi {company} team,</p>
      <p>Saw the <b>{role}</b> role — stack and scope look like a strong match. \
Quick context if useful: I'm {founder}, I run {name} ({website}), a global {tagline} \
pod out of {hq}. 6-20 senior engineers, AI/Data/ML/Cloud, <b>Databricks Champion</b> \
team, 7+ clouds, 8+ yrs avg, regulated-industry work.</p>
      <p>Stack overlap I noticed: {stack_str}.</p>
      <p>If your timeline is tight, happy to run a 4-week pilot pod or staff-aug a senior — \
2-week kickoff, remote delivery, NDA + IP clean. 15-min call this week worth it?</p>
      <p style="margin-top:24px;">— {founder}<br>
        <span style="color:#6b7280;font-size:13px;">{name} · {tagline}</span><br>
        <span style="color:#6b7280;font-size:13px;">{email} · wa.me/{whatsapp} · {website}</span>
      </p>
    </div>
  </div>
</body></html>
"""


def render_html_body(lead: dict) -> str:
    """Inline-CSS HTML body — used as the SMTP body and as a stored preview."""
    co = (lead.get("company") or "").strip() or "your team"
    role = (lead.get("role") or "this role").strip()
    jd = lead.get("jd_text") or ""
    stack = _extract_stack_overlap(jd)
    stack_str = ", ".join(stack[:8]) if stack else "the stack in your JD"
    return _HTML_TEMPLATE.format(
        name=NAME,
        tagline=TAGLINE,
        company=co,
        role=role,
        founder=FOUNDER,
        website=WEBSITE,
        hq=HQ,
        stack_str=stack_str,
        email=EMAIL,
        whatsapp=WHATSAPP,
    )


def render(lead: dict) -> Tuple[str, str, str]:
    """Convenience: returns (subject, text_body, html_body)."""
    return render_subject(lead), render_text_body(lead), render_html_body(lead)


# ============================================================
# Solo-apply mode (Prem personally applies for the role)
# ============================================================
# When apply_mode == 'solo', the lead is one Prem wants to apply to
# himself — not pitch Avilx as a pod. Subject/body shift to a personal
# application: "I'm Prem, this is why I'm a fit, here's my resume,
# can we talk?" — no pod mention, no pricing, no "happy to staff aug"
# language. Resume PDF is still attached by autopilot._pick_resume().
def render_solo_subject(lead: dict) -> str:
    """Subject line — Prem Vishnoi for {company} — {role}, trimmed to ≤70."""
    co = (lead.get("company") or "").strip() or "your team"
    role = (lead.get("role") or "this role").strip()
    co_short = co if len(co) <= 20 else co[:17] + "…"
    role_short = role if len(role) <= 30 else role[:27] + "…"
    subj = f"{FOUNDER} for {co_short} — {role_short}"
    if len(subj) > 70:
        subj = subj[:67] + "…"
    return subj


def render_solo_text_body(lead: dict) -> str:
    """Plain-text solo-apply cover letter. Prem personally applying."""
    co = (lead.get("company") or "").strip() or "your team"
    role = (lead.get("role") or "this role").strip()
    jd = lead.get("jd_text") or ""
    stack = _extract_stack_overlap(jd)
    stack_str = ", ".join(stack[:6]) if stack else "the stack in your JD"
    is_remote = bool(re.search(r"\b(remote|anywhere|work from home|wfh)\b", jd, re.I))
    remote_phrase = "remote" if is_remote else "global"

    return (
        f"Hi {co} team,\n\n"
        f"I'm applying for the {role} role personally — not as a recruiter. "
        f"I'm {FOUNDER}, 15+ years shipping AI/data/cloud systems across "
        f"{CLOUD_LIST} plus Huawei, Oracle, and on-prem. Most recent work spans "
        f"RAG/agentic systems on Databricks, multi-tenant ML platforms, and "
        f"regulated-industry data (banking, healthcare, MLPS in China).\n\n"
        f"Stack overlap I noticed in your JD: {stack_str}. I've shipped all of "
        f"these in production at scale.\n\n"
        f"Resume attached. Happy to do a 30-min technical screen this week and "
        f"share 1-2 relevant case studies ({remote_phrase} delivery, async-first, "
        f"NDA + IP clean).\n\n"
        f"{FOUNDER}\n"
        f"({NAME} founder · also available for senior pod engagements)\n"
        f"Delivery: China · APAC · US · EU | HQ: {HQ}\n"
        f"{EMAIL} | wa.me/{WHATSAPP} | https://{WEBSITE}"
    )


def render_solo_html_body(lead: dict) -> str:
    """Inline-CSS HTML version of the solo cover letter."""
    co = (lead.get("company") or "").strip() or "your team"
    role = (lead.get("role") or "this role").strip()
    jd = lead.get("jd_text") or ""
    stack = _extract_stack_overlap(jd)
    stack_str = ", ".join(stack[:6]) if stack else "the stack in your JD"
    is_remote = bool(re.search(r"\b(remote|anywhere|work from home|wfh)\b", jd, re.I))
    remote_phrase = "remote" if is_remote else "global"
    return _SOLO_HTML_TEMPLATE.format(
        name=FOUNDER, tagline=f"Solo application — {role} at {co}",
        cloud_list=CLOUD_LIST, hq=HQ, email=EMAIL, whatsapp=WHATSAPP,
        website=WEBSITE, co=co, role=role, stack_str=stack_str,
        remote_phrase=remote_phrase, brand=NAME,
    )


_SOLO_HTML_TEMPLATE = """\
<html><body style="font-family:Helvetica,Arial,sans-serif;color:#111;line-height:1.55;">
  <div style="max-width:600px;margin:0 auto;padding:24px;">
    <div style="background:linear-gradient(135deg,#7c2d12,#9a3412);color:#fff;
                padding:18px 20px;border-radius:10px 10px 0 0;">
      <div style="font-size:20px;font-weight:600;">{name}.</div>
      <div style="opacity:.85;font-size:13px;margin-top:2px;">{tagline}</div></div>
    <div style="border:1px solid #e5e7eb;border-top:0;border-radius:0 0 10px 10px;
                padding:20px;background:#fff;">
      <p>Hi {co} team,</p>
      <p>I'm applying for the <b>{role}</b> role personally — not as a recruiter.
         I'm {name}, 15+ years shipping AI/data/cloud systems across {cloud_list}
         plus Huawei, Oracle, and on-prem. Most recent work spans RAG/agentic
         systems on Databricks, multi-tenant ML platforms, and
         regulated-industry data (banking, healthcare, MLPS in China).</p>
      <p>Stack overlap I noticed in your JD: <b>{stack_str}</b>. I've shipped
         all of these in production at scale.</p>
      <p>Resume attached. Happy to do a 30-min technical screen this week and
         share 1-2 relevant case studies ({remote_phrase} delivery, async-first,
         NDA + IP clean).</p>
      <p style="margin-top:28px;">— {name}<br/>
        <span style="color:#6b7280;font-size:13px;">({brand} founder · also
        available for senior pod engagements)<br/>
        Delivery: China · APAC · US · EU | HQ: {hq}<br/>
        {email} | wa.me/{whatsapp} | https://{website}</span></p>
    </div>
  </div>
</body></html>
"""


def render_solo(lead: dict) -> Tuple[str, str, str]:
    """Convenience: returns (subject, text_body, html_body) for solo mode."""
    return (
        render_solo_subject(lead),
        render_solo_text_body(lead),
        render_solo_html_body(lead),
    )


def render_for_mode(lead: dict) -> Tuple[str, str, str]:
    """Dispatch to the right renderer based on lead.apply_mode.

    Modes:
      'pitch_pod'       → Avilx company pitch (render_*) — default
      'apply_personal'  → Prem personally applies for the role (render_solo_*)

    Unknown / unset values fall through to 'pitch_pod' for backward
    compatibility with leads created before the apply_mode column existed.
    """
    mode = (lead.get("apply_mode") or "pitch_pod").strip().lower()
    if mode == "apply_personal":
        return render_solo(lead)
    return render(lead)


# Public mode constants for callers that want to set the column explicitly
# (avoids typo-driven bugs like 'soloo' / 'soulo' silently becoming 'pod')
MODE_PITCH_POD = "pitch_pod"
MODE_APPLY_PERSONAL = "apply_personal"



if __name__ == "__main__":
    sample = {
        "company": "Anyscale",
        "role": "Senior ML Platform Engineer",
        "jd_text": "Looking for a senior engineer with Python, Ray, Kubernetes, "
                   "AWS, Spark, and Kafka experience to build our distributed "
                   "ML platform. RAG, LLMs, and vector databases a plus.",
    }
    subj, txt, html = render(sample)
    print("SUBJECT:", subj)
    print("---TEXT---")
    print(txt)
    print("---HTML---")
    print(html)
