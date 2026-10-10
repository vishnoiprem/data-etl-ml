#!/usr/bin/env python3
"""
process_jd_inbox.py — parse JD_SETUP_TEXT.md and send all leads found.

Usage:
  python3 process_jd_inbox.py            # process + send
  python3 process_jd_inbox.py --dry      # preview only
  python3 process_jd_inbox.py --list     # show what's in the file

What it does:
  1. Reads JD_SETUP_TEXT.md (the user's free-form paste area)
  2. Splits by '--- START PASTE ---' and '--- END PASTE ---' markers
  3. For each block:
     - Detects if it's a URL, an email-heavy text, a LinkedIn DM, a tweet, etc.
     - Extracts: company, role, contact_email, jd_text, rate, stack
     - If URL but no email: try careers@/jobs@/hiring@/talent@/recruiter@ fallbacks
     - If unknown company: skip with warning
  4. For each extracted lead, generates a tailored Avilx cover letter
  5. Appends to leads.json
  6. Runs auto.py --email to send all pending
"""

import os
import re
import sys
import json
import subprocess
import argparse
import textwrap
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# File paths
HERE = Path(__file__).parent
INBOX = HERE / "JD_SETUP_TEXT.md"
LEADS_FILE = HERE / "leads.json"
LOG_FILE = HERE / "auto_log.csv"

# Load .env
from dotenv import load_dotenv
load_dotenv(HERE / ".env")

YOUR_NAME = os.getenv("YOUR_NAME", "Prem Vishnoi")
YOUR_COMPANY = os.getenv("YOUR_COMPANY", "Avilx")
YOUR_EMAIL = os.getenv("YOUR_EMAIL", "hello@avilx.com")
YOUR_WEBSITE = os.getenv("YOUR_WEBSITE", "https://avilx.com")
YOUR_PHONE = os.getenv("YOUR_PHONE", "")

PERSONAL_SIG = f"""{YOUR_NAME}
{YOUR_COMPANY} — Global Build · Deploy · Engineers (AI · Data · ML · Cloud · Databricks · 7+ clouds)
Delivery: China · APAC · US · EU | HQ: Ha Noi, Vietnam
📧 {YOUR_EMAIL} | 📱 {YOUR_PHONE} | 💬 WhatsApp: wa.me/{os.getenv('YOUR_WHATSAPP','').lstrip('+')} | 🌐 {YOUR_WEBSITE} | 🐦 @vishnoiprem"""


# ============== PARSING ==============

EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
URL_RE = re.compile(r'https?://[^\s\)\]\"\'<>]+')
DOLLAR_RE = re.compile(
    r'(?:[\$£€¥]|SGD|USD|S\$|S\$|AU\$|CA\$|HK\$|NT\$)\s?'
    r'\d{1,3}(?:[,\s]\d{3})*'
    r'(?:\s*[Kk]\b|\s*[Mm]\b)?'
    r'(?:\s*[\-–]\s*'
    r'(?:[\$£€¥]|SGD|USD|S\$)?\s?'
    r'\d{1,3}(?:[,\s]\d{3})*'
    r'(?:\s*[Kk]\b|\s*[Mm]\b)?)?'
    r'(?:\s*/\s*(?:hour|year|month|hr|yr|mo))?',
    re.IGNORECASE,
)
# Phone: international or local, with common separators
PHONE_RE = re.compile(
    r'(?:\+?\d{1,3}[\s\-\.]?)?'                # country code
    r'(?:\(\d{1,4}\)|\d{1,4})'                  # area code
    r'[\s\-\.]?\d{2,4}[\s\-\.]?\d{2,4}[\s\-\.]?\d{0,4}',
    re.UNICODE,
)

# Common false-positive emails to skip
SKIP_EMAILS = {
    "example@example.com", "noreply@", "no-reply@", "donotreply@",
    "privacy@", "support@", "info@", "contact@", "hello@",
}


def is_real_contact_email(email: str) -> bool:
    """Return True if the email looks like a recruiter/hiring contact (not generic)."""
    if not email:
        return False
    e = email.lower()
    for skip in SKIP_EMAILS:
        if skip in e:
            return False
    return True


