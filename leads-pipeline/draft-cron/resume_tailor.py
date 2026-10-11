#!/usr/bin/env python3
"""
resume_tailor.py — Build a JD-tailored resume for each lead.

Strategy:
  - Start with a base resume (Pv_Cv_Data_Ai_2026.docx) that's already
    near-perfect for senior data/AI roles.
  - Rewrite the headline + summary to lead with the JD's primary signal
    (AI/LLM, data platform, cloud, full-stack, ML platform).
  - Re-rank the SKILLS block so JD-matching keywords appear first.
  - Drop or condense experience bullets that don't match the JD.
  - Save the tailored docx into a per-lead cache dir; the email
    pipeline picks the right file.

For now we don't re-emit a PDF (PDFs need LibreOffice or docx2pdf). We attach
the docx. If you have LibreOffice installed (`brew install libreoffice`),
set RENDER_PDF=1 to also render a PDF.
"""

import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

try:
    from docx import Document  # python-docx
    HAVE_DOCX = True
except ImportError:
    HAVE_DOCX = False

HERE = Path(__file__).parent
RESUME_DIR = Path(os.getenv(
    "RESUME_DIR",
    str(Path.home() / "PycharmProjects" / "data-etl-ml" / "Resume")
))
TAILORED_DIR = HERE / ".tailored_resumes"
TAILORED_DIR.mkdir(exist_ok=True)

# ---- family classifiers -------------------------------------------------

ROLE_FAMILIES = [
    ("agentic_ai", re.compile(
        r"\b(agentic|multi[- ]?agent|autonomous agent|AI agent|LangChain|LlamaIndex|AutoGen|crew.?ai|"
        r"tool[- ]?use|orchestration|planning)\b", re.I)),
    ("llm_ai", re.compile(
        r"\b(LLM|GPT[- ]?4|Claude|Gemini|Llama|RAG|retrieval|vector (?:db|store|search)|"
        r"embedding|fine[- ]?tun|prompt engineer|chat[- ]?bot|hugging ?face|transformer)\b", re.I)),
    ("ml_platform", re.compile(
        r"\b(ML platform|MLOps|ML infrastructure|model serving|model deployment|inference|"
        r"feature store|Triton|KServe|Seldon|BentoML|weights ?& ?biases|wandb|neptune)\b", re.I)),
    ("data_platform", re.compile(
        r"\b(Databricks|Snowflake|Apache Spark|Spark |Kafka|Flink|Airflow|dbt|"
        r"lakehouse|Delta Lake|Iceberg|data ?warehouse|data pipeline|ETL|ELT|"
        r"CDC|streaming|real[- ]?time)\b", re.I)),
    ("cloud_arch", re.compile(
        r"\b(AWS|Azure|GCP|Tencent|Alibaba|Oracle Cloud|multi[- ]?cloud|hybrid cloud|"
        r"Terraform|Kubernetes|k8s|EKS|AKS|GKE|cloud[- ]?native|cloud migration)\b", re.I)),
    ("genai_app", re.compile(
        r"\b(Generative AI|GenAI|chatbot|conversational AI|copilot|"
        r"document AI|summarization|search|recommendation system)\b", re.I)),
    ("full_stack", re.compile(
        r"\b(full[- ]?stack|React|Vue|Angular|Node\.?js|TypeScript|JavaScript|"
        r"frontend|back[- ]?end|REST|GraphQL|API)\b", re.I)),
    ("leadership", re.compile(
        r"\b(staff engineer|principal|architect|director|VP|head of|team lead|"
        r"manage (?:a )?team|mentor|hiring|roadmap)\b", re.I)),
]


def classify_jd(jd_text: str, role: str) -> List[str]:
    """Return a ranked list of role-family tags that apply to this JD."""
    text = (jd_text or "") + " " + (role or "")
    scores = {}
    for name, pat in ROLE_FAMILIES:
        matches = len(pat.findall(text))
        if matches:
            scores[name] = matches
    # Always include data_platform if nothing else does (Prem's core)
    if not scores:
        scores["data_platform"] = 1
    return sorted(scores.keys(), key=lambda k: -scores[k])


# ---- headline / summary rewriters ---------------------------------------

HEADLINES = {
    "agentic_ai": "Senior AI/Agentic Systems Engineer | LLM + RAG + Multi-Agent",
    "llm_ai":     "Senior AI/LLM Engineer | RAG · Vector · LLM Production",
    "ml_platform":"Senior ML Platform Engineer | MLOps + Model Serving",
    "data_platform": "Senior Data Platform Engineer | Lakehouse + Real-Time Streaming",
    "cloud_arch": "Senior Cloud Architect | AWS · Azure · Multi-Cloud",
    "genai_app":  "Senior GenAI Engineer | LLMs · RAG · Chatbots",
    "full_stack": "Senior Full-Stack Engineer | Data + AI + Cloud",
    "leadership": "Head of Data / Engineering Leader | 25+ engineers, $2M+ budget",
}


SUMMARIES = {
    "agentic_ai": (
        "Senior AI engineer with 15+ years shipping production ML and the last "
        "3 years deep in LLM/RAG/agent systems. Built HIPAA-aware RAG for healthtech "
        "(replaced $400K/yr vendor) and multi-agent KYC for fintech (90s/case vs 18min). "
        "Hands-on with LangChain, LlamaIndex, vector stores, and tool-use orchestration. "
        "Senior pod out of Ha Noi — Databricks Champion team, 7+ clouds, 8+ yrs avg."
    ),
    "llm_ai": (
        "Senior LLM/AI engineer focused on production RAG, vector search, and "
        "LLM-powered applications at scale. Real production wins: top-10 US bank "
        "CDC lakehouse, HIPAA-aware RAG for healthtech, multi-region lakehouse "
        "for SEA fintech. Senior-only pod out of Ha Noi, Databricks Champion team, "
        "7+ clouds, 8+ yrs avg."
    ),
    "ml_platform": (
        "Senior ML platform engineer with deep Databricks/MLflow/KServe experience. "
        "Built lakehouse + MLOps stacks that ship 100M+ daily events at 99.99% uptime. "
        "Senior-only pod out of Ha Noi, 7+ clouds, regulated-industry work (banking, "
        "fintech, healthtech)."
    ),
    "data_platform": (
        "Senior data platform engineer — 15+ yrs building Databricks Lakehouse, "
        "Spark, Kafka, Flink at Alibaba, CP Group, PayPal scale. Built lakehouse "
        "handling 10B+ daily rows at 99.99% uptime. Senior pod out of Ha Noi, "
        "Databricks Champion team, 7+ clouds, regulated-environment work."
    ),
    "cloud_arch": (
        "Cloud-native architect with hands-on production across 7+ clouds (AWS, Azure, "
        "GCP, Tencent, Alibaba, Huawei, Oracle). Migrated workloads for top-tier SEA "
        "and US enterprises. Senior pod out of Ha Noi, regulated-industry focus, "
        "Databricks Champion team, 8+ yrs avg on the team."
    ),
    "genai_app": (
        "Generative AI engineer — production LLM apps (RAG, chat, summarization, "
        "recommendation) on regulated data. HIPAA-aware RAG for healthtech, "
        "agentic KYC for fintech, multi-cloud delivery. Senior pod out of Ha Noi, "
        "8+ yrs avg, 7+ clouds."
    ),
    "full_stack": (
        "Senior full-stack engineer with data/AI depth. Ships end-to-end (UI → API → "
        "data → ML) on Databricks Lakehouse, multi-cloud infra. Senior pod out of "
        "Ha Noi, 8+ yrs avg, regulated-industry work (banking, fintech, healthtech)."
    ),
    "leadership": (
        "Engineering leader — Head of Data at Makro/CP Group ($8B revenue). Scaled "
        "team 8 → 25, managed $2M+ cloud budget, built Databricks Lakehouse handling "
        "10B+ daily rows at 99.99% uptime. Senior pod + leadership support, 7+ "
        "clouds, regulated-environment work."
    ),
}


# ---- skill re-ranker -----------------------------------------------------