def extract_emails(text: str) -> list:
    """Extract all emails, prioritizing real-looking contacts over generic ones."""
    all_emails = EMAIL_RE.findall(text)
    real = [e for e in all_emails if is_real_contact_email(e)]
    generic = [e for e in all_emails if e not in real]
    return real + generic  # real first


def extract_url(text: str) -> str | None:
    """Extract the first URL."""
    m = URL_RE.search(text)
    return m.group(0).rstrip('.,;:') if m else None


def extract_phone(text: str) -> str | None:
    """Extract a phone number, preferring ones that look real (have country code or >=10 digits)."""
    candidates = []
    for m in PHONE_RE.finditer(text):
        raw = m.group(0).strip()
        digits = re.sub(r'\D', '', raw)
        if len(digits) < 7 or len(digits) > 15:
            continue
        # Skip if it's actually part of a longer number sequence (rare)
        candidates.append(raw)
    if not candidates:
        return None
    # Prefer numbers with + (country code)
    for c in candidates:
        if c.startswith('+'):
            return c
    return candidates[0]


def extract_company_from_email(email: str) -> str | None:
    """Get the company name guess from an email domain."""
    if not email or "@" not in email:
        return None
    domain = email.split("@")[1].lower()
    # Strip common subdomains
    for prefix in ["careers.", "jobs.", "hiring.", "talent.", "recruit.", "recruiting.", "hr.", "apply."]:
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    # Strip TLD
    base = domain.split(".")[0]
    # Special cases for known brands
    SPECIAL = {
        "singlestore": "SingleStore",
        "single-store": "SingleStore",
        "funnelstory": "FunnelStory",
        "funnel-story": "FunnelStory",
        "k4econsultancy": "K4Econsultancy",
        "agreeya": "AgreeYa",
        "radiantjapan": "Radiant Japan",
        "cis-tec": "CIS-TEC",
        "cistec": "CIS-TEC",
        "stickermule": "Sticker Mule",
        "menrvagroup": "Menrva Group",
        "bytedance": "ByteDance",
        "bytedancewe": "ByteDance",
        "quadranttechnologies": "Quadrant Technologies",
        "avanceservices": "Avance Services",
        "primetechpartners": "Prime Tech Partners",
        "primetechpartnersin": "Prime Tech Partners",
        "jpstechsolutions": "JPS Tech Solutions",
        "kk-talents": "KK Talents",
        "kktalents": "KK Talents",
        "wearehackerone": "HackerOne",
    }
    if base in SPECIAL:
        return SPECIAL[base]
    return base.replace("-", " ").title()