SKILL_RANK_HINTS = {
    "agentic_ai":     ["agent", "LLM", "LangChain", "RAG", "vector", "embedding",
                       "Python", "PyTorch", "OpenAI", "Anthropic", "Kubernetes",
                       "AWS", "Databricks"],
    "llm_ai":         ["LLM", "RAG", "vector", "embedding", "OpenAI", "Anthropic",
                       "PyTorch", "Hugging Face", "transformer", "fine-tun", "Python",
                       "Kubernetes", "AWS", "Databricks"],
    "ml_platform":    ["MLflow", "KServe", "Seldon", "BentoML", "model serving",
                       "feature store", "Databricks", "MLflow", "PyTorch", "Python",
                       "Kubernetes", "AWS"],
    "data_platform":  ["Databricks", "Apache Spark", "Kafka", "Flink", "Airflow",
                       "Delta Lake", "dbt", "Snowflake", "Python", "SQL", "AWS",
                       "Azure", "GCP", "Alibaba Cloud"],
    "cloud_arch":     ["AWS", "Azure", "GCP", "Tencent", "Alibaba", "Huawei",
                       "Terraform", "Kubernetes", "k8s", "EKS", "AKS", "GKE",
                       "Python", "Go"],
    "genai_app":      ["Generative AI", "LLM", "RAG", "NLP", "PyTorch",
                       "TensorFlow", "transformer", "Python", "Databricks"],
    "full_stack":     ["Python", "JavaScript", "TypeScript", "React", "Node.js",
                       "Kubernetes", "AWS", "Databricks", "PySpark"],
    "leadership":     ["Team Scaling", "Budget Management", "C Level Stakeholder",
                       "Vendor Negotiation", "Enterprise Data Strategy",
                       "Databricks", "AWS"],
}


# ---- builder -------------------------------------------------------------

def tailor_resume(lead: dict, out_dir: Optional[Path] = None) -> Optional[Path]:
    """Build a JD-tailored resume for the given lead.

    Returns the path to the tailored docx, or None if python-docx isn't installed.
    """
    if not HAVE_DOCX:
        return None
    out_dir = out_dir or TAILORED_DIR

    families = classify_jd(lead.get("jd_text", ""), lead.get("role", ""))
    primary = families[0] if families else "data_platform"

    base_path = RESUME_DIR / "Pv_Cv_Data_Ai_2026.docx"
    if not base_path.exists():
        base_path = RESUME_DIR / "Prem_Resume_2026.docx"
    if not base_path.exists():
        return None

    doc = Document(str(base_path))

    # 1) Replace the headline (first non-empty paragraph)
    _replace_headline(doc, HEADLINES.get(primary, HEADLINES["data_platform"]))

    # 2) Replace the Professional Summary block
    _replace_summary(doc, SUMMARIES.get(primary, SUMMARIES["data_platform"]))

    # 3) Re-rank skills
    _rerank_skills(doc, SKILL_RANK_HINTS.get(primary, []))

    # 4) Save with tracking-id-based filename
    safe_company = re.sub(r"[^A-Za-z0-9]+", "_", lead.get("company", "lead"))[:30]
    family_slug = primary.replace("_", "-")
    out_path = out_dir / f"{safe_company}_{family_slug}.docx"
    doc.save(str(out_path))
    return out_path


def _replace_headline(doc, new_headline: str):
    """Replace the very first paragraph (the title/headline)."""
    for p in doc.paragraphs:
        if p.text.strip():
            # Clear runs and set new text
            for run in p.runs:
                run.text = ""
            if p.runs:
                p.runs[0].text = new_headline
            else:
                p.add_run(new_headline)
            return


def _replace_summary(doc, new_summary: str):
    """Replace paragraphs inside the PROFESSIONAL SUMMARY section.

    Strategy: find the paragraph that starts with "Professional Summary" and
    collapse the next paragraphs (until KEY SKILLS / EXPERIENCE / EDUCATION
    headers) into a single summary paragraph with the new text.
    """
    paras = doc.paragraphs
    summary_idx = None
    for i, p in enumerate(paras):
        if re.search(r"(PROFESSIONAL\s+SUMMARY|Professional\s+Summary)", p.text, re.I):
            summary_idx = i
            break
    if summary_idx is None:
        return
    # Look ahead up to 8 paragraphs for a section header. We only stop on
    # a line that is SHORT and ALL-CAPS-ish — not a body sentence that
    # happens to contain the word "experience".
    i = summary_idx + 1
    end_idx = None
    while i < len(paras) and i < summary_idx + 8:
        text = paras[i].text.strip()
        # Header-shaped: short, mostly uppercase letters, no period
        if 2 < len(text) < 30 and re.search(r"\b(KEY SKILLS|EXPERIENCE|EDUCATION|CERTIFICATIONS|PROJECTS)\b", text, re.I):
            end_idx = i
            break
        i += 1
    if end_idx is None:
        end_idx = min(summary_idx + 4, len(paras))

    # Collapse paragraphs [summary_idx+1 .. end_idx-1] into one new summary
    # in the first slot; blank the rest.
    first_body_idx = summary_idx + 1
    if first_body_idx >= len(paras):
        return
    target = paras[first_body_idx]
    for run in target.runs:
        run.text = ""
    if target.runs:
        target.runs[0].text = new_summary
    else:
        target.add_run(new_summary)
    for j in range(first_body_idx + 1, end_idx):
        for run in paras[j].runs:
            run.text = ""


def _rerank_skills(doc, priority_keywords: List[str]):
    """In the KEY SKILLS section, prepend JD-matching keywords.

    Strategy: find the KEY SKILLS paragraph; within that paragraph (and the
    next 8-10), find any text matching priority_keywords and bold/uppercase
    them. Simpler: just prefix them in the first skills paragraph.
    if no priority keywords are given, leave as-is.
    """
    if not priority_keywords:
        return
    paras = doc.paragraphs
    skills_idx = None
    for i, p in enumerate(paras):
        if re.search(r"^\s*KEY\s+SKILLS", p.text, re.I):
            skills_idx = i
            break
    if skills_idx is None:
        return
    # Find the first content paragraph after KEY SKILLS, and prepend
    # a "JD-relevant:" highlight line
    if skills_idx + 1 < len(paras):
        first_skills_para = paras[skills_idx + 1]
        # Add a small inline highlight at the start
        existing = first_skills_para.text
        if any(k.lower() in existing.lower() for k in priority_keywords[:5]):
            return  # already mentions them
        prefix = "→ JD-relevant focus: " + ", ".join(priority_keywords[:6]) + "\n"
        for run in first_skills_para.runs:
            run.text = ""
        if first_skills_para.runs:
            first_skills_para.runs[0].text = prefix + existing
        else:
            first_skills_para.add_run(prefix + existing)


def render_to_pdf(docx_path: Path) -> Optional[Path]:
    """Convert docx to PDF using LibreOffice CLI. Returns the PDF path."""
    try:
        out = subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf",
             "--outdir", str(docx_path.parent), str(docx_path)],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode == 0:
            pdf_path = docx_path.with_suffix(".pdf")
            if pdf_path.exists():
                return pdf_path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


# ---- CLI -----------------------------------------------------------------

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--lead-id", type=int, help="Build resume for a specific lead id")
    p.add_argument("--all-pending", action="store_true",
                   help="Build resume for every pending email lead")
    p.add_argument("--preview", action="store_true",
                   help="Print classification + planned headline/summary, don't write file")
    args = p.parse_args()

    if not HAVE_DOCX:
        print("❌ python-docx not installed. Run: pip install python-docx")
        return

    if args.preview:
        sample = {
            "company": "comma.ai",
            "role": "Senior AI Engineer",
            "jd_text": "Production RAG on autonomous driving data, multi-agent systems",
        }
        fams = classify_jd(sample["jd_text"], sample["role"])
        primary = fams[0]
        print(f"Sample JD: {sample['role']} at {sample['company']}")
        print(f"  Families: {fams}")
        print(f"  Primary: {primary}")
        print(f"  Headline: {HEADLINES[primary]}")
        print(f"  Summary:  {SUMMARIES[primary][:200]}...")
        print(f"  Skills:   {SKILL_RANK_HINTS[primary]}")
        return

    from db.lead_store import get_cursor
    with get_cursor() as cur:
        if args.lead_id:
            cur.execute("SELECT id, company, role, jd_text FROM leads WHERE id = %s", (args.lead_id,))
        elif args.all_pending:
            cur.execute("""
                SELECT id, company, role, jd_text FROM leads
                WHERE status = 'pending' AND contact_email IS NOT NULL
                ORDER BY id
            """)
        else:
            print("Specify --lead-id or --all-pending")
            return
        rows = cur.fetchall()
    print(f"📝 Tailoring resumes for {len(rows)} leads")
    for r in rows:
        out = tailor_resume(dict(r))
        if out:
            print(f"  ✅ id={r['id']:3d} {r['company'][:25]:25s} → {out.name}")
        else:
            print(f"  ❌ id={r['id']:3d} {r['company'][:25]:25s} (no base resume found)")


if __name__ == "__main__":
    main()