def extract_company_from_url(url: str) -> str | None:
    """Get company name guess from a URL."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        # Strip subdomains
        for prefix in ["www.", "jobs.", "boards.", "careers.", "apply."]:
            if host.startswith(prefix):
                host = host[len(prefix):]
        # Strip paths and TLD
        base = host.split(".")[0]
        if "ashbyhq" in host:
            # jobs.ashbyhq.com/{company} — get from path
            parts = parsed.path.strip("/").split("/")
            if parts:
                return parts[0].replace("-", " ").title()
        if "greenhouse" in host:
            parts = parsed.path.strip("/").split("/")
            for p in parts:
                if p and p not in ("boards", "jobs", "embed"):
                    return p.replace("-", " ").title()
        if "lever" in host:
            parts = parsed.path.strip("/").split("/")
            for p in parts:
                if p and p not in ("jobs", "lever", "embed"):
                    return p.replace("-", " ").title()
        if "workday" in host:
            # workday is harder, just use base
            return base.title()
        if "weworkremotely" in host:
            # weworkremotely.com/remote-jobs/{company}-{role}
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2 and parts[0] == "remote-jobs":
                return parts[1].split("-")[0].title()
        return base.title()
    except Exception:
        return None


def extract_role(text: str) -> str | None:
    """Try to find a role title in the text. Prefers Senior/Staff/Principal when present."""
    # Common role patterns
    role_patterns = [
        # "Hiring: <role>" or "Hiring <role>"
        r'Hiring\s*[:\-]?\s*([A-Z][A-Za-z\/\-\s]{3,60}?)(?:\s*\(|[\n\.]|$)',
        # "Looking for <role>"
        r'Looking\s+for\s+(?:a|an)?\s*([A-Z][A-Za-z\/\-\s]{3,60}?)(?:\s+in\s|\s*\(|[\n\.]|$)',
        # "<role> needed/wanted/hiring"
        r'((?:Senior|Junior|Staff|Principal|Lead|Head\s+of|Director\s+of)\s+[A-Z][A-Za-z\/\-\s]{3,60}?)\s+(?:needed|wanted|hiring|opening|role|position)',
        # "X Engineer - Y yen" or "X Engineer, ..."  (with prefix)
        r'((?:Senior|Junior|Staff|Principal|Lead|Head\s+of|Director\s+of)\s+[A-Z][A-Za-z\/\-]+(?:\s+[A-Z][A-Za-z\/\-]+){0,3}\s+(?:Engineer|Architect|Scientist|Developer|Manager|Analyst|Designer|Consultant))\s*[–\-]',
        # Generic "X Engineer" with caps
        r'((?:Senior|Junior|Staff|Principal|Lead|Head\s+of|Director\s+of)?\s*[A-Z][A-Za-z\/\-]+(?:\s+[A-Z][A-Za-z\/\-]+){0,3}\s+(?:Engineer|Architect|Scientist|Developer|Manager|Analyst|Designer|Consultant))\b',
    ]
    # Prefer Senior/Staff/Principal/Lead over Junior
    preferred_prefixes = ('Senior', 'Staff', 'Principal', 'Lead', 'Head', 'Director')
    found = []
    for pat in role_patterns:
        for m in re.finditer(pat, text, re.MULTILINE):
            role = m.group(1).strip()
            for sep in ['\n', ' at ', ' for ', ' (', ' —', ' -', ' –']:
                if sep in role:
                    role = role.split(sep)[0]
            if 3 < len(role) < 80:
                found.append(role)
    if not found:
        return None
    # Prefer first match that starts with a senior prefix
    for r in found:
        if any(r.startswith(p + ' ') for p in preferred_prefixes):
            return r
    return found[0]


def extract_rate(text: str) -> str | None:
    """Try to find salary/rate info. Skips funding/valuation lines."""
    funding_keywords = re.compile(
        r'\b(raised|funding|valuation|series [a-f]|seed round|backed by)\b',
        re.IGNORECASE,
    )
    candidates = []
    for line in text.split('\n'):
        if funding_keywords.search(line):
            continue
        m = DOLLAR_RE.search(line)
        if m:
            candidates.append(m.group(0))
    if candidates:
        return candidates[0]
    return None


def guess_email_for_company(company: str) -> str | None:
    """Generate best-guess generic email for a company domain."""
    # Common patterns: careers@, jobs@, hiring@, talent@, recruiter@
    # We just return the first one; sender will try them
    base = re.sub(r'[^a-z]', '', company.lower())
    return f"careers@{base}.com"


def parse_block(block: str) -> dict | None:
    """Parse a single free-form block into a structured lead."""
    if not block.strip():
        return None
    if len(block.strip()) < 20:
        return None

    block = block.strip()

    # Extract signals
    emails = extract_emails(block)
    url = extract_url(block)
    role = extract_role(block)
    rate = extract_rate(block)
    phone = extract_phone(block)

    # Determine company
    company = None
    if emails:
        company = extract_company_from_email(emails[0])
    if not company and url:
        company = extract_company_from_url(url)
    if not company:
        # Try to find a "Company Name" or "@handle" pattern (single line only)
        m = re.search(r'@([A-Za-z][A-Za-z0-9\-]+)', block)
        if m:
            company = m.group(1).title()
        if not company:
            # Limit to single line — multi-line greedy matches can grab junk
            for line in block.split('\n')[:5]:  # only first 5 lines (header area)
                m = re.search(r'(?:at|@|for|with)\s+([A-Z][A-Za-z0-9\-]+(?:\s+[A-Z][A-Za-z0-9\-]+)?)', line)
                if m:
                    company = m.group(1)
                    break

    if not company:
        return {
            "error": "couldn't identify company",
            "raw": block[:300]
        }

    # Pick best email
    contact_email = emails[0] if emails else None
    if not contact_email:
        contact_email = guess_email_for_company(company)

    # JD text = the block itself (or cleaned)
    jd_text = block

    # Resume guess: principal for staff/principal/head, senior for mid
    role_lower = (role or "").lower()
    if any(kw in role_lower for kw in ["staff", "principal", "head", "director", "architect", "vp", "chief"]):
        resume = "PREM_2026.pdf"
    else:
        resume = "Prem_Resume_2026.pdf"

    return {
        "company": company,
        "role": role or "Role TBD",
        "contact_email": contact_email,
        "contact_phone": phone or "",
        "apply_method": "email",
        "resume_file": resume,
        "rate": rate or "Not listed",
        "jd_text": jd_text,
        "source_url": url or "",
    }


def read_inbox() -> list[str]:
    """Read JD_SETUP_TEXT.md and return all blocks between the START/END markers.

    Always runs through _split_into_posts (smart post-boundary detector) so we
    don't accidentally break a long post into fragments at blank lines.
    """
    if not INBOX.exists():
        return []
    text = INBOX.read_text()
    if "--- START PASTE ---" not in text:
        # No markers, treat whole file as one blob and split on post boundaries
        return _split_into_posts(text)
    parts = text.split("--- START PASTE ---", 1)
    if len(parts) < 2:
        return []
    after = parts[1]
    if "--- END PASTE ---" in after:
        after = after.split("--- END PASTE ---", 1)[0]
    after = after.strip()
    if not after:
        return []
    # Run the smart post-splitter — it correctly keeps one long post together
    # even when the post has multiple paragraphs separated by blank lines.
    return _split_into_posts(after)


def _split_into_posts(text: str) -> list[str]:
    """Split a blob of recruiter posts (no markers) on natural post boundaries.

    Conservative splitter: only splits on very obvious signals so we don't break
    long posts into fragments.

    Heuristics (in priority order):
      1. *** <text> *** inline star separator  (very strong)
      2. *** bare star line (acts as separator between two posts)
      3. "Hiring:" or "Looking for" line at the start of a paragraph (when
         this looks like a fresh post — e.g. the previous post already had
         contact info, or we're at the top of the file)
    Each new post starts with one of these patterns.
    """
    # Inline star separator: a line that's mostly stars with text inside
    # e.g.  *** Staff ML Engineer — Generative AI (Series B...) ***
    star_inline_re = re.compile(r'^\s*\*+[^*]*\*+\s*$', re.MULTILINE)
    # Bare star line (just stars, no text)
    star_bare_re = re.compile(r'^\s*\*+\s*$', re.MULTILINE)
    # Post header at start of a line. Be permissive: allow leading emoji,
    # "Hiring:" / "Looking for" / "Role:-" / "Role:" / "JOB ALERT" / etc.
    header_re = re.compile(
        r'^\s*'                                  # leading whitespace
        r'(?:[\U0001F300-\U0001FAFF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\u2700-\u27BF\u2600-\u26FF\u2700-\u27BF\u2300-\u23FF\u2B50\u2728\U0001F4CC\U0001F4CD\U0001F4CE\U0001F4A1\u2705\u2728\U0001F44D\u26A1\U0001F525\U0001F680\u2B06\u2B07\u2B05\u2B95\u2934\u2935\u2192\u2193\u2190\u2191\u2B05\u2B06\u2B07\u2192\u2190\u2191\u2193\u2934\u2935]\s*)*'  # leading emojis
        r'(?:'
        r'Hiring\s*:|'
        r'Looking\s+for|'
        r'Role\s*[:-]|'
        r'JOB\s+ALERT|'
        r'We[\'\u2019]?re\s+(?:Hiring|looking)|'
        r'(?:Senior|Junior|Staff|Principal|Lead|Head\s+of|Director\s+of)?\s*'
        r'[A-Z][A-Za-z\-/]+(?:\s+[A-Z][A-Za-z\-/]+){0,3}\s+'
        r'(?:Engineer|Architect|Scientist|Developer|Manager|Analyst|Designer|Consultant)\b'
        r'(?:\s*[—\-:].*)?'
        r')',
        re.UNICODE,
    )

    # Walk through lines and rebuild into blocks
    lines = text.split('\n')
    blocks = []
    current = []
    seen_email_in_current = False  # tracks if current block already has a contact

    def is_strong_boundary(stripped: str) -> bool:
        """True if this line is unambiguous post boundary (with role text inside)."""
        if star_inline_re.match(stripped):
            return True
        return False

    def is_soft_header(stripped: str) -> bool:
        """True if this looks like a new post header (Hiring:/Looking for/etc)."""
        if not stripped or len(stripped) > 200:
            return False
        if header_re.match(stripped):
            return True
        return False

    for line in lines:
        stripped = line.strip()
        # Strong boundary: split, but preserve the text inside the stars
        # (the role/title often lives inside the ***...***)
        if is_strong_boundary(stripped):
            if current:
                blocks.append('\n'.join(current).strip())
                current = []
                seen_email_in_current = False
            # Strip the stars but keep the inner text as the new block's start
            inner = re.sub(r'^\s*\*+\s*', '', stripped)
            inner = re.sub(r'\s*\*+\s*$', '', inner).strip()
            if inner:
                current = [inner]
            continue
        # Soft header: always split (the previous post is implicitly complete
        # because we're seeing a new post header). This handles the case of
        # short first posts that don't have their own separator.
        if is_soft_header(stripped) and current:
            blocks.append('\n'.join(current).strip())
            current = [line]
            seen_email_in_current = False
            continue
        # Bare star lines: split if current has email (means previous post is complete)
        if star_bare_re.match(stripped) and current and seen_email_in_current:
            blocks.append('\n'.join(current).strip())
            current = []
            seen_email_in_current = False
            continue
        current.append(line)
        if re.search(r'@', stripped):
            seen_email_in_current = True

    if current:
        blocks.append('\n'.join(current).strip())

    # Merge any block without contact email with the NEXT block (it's a header fragment
    # or a partial post). We do this iteratively from the start.
    merged = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        email_re = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
        if not email_re.search(b) and i + 1 < len(blocks):
            merged.append(b + "\n\n" + blocks[i + 1])
            i += 2
        else:
            merged.append(b)
            i += 1

    return [b for b in merged if b and len(b) > 20]


def generate_cover_letter(lead: dict) -> tuple[str, str]:
    """Generate (subject, body) for a parsed lead."""
    company = lead["company"]
    role = lead["role"]
    jd = lead.get("jd_text", "")
    rate = lead.get("rate", "")

    # Pull 1-2 must-haves from JD if we can find any
    must_haves = []
    for line in jd.split("\n"):
        line = line.strip()
        if line.startswith(("-", "•", "*", "✅", "🔹")) and len(line) > 10 and len(line) < 200:
            must_haves.append(line.lstrip("-•*✅🔹 ").strip())
        if len(must_haves) >= 2:
            break

    must_have_text = ""
    if must_haves:
        must_have_text = f" Specifically caught my eye: {'; '.join(must_haves[:2])}."

    # Pull stack from JD
    stack_keywords = ["Python", "TypeScript", "Go", "Rust", "Java", "Kubernetes", "Kafka", "Spark",
                      "Databricks", "Snowflake", "dbt", "LangChain", "LangGraph", "RAG", "agents",
                      "AWS", "Azure", "GCP", "Tencent", "Alibaba", "React", "Node", "FastAPI"]
    stack_found = [k for k in stack_keywords if k.lower() in jd.lower()][:4]
    stack_text = ", ".join(stack_found) if stack_found else "modern data/AI/cloud"

    # Contact name guess from email or signature
    email = lead.get("contact_email", "")
    first_name = "there"
    if email and "@" in email:
        local = email.split("@")[0]
        # Common patterns: firstname.lastname, firstnamelastname, fmlastname
        # Detect via multi-letter split heuristics
        # Skip if local is clearly not a name (e.g., "careers", "hiring", "info")
        if local.lower() in ("careers", "jobs", "hiring", "talent", "recruiter", "hr", "info",
                              "hello", "contact", "apply", "noreply", "support", "admin"):
            first_name = "there"
        else:
            for sep in [".", "_", "-"]:
                if sep in local:
                    parts = local.split(sep)
                    # firstname.lastname → first name is the first part
                    if len(parts[0]) >= 2:
                        first_name = parts[0].capitalize()
                    break
            if first_name == "there":
                # Try to detect "fmlastname" pattern (e.g., wdenholm = w denholm? unlikely)
                # or just use localpart capitalized
                first_name = local.capitalize() if len(local) >= 3 else "there"

    subject = f"Avilx — {role} for {company} (global delivery, 7+ clouds, Databricks Champion)"

    body = f"""Hi {first_name} —

{('Saw the ' + role + ' role at ' + company + '.') if 'role' in lead else ('Got your message about ' + company + '.')} Avilx (avilx.com) is a global Build·Deploy·Engineers partner — Databricks Champion team, 15+ yrs across 7+ clouds (AWS · Azure · GCP · Tencent · Alibaba), senior-only vetted engineers (8+ yrs, no recruiters).{must_have_text}

Two angles: (1) I'm personally interested in the role — I've shipped {stack_text} at production scale. (2) Avilx can run a senior build pod (4-6 engineers, $40-70/hr blended) or staff aug ($50-100/hr) or principal architect seat ($120-180/hr) if {company} needs scale-up alongside this hire. Global delivery to China + APAC + US + EU, USD/EUR/CNY/SGD invoicing, Vietnam LLC, NDA + IP standard.

Happy to share my resume (attached) and 1-2 relevant case studies on a 15-min call this week. WhatsApp me at wa.me/{os.getenv('YOUR_WHATSAPP','').lstrip('+')} or drop a time: hello@avilx.com

{PERSONAL_SIG}"""

    return subject, body


def load_leads() -> list:
    with open(LEADS_FILE) as f:
        return json.load(f)


def save_leads(leads: list):
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2)


def merge_lead(parsed: dict) -> bool:
    """Merge a parsed lead into leads.json (and Postgres). Returns True if added, False if duplicate."""
    leads = load_leads()
    # Check for duplicate by (company, role) or (company, contact_email)
    for existing in leads:
        if (existing.get("company", "").lower() == parsed["company"].lower()
                and existing.get("role", "").lower() == parsed["role"].lower()):
            return False
        if (existing.get("contact_email") == parsed["contact_email"]
                and parsed["contact_email"]
                and parsed["contact_email"] != "careers@" + parsed["company"].lower().replace(" ", "") + ".com"):
            return False

    # Also check Postgres for dedup (works across machines, persistent)
    try:
        from db.lead_store import find_duplicate as _pg_dup
        dup = _pg_dup(parsed["company"], parsed.get("contact_email", ""), parsed.get("role", ""))
        if dup:
            return False
    except Exception as e:
        # If DB is down, fall back to file-based dedup (already done above)
        pass

    subject, body = generate_cover_letter(parsed)

    new_lead = {
        "company": parsed["company"],
        "role": parsed["role"],
        "rate": parsed.get("rate", "Not listed"),
        "stack": parsed.get("stack", "TBD"),
        "remote": parsed.get("remote", "TBD"),
        "url": parsed.get("source_url", ""),
        "contact_email": parsed.get("contact_email"),
        "contact_phone": parsed.get("contact_phone", ""),
        "apply_method": "email",
        "cover_letter_subject": subject,
        "cover_letter_body": body,
        "resume_file": parsed.get("resume_file", "PREM_2026.pdf"),
        "status": "pending",
    }

    leads.insert(0, new_lead)  # put at top so it gets processed first
    save_leads(leads)

    # Mirror to Postgres for cross-machine dedup + tracking
    try:
        from db.lead_store import insert_lead as _pg_insert
        pg_id = _pg_insert(new_lead, source="jd_inbox")
        new_lead["_pg_id"] = pg_id
    except Exception as e:
        print(f"   ⚠️  Postgres insert failed: {e}")

    return True


def log_send(company: str, email: str, status: str, error: str = ""):
    """Append to auto_log.csv."""
    file_exists = LOG_FILE.exists()
    with open(LOG_FILE, "a") as f:
        if not file_exists:
            f.write("timestamp,action,company,target,status,error\n")
        ts = datetime.now().isoformat()
        f.write(f"{ts},email,{company},{email},{status},{error}\n")


def render_preview(lead: dict) -> str:
    """Render a nice boxed preview of the cover letter for terminal display."""
    subject, body = generate_cover_letter(lead)
    company = lead.get("company", "?")
    role = lead.get("role", "?")
    to = lead.get("contact_email", "?")
    rate = lead.get("rate", "Not listed")
    url = lead.get("source_url", "")
    width = 78
    sep = "═" * width
    sub = "─" * width

    lines = []
    lines.append(sep)
    lines.append(f"  #{lead.get('_idx', '?')}  {company}  •  {role}".ljust(width))
    lines.append(sub)
    lines.append(f"  TO:      {to}".ljust(width))
    lines.append(f"  RATE:    {rate}".ljust(width))
    if url:
        lines.append(f"  URL:     {url}".ljust(width))
    lines.append(f"  RESUME:  {lead.get('resume_file', 'Prem_Resume_2026.pdf')}".ljust(width))
    lines.append(sub)
    lines.append(f"  SUBJECT: {subject}".ljust(width))
    lines.append(sub)
    # Word-wrap the body to width-2
    for paragraph in body.split("\n\n"):
        wrapped = textwrap.wrap(paragraph.strip(), width=width - 2) or [""]
        for w in wrapped:
            lines.append(f"  {w}".ljust(width))
        lines.append("")  # blank line between paragraphs
    lines.append(sep)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true", help="Preview only, don't send")
    parser.add_argument("--list", action="store_true", help="Just list parsed leads")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt before sending")
    args = parser.parse_args()

    blocks = read_inbox()
    print(f"📥 Found {len(blocks)} block(s) in JD_SETUP_TEXT.md\n")

    parsed_leads = []
    errors = []
    for i, block in enumerate(blocks, 1):
        result = parse_block(block)
        if not result:
            continue
        if "error" in result:
            errors.append(result)
            print(f"  ❌ Block {i}: {result['error']}")
            print(f"     Raw: {result['raw'][:80]}...")
            continue
        result["_idx"] = i
        parsed_leads.append(result)
        print(f"  ✅ Block {i}: {result['company']} — {result['role']} → {result['contact_email']}")

    if errors:
        print(f"\n⚠️  {len(errors)} block(s) couldn't be parsed. Add more context (company name, role, contact) and try again.")

    if args.list:
        return

    if not parsed_leads:
        print("\nNothing to send.")
        return

    # Show the cover-letter preview for every parsed lead
    print(f"\n{'=' * 80}")
    print(f"  📬  COVER LETTER PREVIEW — {len(parsed_leads)} email(s)")
    print(f"{'=' * 80}\n")
    for lead in parsed_leads:
        print(render_preview(lead))
        print()

    if args.dry:
        print("🔵 DRY RUN — not merging or sending. Run without --dry to fire.")
        return

    print(f"\n📝 Merging {len(parsed_leads)} lead(s) into leads.json...")
    added = 0
    for p in parsed_leads:
        if merge_lead(p):
            added += 1
    print(f"   Added: {added}, duplicates skipped: {len(parsed_leads) - added}")

    if added == 0:
        print("\nNo new leads to send (all duplicates).")
        return

    if not args.yes:
        try:
            ans = input(f"\n🚀 Fire {added} email(s) now? [Y/n] ").strip().lower()
        except EOFError:
            ans = "y"
        if ans and ans not in ("y", "yes"):
            print("❌ Cancelled. Leads are saved to leads.json with status=pending.")
            print("   Run `python3 auto.py --email` later to send.")
            return

    print(f"\n📧 Firing pending emails via auto.py --email...")
    result = subprocess.run(
        [sys.executable, str(HERE / "auto.py"), "--email"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        return

    # Clear the paste area so the same blocks don't re-send next time
    text = INBOX.read_text()
    if "--- START PASTE ---" in text and "--- END PASTE ---" in text:
        # Replace the content between markers with empty
        import re as re2
        cleared = re2.sub(
            r'(--- START PASTE ---)(.*?)(--- END PASTE ---)',
            r'\1\n\n\n\n\n--- END PASTE ---',
            text, flags=re2.DOTALL
        )
        INBOX.write_text(cleared)
        print("\n🧹 Cleared paste area in JD_SETUP_TEXT.md")


if __name__ == "__main__":
    main()
