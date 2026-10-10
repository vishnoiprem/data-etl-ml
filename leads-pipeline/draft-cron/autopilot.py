#!/usr/bin/env python3
"""
autopilot.py — Fully autonomous daily lead engine.

Runs the full pipeline end-to-end with zero human input:

  1. SCRAPE   — Pull last-24h AI/ML/Data job postings from public sources
                 that DO expose contact emails (HN Who's Hiring, ai-jobs.net,
                 WeWorkRemotely, company career pages).
  2. ENRICH   — For URL-only leads, probe the company domain for a contact
                 email on /careers, /contact, /about, /team pages.
  3. DEDUP    — Cross-check vs Postgres (email + company + URL).
  4. QUEUE    — Insert net-new leads with a personalised Avilx cover letter
                 rendered from a template.
  5. EMAIL    — Send up to DAILY_LIMIT emails with a per-lead delay.
  6. REPORT   — Print what happened, mirror to send_log.

Usage:
  python3 autopilot.py                 # full daily run
  python3 autopilot.py --scrape        # scrape + queue only (no email)
  python3 autopilot.py --enrich        # enrich URL-only leads only
  python3 autopilot.py --email         # send queued emails only
  python3 autopilot.py --dry           # preview, no writes, no sends
  python3 autopilot.py --max-emails 5  # cap emails this run

Environment:
  All SMTP / Postgres / .env config comes from .env (same as auto.py).

Cron-ready:
  0 9 * * * /usr/bin/python3 /path/autopilot.py >> /tmp/autopilot.log 2>&1
"""

import os
import re
import sys
import json
import time
import socket
import smtplib
import ssl
import argparse
import subprocess
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from db.cron_lock import cron_lock

# --- env / config ---
load_dotenv(HERE / ".env")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USERNAME", os.getenv("GMAIL_ADDRESS", ""))
SMTP_PASS = os.getenv("SMTP_PASSWORD", os.getenv("GMAIL_APP_PASSWORD", "")).replace(" ", "")
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
YOUR_NAME = os.getenv("YOUR_NAME", "Prem Vishnoi")
YOUR_COMPANY = os.getenv("YOUR_COMPANY", "Avilx")
YOUR_EMAIL = os.getenv("YOUR_EMAIL", "hello@avilx.com")
YOUR_PHONE = os.getenv("YOUR_PHONE", "")
YOUR_WHATSAPP = os.getenv("YOUR_WHATSAPP", "")
YOUR_WEBSITE = os.getenv("YOUR_WEBSITE", "https://avilx.com")
RESUME_DIR = Path(os.getenv("RESUME_DIR", str(Path.home() / "Documents" / "Resumes")))
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "20"))
DELAY_BETWEEN_EMAILS_SEC = int(os.getenv("DELAY_BETWEEN_EMAILS_SEC", "90"))
LOG_FILE = HERE / "autopilot.log.jsonl"
REPORT_FILE = HERE / "autopilot_report.json"

# --- keywords that scream "we need senior eng NOW" ---
SCRAPE_KEYWORDS = [
    "AI engineer", "ML engineer", "machine learning engineer",
    "LLM engineer", "RAG engineer", "GenAI engineer", "Generative AI engineer",
    "AI agent engineer", "agentic AI", "AI platform engineer",
    "data platform engineer", "Databricks engineer", "MLOps engineer",
    "AI solutions architect", "ML infrastructure",
    "AI architect", "senior AI", "staff ML", "principal AI",
]

LOCATION_KEYWORDS_REMOTE = [
    "remote", "worldwide", "anywhere", "global", "work from home",
    "distributed", "async", "wfh",
]

EXCLUDE_TITLE = re.compile(
    r"\b(intern|junior|entry[- ]level|graduate|new grad|"
    r"data entry|data annotator|prompt engineer)\b",
    re.I,
)

PERSONAL_SIG = (
    f"{YOUR_NAME}\n"
    f"{YOUR_COMPANY} — Global Build · Deploy · Engineers\n"
    f"(AI · Data · ML · Cloud · Databricks · 7+ clouds)\n"
    f"Delivery: China · APAC · US · EU | HQ: Ha Noi, Vietnam\n"
    f"📧 {YOUR_EMAIL} | 💬 wa.me/{YOUR_WHATSAPP.lstrip('+')} | 🌐 {YOUR_WEBSITE}"
)


# =============================================================
# 1. SCRAPE — public sources that expose emails
# =============================================================

def _curl(url, timeout=12, max_retries=2):
    """Return (status_code, html_text) with per-call tempfile + 429 backoff.

    Per-call tempfile avoids the race that the old shared /tmp/_scrape.html had
    when scrapers run in parallel. 429 handling is essential — cron jobs that
    hammer a rate-limited endpoint will get silently zero-result runs without it.
    """
    import tempfile
    backoff = 1.0
    for attempt in range(max_retries + 1):
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".html", delete=False
            ) as tmp:
                tmp_path = tmp.name
            try:
                out = subprocess.run(
                    ["curl", "-sL", "-m", str(timeout),
                     "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) "
                           "AppleWebKit/537.36 Chrome/129.0 Safari/537.36",
                     "-o", tmp_path, "-w", "%{http_code}", url],
                    capture_output=True, text=True,
                    timeout=timeout + 5,
                )
                code = int((out.stdout or "0").strip() or 0)
                if code == 429 and attempt < max_retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                with open(tmp_path, "rb") as f:
                    html = f.read().decode("utf-8", errors="ignore")
                return code, html
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        except Exception:
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            return 0, ""
    return 0, ""


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IGNORE_EMAIL = re.compile(
    r"(example\.com|your@|sentry|wixpress|cloudflare|googleapis|gstatic|"
    r"w3\.org|schema\.org|noreply|no-reply|donotreply|mailer-daemon|"
    r"@2x\.png|@1x\.png|\.png$|\.jpg$|\.svg$|licdn\.com|"
    r"schemaorg|placeholder|@avatar)",
    re.I,
)


def looks_like_contact_email(addr):
    """Filter obvious noise: noreply, image refs, schema.org, etc."""
    if IGNORE_EMAIL.search(addr):
        return False
    # Common ATS no-reply prefixes
    local = addr.split("@", 1)[0].lower()
    if local in ("noreply", "no-reply", "donotreply", "mailer-daemon", "postmaster"):
        return False
    return True


def _extract_real_emails(html):
    """Return list of real-looking email addresses (deduped, lowercase)."""
    found = set()
    for m in EMAIL_RE.findall(html):
        a = m.lower()
        if looks_like_contact_email(a):
            found.add(a)
    return sorted(found)


def scrape_hn_who_is_hiring():
    """Hacker News 'Ask HN: Who is hiring?' — most recent thread.

    These posts almost always include a direct contact email or careers URL
    inside the post body. We fetch the thread index and walk each comment.
    """
    leads = []
    # The Algolia HN search API
    api = (
        "https://hn.algolia.com/api/v1/search?query=ask+hn+who+is+hiring"
        "&tags=story&hitsPerPage=5"
    )
    code, html = _curl(api)
    if code != 200 or not html:
        return leads
    try:
        data = json.loads(html)
    except Exception:
        return leads
    for hit in data.get("hits", []):
        thread_id = hit.get("objectID")
        if not thread_id:
            continue
        # Load all comments
        items_url = f"https://hn.algolia.com/api/v1/items/{thread_id}"
        code2, html2 = _curl(items_url, timeout=20)
        if code2 != 200 or not html2:
            continue
        try:
            tree = json.loads(html2)
        except Exception:
            continue
        for node in _walk_hn_tree(tree):
            text = node.get("text", "") or ""
            if not text:
                continue
            lower = text.lower()
            if not any(kw.lower() in lower for kw in SCRAPE_KEYWORDS):
                continue
            if EXCLUDE_TITLE.search(text):
                continue
            emails = _extract_real_emails(text)
            # Pull external URL from text
            urls = re.findall(r"https?://[^\s)\"']+", text)
            urls = [u.rstrip(".,;:") for u in urls if "news.ycombinator.com" not in u]
            if not emails and not urls:
                continue
            # Try to find a company name (first quoted phrase or first capitalized line)
            company = _guess_company_from_hn_comment(text)
            role = _guess_role_from_hn_comment(text)
            leads.append({
                "company": company or "Unknown (HN)",
                "role": role or "AI/ML engineer (see comment)",
                "source": f"HN Who's Hiring {thread_id}",
                "source_url": f"https://news.ycombinator.com/item?id={node.get('id','')}",
                "contact_email": emails[0] if emails else None,
                "extra_emails": emails[1:5],
                "extra_urls": urls[:3],
                "raw_excerpt": text[:400],
            })
    return leads


def _walk_hn_tree(node):
    """Yield every comment in an HN thread tree."""
    yield node
    for child in node.get("children") or []:
        yield from _walk_hn_tree(child)


def _guess_company_from_hn_comment(text):
    """Best-effort: HN format is 'Role | Company | Location | ...'."""
    # Format: "Role | Company | Location | ...
    parts = [p.strip() for p in text.split("|")]
    # Company is usually the 2nd non-empty, non-keyword part
    if len(parts) >= 2:
        candidate = parts[1]
        if candidate and not re.search(
            r"remote|onsite|hybrid|full[- ]time|part[- ]time|contract|"
            r"\$|usd|eur|gbp|apac|us|eu|china|singapore|london|nyc|"
            r"san francisco|bay area|berlin|seoul|tokyo|toronto|"
            r"anywhere|worldwide|wfh|distributed",
            candidate, re.I,
        ):
            return candidate[:60]
    # Format: "CompanyName (YC W25) is hiring..."
    m = re.search(r"^([A-Z][A-Za-z0-9&'.\- ]{1,40})\s*\((?:YC|W)\d+\)", text, re.M)
    if m:
        return m.group(1).strip()
    # Fallback: first non-empty line
    first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    return first_line[:60] if first_line else None


def _guess_role_from_hn_comment(text):
    """Pick the most 'role-like' pipe segment (contains 'engineer', 'developer', etc)."""
    parts = [p.strip() for p in text.split("|")]
    role_keywords = re.compile(
        r"\b(engineer|developer|architect|scientist|researcher|"
        r"designer|manager|lead|analyst|admin|writer|designer)\b",
        re.I,
    )
    location_keywords = re.compile(
        r"\b(remote|onsite|hybrid|anywhere|worldwide|wfh|distributed)\b|"
        r",\s*[A-Z][a-z]+(,)?(\s+[A-Z][a-z]+)*\b|"
        r"\b(sf|nyc|us|eu|uk|apac|china|sg|hk|jp|kr|de|fr|es|it|br|"
        r"canada|india|israel|australia|germany|spain|france|italy|"
        r"brazil|mexico|argentina|ireland|netherlands|sweden|finland|"
        r"poland|czech|denmark|norway|switzerland|austria|portugal|"
        r"belgium|austria|turkey|saudi|uae|qatar|egypt|nigeria|"
        r"kenya|south africa|philippines|indonesia|thailand|vietnam|"
        r"malaysia|singapore|taiwan|japan|korea|hong kong)\b",
        re.I,
    )
    for p in parts:
        p = p.splitlines()[0].strip()
        if role_keywords.search(p) and not location_keywords.search(p) and len(p) > 4:
            return p[:100]
    # Fallback to first non-empty part
    for p in parts:
        p = p.splitlines()[0].strip()
        if p and not location_keywords.search(p):
            return p[:100]
    return None


def scrape_weworkremotely():
    """WWR categories feed — many posts include an apply email in description."""
    leads = []
    feeds = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    ]
    for feed_url in feeds:
        code, xml = _curl(feed_url, timeout=20)
        if code != 200 or not xml:
            continue
        # Parse RSS items
        items = re.findall(r"<item>(.*?)</item>", xml, re.S)
        for item in items:
            title_m = re.search(r"<title>(.*?)</title>", item, re.S)
            link_m = re.search(r"<link>(.*?)</link>", item)
            desc_m = re.search(r"<description>(.*?)</description>", item, re.S)
            if not (title_m and link_m and desc_m):
                continue
            title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
            link = link_m.group(1).strip()
            desc = re.sub(r"<[^>]+>", " ", desc_m.group(1))
            desc = re.sub(r"\s+", " ", desc).strip()
            lower = (title + " " + desc).lower()
            if not any(kw.lower() in lower for kw in SCRAPE_KEYWORDS):
                continue
            if EXCLUDE_TITLE.search(title + " " + desc):
                continue
            emails = _extract_real_emails(desc)
            # Extract company from "Company: ..."
            comp_m = re.search(r"<company>(.*?)</company>", item, re.S)
            company = (comp_m.group(1).strip() if comp_m
                       else title.split(" - ")[0].strip() if " - " in title
                       else title.split(":")[0].strip())
            leads.append({
                "company": company,
                "role": title,
                "source": "weworkremotely",
                "source_url": link,
                "contact_email": emails[0] if emails else None,
                "extra_emails": emails[1:5],
                "raw_excerpt": desc[:400],
            })
    return leads


def scrape_ai_jobs_net():
    """ai-jobs.net — public job board with emails in descriptions."""
    leads = []
    # Search the public feed
    urls = [
        "https://ai-jobs.net/?feed=job_feed&search=remote+ai+engineer",
        "https://ai-jobs.net/?feed=job_feed",
    ]
    for url in urls:
        code, xml = _curl(url, timeout=20)
        if code != 200 or not xml:
            continue
        items = re.findall(r"<item>(.*?)</item>", xml, re.S)
        for item in items[:50]:  # cap per feed
            title_m = re.search(r"<title>(.*?)</title>", item, re.S)
            link_m = re.search(r"<link>(.*?)</link>", item)
            desc_m = re.search(r"<description>(.*?)</description>", item, re.S)
            if not (title_m and link_m and desc_m):
                continue
            title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
            link = link_m.group(1).strip()
            desc = re.sub(r"<[^>]+>", " ", desc_m.group(1))
            desc = re.sub(r"\s+", " ", desc).strip()
            lower = (title + " " + desc).lower()
            if not any(kw.lower() in lower for kw in SCRAPE_KEYWORDS):
                continue
            if EXCLUDE_TITLE.search(title + " " + desc):
                continue
            emails = _extract_real_emails(desc)
            # company from <ai:company> or parse title
            comp_m = re.search(r'<ai:company>(.*?)</ai:company>', item, re.S)
            company = (comp_m.group(1).strip() if comp_m
                       else re.split(r" - | at ", title, 1)[0].strip())
            leads.append({
                "company": company,
                "role": title,
                "source": "ai-jobs.net",
                "source_url": link,
                "contact_email": emails[0] if emails else None,
                "extra_emails": emails[1:5],
                "raw_excerpt": desc[:400],
            })
    return leads


def scrape_reddit_ml_jobs():
    """Reddit r/forhire, r/jobbit, r/MachineLearning, r/RemoteJobs, etc.

    Reddit's .json / .rss endpoints are now blocked without auth. So we
    hit Bing's public RSS search (no auth) for site:reddit.com queries
    in the job-hire subs. Each result is a real post with a permalink
    we can revisit.
    """
    leads = []
    # Bing query: site:reddit.com restricted to hiring subs, with AI/ML keywords
    queries = [
        ('site:reddit.com/r/forhire (hiring OR "we are hiring") '
         '(AI OR ML OR "data engineer" OR "LLM" OR "data scientist")'),
        ('site:reddit.com/r/jobbit (hiring OR "we are hiring") '
         '(AI OR ML OR "data engineer" OR "LLM" OR "data scientist")'),
        ('site:reddit.com/r/MachineLearning (hiring OR "we are hiring") '
         '(AI OR ML OR "data engineer" OR "LLM" OR "data scientist")'),
        ('site:reddit.com/r/RemoteJobs (hiring OR "we are hiring") '
         '(AI OR ML OR "data engineer" OR "LLM" OR "data scientist")'),
        ('site:reddit.com/r/dataengineering (hiring OR "we are hiring")'),
    ]
    for q in queries:
        url = "https://www.bing.com/search?" + urllib.parse.urlencode(
            {"q": q, "format": "rss", "count": "30"}
        )
        code, xml = _curl(url, timeout=15)
        if code != 200 or not xml or "<rss" not in xml[:200].lower():
            continue
        for item in re.findall(r"<item>(.*?)</item>", xml, re.S):
            title_m = re.search(r"<title>(.*?)</title>", item, re.S)
            link_m = re.search(r"<link>(.*?)</link>", item)
            desc_m = re.search(r"<description>(.*?)</description>", item, re.S)
            if not (title_m and link_m):
                continue
            title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
            desc = re.sub(r"<[^>]+>", " ", desc_m.group(1)) if desc_m else ""
            desc = re.sub(r"&[a-z]+;", " ", desc)
            desc = re.sub(r"\s+", " ", desc).strip()
            text = f"{title}\n{desc}"
            if EXCLUDE_TITLE.search(text):
                continue
            # Must actually mention our keyword set
            if not any(kw.lower() in text.lower() for kw in SCRAPE_KEYWORDS):
                continue
            # Filter FAQ/meta posts
            if re.search(r"\b(FAQ|meta|thread|announcement)\b", text, re.I):
                continue
            emails = _extract_real_emails(text)
            # Reddit permalink sometimes is missing - construct a fallback
            url_link = link_m.group(1).strip()
            if "reddit.com" not in url_link:
                continue
            # Try to extract company from the title
            company = None
            m = re.search(r"(?:at|@|for)\s+([A-Z][\w&'.\- ]{1,40})(?:\s+|,|\.|\|)",
                          title)
            if m:
                company = m.group(1).strip().rstrip("—-–")
            if not company:
                m = re.search(r"\[(?:Hiring|Hire)\]\s*(.*?)(?:\s*[\|\-—–]|\s*$)",
                              title)
                if m:
                    company = m.group(1).strip()[:60]
            if not company:
                # Pull subreddit from URL
                sm = re.search(r"reddit\.com/r/(\w+)/", url_link)
                company = f"r/{sm.group(1)}" if sm else "reddit"
            leads.append({
                "company": company,
                "role": title[:120],
                "source": f"reddit (via bing)",
                "source_url": url_link,
                "contact_email": emails[0] if emails else None,
                "extra_emails": emails[1:5],
                "raw_excerpt": desc[:400] or title[:400],
            })
    return leads


def scrape_twitter_x_jobs():
    """X/Twitter 'hiring' / 'we are hiring' posts.

    Uses the public syndication API at tweet-url.json — no auth needed
    for individual tweet lookups, but the public search is rate-limited
    to ~180 calls/15min. We hit a small set of high-signal queries.

    If you have TWITTER_BEARER_TOKEN in env, we use the v2 search API
    (much better rate limit + longer history).
    """
    leads = []
    bearer = os.getenv("TWITTER_BEARER_TOKEN", "").strip()
    queries = [
        "we are hiring AI engineer",
        "hiring ML engineer remote",
        "looking for AI agent engineer",
        "hiring data platform engineer",
        "hiring senior AI LLM",
        "hiring RAG engineer",
        "hiring GenAI engineer",
    ]
    if bearer:
        # v2 recent search
        for q in queries:
            url = (
                "https://api.twitter.com/2/tweets/search/recent"
                f"?query={urllib.parse.quote(q + ' -is:retweet lang:en')}"
                "&max_results=50&tweet.fields=created_at,author_id,text"
                "&expansions=author_id&user.fields=username,name,description"
            )
            try:
                out = subprocess.run(
                    ["curl", "-sL", "-m", "20",
                     "-H", f"Authorization: Bearer {bearer}",
                     "-A", "avilx-lead-bot/1.0",
                     url],
                    capture_output=True, text=True, timeout=25,
                )
                if out.returncode != 0 or not out.stdout:
                    continue
                data = json.loads(out.stdout)
            except Exception:
                continue
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            for t in data.get("data", []) or []:
                text = t.get("text", "")
                if EXCLUDE_TITLE.search(text):
                    continue
                emails = _extract_real_emails(text)
                urls = re.findall(r"https?://[^\s)\"']+", text)
                urls = [u for u in urls if "twitter.com" not in u and "x.com" not in u]
                if not emails and not urls:
                    continue
                author = users.get(t.get("author_id", ""), {}) or {}
                handle = author.get("username", "unknown")
                company = (author.get("name") or handle).strip()[:60]
                leads.append({
                    "company": company or f"@{handle}",
                    "role": text[:120],
                    "source": f"twitter @{handle}",
                    "source_url": f"https://x.com/{handle}/status/{t.get('id')}",
                    "contact_email": emails[0] if emails else None,
                    "extra_emails": emails[1:5],
                    "extra_urls": urls[:3],
                    "raw_excerpt": text[:400],
                })
    else:
        # Fallback: Nitter public instances (often down, but worth a try)
        nitter_hosts = ["nitter.net", "nitter.poast.org", "nitter.privacydev.net"]
        for q in queries[:3]:  # cap to keep this fast
            for host in nitter_hosts:
                url = f"https://{host}/search?f=tweets&q={urllib.parse.quote(q)}"
                code, html = _curl(url, timeout=10)
                if code != 200 or not html:
                    continue
                # Pull tweet text + handle from Nitter's HTML
                for m in re.finditer(
                    r'<a class="username"[^>]*>@([\w]+)</a>.*?'
                    r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>',
                    html, re.S,
                ):
                    handle = m.group(1)
                    body = re.sub(r"<[^>]+>", " ", m.group(2))
                    body = re.sub(r"\s+", " ", body).strip()
                    if not body or EXCLUDE_TITLE.search(body):
                        continue
                    emails = _extract_real_emails(body)
                    if not emails:
                        continue
                    leads.append({
                        "company": f"@{handle}",
                        "role": body[:120],
                        "source": f"twitter @{handle} (via nitter)",
                        "source_url": f"https://x.com/{handle}",
                        "contact_email": emails[0],
                        "extra_emails": emails[1:5],
                        "raw_excerpt": body[:400],
                    })
                if leads:
                    break  # one nitter host succeeded
    return leads


def scrape_remotive():
    """Remotive.io public job feed — JSON API, no auth.

    Capped to software/developer roles and our keyword set.
    """
    leads = []
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=100"
    code, body = _curl(url, timeout=20)
    if code != 200 or not body:
        return leads
    try:
        data = json.loads(body)
    except Exception:
        return leads
    for jl in (data.get("jobs") or [])[:50]:
        title = (jl.get("title") or "").strip()
        company = (jl.get("company_name") or "").strip()
        desc = (jl.get("description") or "")
        text = f"{title}\n{desc}"
        if not any(kw.lower() in text.lower() for kw in SCRAPE_KEYWORDS):
            continue
        if EXCLUDE_TITLE.search(text):
            continue
        # Strip HTML for email extraction
        text_plain = re.sub(r"<[^>]+>", " ", text)
        emails = _extract_real_emails(text_plain)
        leads.append({
            "company": company or "Remotive",
            "role": title,
            "source": "remotive",
            "source_url": jl.get("url", ""),
            "contact_email": emails[0] if emails else None,
            "extra_emails": emails[1:5],
            "raw_excerpt": re.sub(r"\s+", " ", text_plain)[:400],
        })
    return leads


def scrape_jobicy():
    """Jobicy.com public feed — JSON API."""
    leads = []
    for tag in ["data-science", "ai-ml", "software-engineer", "devops"]:
        url = f"https://jobicy.com/api/v2/remote-jobs?count=50&tag={tag}"
        code, body = _curl(url, timeout=20)
        if code != 200 or not body:
            continue
        try:
            data = json.loads(body)
        except Exception:
            continue
        for jl in (data.get("jobList") or [])[:30]:
            title = (jl.get("jobTitle") or "").strip()
            company = (jl.get("companyName") or "").strip()
            desc = (jl.get("jobDescription") or "")
            text = f"{title}\n{desc}"
            if not any(kw.lower() in text.lower() for kw in SCRAPE_KEYWORDS):
                continue
            if EXCLUDE_TITLE.search(text):
                continue
            text_plain = re.sub(r"<[^>]+>", " ", text)
            emails = _extract_real_emails(text_plain)
            leads.append({
                "company": company or "Jobicy",
                "role": title,
                "source": f"jobicy:{tag}",
                "source_url": jl.get("url", ""),
                "contact_email": emails[0] if emails else None,
                "extra_emails": emails[1:5],
                "raw_excerpt": re.sub(r"\s+", " ", text_plain)[:400],
            })
    return leads


def scrape_discord_jobs():
    """Public Discord servers that post jobs (no auth needed for public channels).

    Strategy: search for Discord server invite links on the open web via
    Google-style search. For each invite, we just record the URL — we
    don't join the server (that would need a user token).

    For practical leads, we focus on a small set of well-known public
    hiring servers whose invite links appear on Reddit/LinkedIn posts.

    Note: actual scraping inside Discord requires a user/bot token.
    Without one, this is a directory of leads-to-prospect, not direct
    contacts. Mark them with `apply_method=url` so the email pipeline
    skips them and a manual outreach workflow picks them up.
    """
    # Curated list of public AI/Data hiring Discord servers — invites are
    # stable. Update this list as you discover more.
    SERVERS = [
        ("MLOps Community",       "https://discord.gg/MLOps"),
        ("DSPy",                  "https://discord.gg/XCGyv2DuGM"),
        ("Weights & Biases",      "https://discord.gg/wandb"),
        ("LangChain",             "https://discord.gg/langchain"),
        ("LlamaIndex",            "https://discord.gg/eN6D2HQ6aX"),
        ("OpenAI Dev",            "https://discord.gg/openai"),
        ("HuggingFace",           "https://discord.gg/huggingface"),
        ("PyTorch",               "https://discord.gg/pytorch"),
        ("Databricks Community",  "https://discord.gg/databricks"),
        ("Snowflake Builders",    "https://discord.gg/snowflake"),
        ("dbt Community",         "https://discord.gg/getdbt"),
        ("Apache Airflow",        "https://airflow.apache.org/community/"),
    ]
    leads = []
    for name, invite in SERVERS:
        leads.append({
            "company": name,
            "role": "Discord community (look for #jobs / #hiring channels)",
            "source": "discord (directory)",
            "source_url": invite,
            "contact_email": None,
            "extra_emails": [],
            "raw_excerpt": f"Public hiring-focused Discord server: {invite}",
            "apply_method": "url",
        })
    return leads


def scrape_telegram_jobs():
    """Public Telegram channels that post jobs.

    Telegram's public channels can be fetched via the `t.me/s/<channel>`
    web preview — no auth needed. We crawl a curated list of well-known
    AI/Data hiring channels.
    """
    CHANNELS = [
        ("remoteai",       "https://t.me/s/remoteai"),
        ("ai_jobs",        "https://t.me/s/ai_jobs"),
        ("ml_jobs",        "https://t.me/s/ml_jobs"),
        ("data_jobs",      "https://t.me/s/data_jobs"),
        ("ds_jobs",        "https://t.me/s/ds_jobs"),
        ("remotedevjobs",  "https://t.me/s/remotedevjobs"),
        ("weworkremotely", "https://t.me/s/weworkremotely_jobs"),
    ]
    leads = []
    for ch_name, url in CHANNELS:
        code, html = _curl(url, timeout=15)
        if code != 200 or not html:
            continue
        # Each message is wrapped in <div class="tgme_widget_message_wrap">
        for m in re.finditer(
            r'<div class="tgme_widget_message_wrap"[^>]*>(.*?)(?=<div class="tgme_widget_message_wrap"|</div></div></div></div>\s*</div>\s*</body)',
            html, re.S,
        ):
            chunk = m.group(1)
            text_m = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
                               chunk, re.S)
            if not text_m:
                continue
            text = re.sub(r"<[^>]+>", " ", text_m.group(1))
            text = re.sub(r"&[a-z]+;", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if not text or len(text) < 20:
                continue
            lower = text.lower()
            if not any(kw.lower() in lower for kw in SCRAPE_KEYWORDS):
                continue
            if EXCLUDE_TITLE.search(text):
                continue
            emails = _extract_real_emails(text)
            leads.append({
                "company": f"Telegram @{ch_name}",
                "role": text[:120],
                "source": f"telegram:{ch_name}",
                "source_url": url,
                "contact_email": emails[0] if emails else None,
                "extra_emails": emails[1:5],
                "raw_excerpt": text[:400],
            })
        if not leads:
            # Still record the channel as a URL lead so we know it was checked
            leads.append({
                "company": f"Telegram @{ch_name}",
                "role": "Telegram hiring channel",
                "source": f"telegram:{ch_name}",
                "source_url": url,
                "contact_email": None,
                "raw_excerpt": "Telegram hiring channel — view on web to see posts",
                "apply_method": "url",
            })
    return leads


def scrape_asian_chat_jobs():
    """WeChat / Zalo / Line — Asian chat platforms.

    These are closed networks (no public search API like Discord/Telegram).
    We do a best-effort web search for public posts that mention hiring
    into these networks, then record the post URL as a manual-lead.

    Specifically we hit Bing's public search (no auth, ~10 queries/min)
    for WeChat Official Accounts that post jobs and Zalo OA channels.
    """
    leads = []
    queries = [
        '"wechat" "hiring" "AI engineer" "data scientist"',
        '"zalo" "tuyển" "AI engineer" OR "data engineer"',
        '"wechat group" "AI jobs" "apply"',
    ]
    for q in queries:
        url = "https://www.bing.com/search?" + urllib.parse.urlencode({
            "q": q, "format": "rss",
        })
        code, xml = _curl(url, timeout=15)
        if code != 200 or not xml:
            continue
        for item in re.findall(r"<item>(.*?)</item>", xml, re.S):
            title_m = re.search(r"<title>(.*?)</title>", item, re.S)
            link_m = re.search(r"<link>(.*?)</link>", item)
            desc_m = re.search(r"<description>(.*?)</description>", item, re.S)
            if not (title_m and link_m):
                continue
            title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
            desc = re.sub(r"<[^>]+>", " ", desc_m.group(1)) if desc_m else ""
            desc = re.sub(r"\s+", " ", desc).strip()
            text = f"{title}\n{desc}"
            if not any(kw.lower() in text.lower() for kw in SCRAPE_KEYWORDS):
                continue
            if EXCLUDE_TITLE.search(text):
                continue
            emails = _extract_real_emails(text)
            leads.append({
                "company": "WeChat/Zalo (CN/VN chat)",
                "role": title[:120],
                "source": "bing:wechat_zalo",
                "source_url": link_m.group(1).strip(),
                "contact_email": emails[0] if emails else None,
                "extra_emails": emails[1:5],
                "raw_excerpt": desc[:400] or title[:400],
                "apply_method": "url",  # mark as manual-outreach
            })
    return leads


SCRAPERS = [
    ("hn_who_is_hiring",   scrape_hn_who_is_hiring),
    ("weworkremotely",     scrape_weworkremotely),
    ("ai_jobs_net",        scrape_ai_jobs_net),
    ("reddit_ml_jobs",     scrape_reddit_ml_jobs),
    ("twitter_x_jobs",     scrape_twitter_x_jobs),
    ("remotive",           scrape_remotive),
    ("jobicy",             scrape_jobicy),
    ("discord_jobs",       scrape_discord_jobs),
    ("telegram_jobs",      scrape_telegram_jobs),
    ("asian_chat_jobs",    scrape_asian_chat_jobs),
]


def scrape_all():
    """Run every scraper, return de-duped list keyed on (company, role)."""
    all_leads = []
    for name, fn in SCRAPERS:
        try:
            found = fn()
            print(f"  scrape.{name}: {len(found)} candidates")
            all_leads.extend(found)
        except Exception as e:
            print(f"  scrape.{name} error: {e}")
    # Dedup in-process
    seen = set()
    deduped = []
    for ld in all_leads:
        key = (ld["company"].lower(), ld["role"][:60].lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ld)
    return deduped


# =============================================================
# 2. ENRICH — for URL-only leads, hunt for a contact email
# =============================================================

def enrich_url_only_lead(lead):
    """Given a lead dict with no contact_email but with source_url,
    try to find a real contact email on the source page or the company domain.
    Returns updated lead."""
    from db.lead_store import find_duplicate

    url = lead.get("source_url")
    if not url or lead.get("contact_email"):
        return lead

    # 1. Fetch source page, scan for emails
    code, html = _curl(url, timeout=12)
    if code == 200 and html:
        emails = _extract_real_emails(html)
        if emails:
            lead["contact_email"] = emails[0]
            lead["extra_emails"] = emails[1:5]
            return lead

    # 2. Derive company domain, probe /careers /contact /hiring
    domain = _company_domain_from_url(url) or _company_domain_from_company(lead["company"])
    if not domain:
        return lead
    for path in ("/careers", "/careers/", "/jobs", "/jobs/", "/hiring",
                 "/contact", "/contact-us", "/team", "/about", "/about-us"):
        probe = f"https://{domain}{path}"
        code, html = _curl(probe, timeout=10)
        if code == 200 and html:
            emails = _extract_real_emails(html)
            if emails:
                lead["contact_email"] = emails[0]
                lead["extra_emails"] = emails[1:5]
                lead["enrich_source"] = probe
                return lead
    return lead


def _company_domain_from_url(url):
    try:
        host = urllib.parse.urlparse(url).hostname or ""
        host = host.lower()
        if host.startswith("www."):
            host = host[4:]
        if host.endswith("linkedin.com") or host.endswith("indeed.com"):
            return None
        # Only treat as company site if it has at least 2 dots
        if host.count(".") >= 1 and not host.endswith(".gg"):
            return host
    except Exception:
        pass
    return None


def _company_domain_from_company(company):
    """Heuristic: 'Acme Corp' -> 'acmecorp.com' (just guess; we verify by probe)."""
    if not company or company == "Unknown (HN)":
        return None
    slug = re.sub(r"[^A-Za-z0-9]", "", company).lower()
    if not slug:
        return None
    return f"{slug}.com"


# =============================================================
# 3+4. DEDUP + QUEUE — insert net-new into Postgres
# =============================================================

def queue_leads(leads, dry=False):
    """Insert leads into Postgres, skipping duplicates.

    Returns (inserted, skipped) counts.
    """
    from db.lead_store import insert_lead, find_duplicate
    inserted, skipped, errored = 0, 0, 0
    for ld in leads:
        try:
            # If no email and not enrichable, mark for manual follow-up
            if not ld.get("contact_email"):
                # Try enrich
                ld = enrich_url_only_lead(ld)
            email = ld.get("contact_email")
            if not email:
                # Skip but record as URL-only lead (apply_method=url)
                role = ld["role"]
            else:
                role = ld["role"]
            # Dedupe: by company + email (or company + role if no email)
            dup = find_duplicate(ld["company"], email or f"no-email@{ld['source']}", role)
            if dup:
                skipped += 1
                continue
            if dry:
                inserted += 1
                continue
            cover_subject, cover_body = _build_cover_letter(ld)
            stack = _guess_stack(ld)
            lead_row = {
                "company": ld["company"],
                "role": role,
                "contact_email": email,
                "contact_phone": None,
                "apply_method": "email" if email else "url",
                "stack": stack,
                "rate": "Not listed",
                "source_url": ld.get("source_url", ""),
                "jd_text": ld.get("raw_excerpt", ""),
                "cover_letter_subject": cover_subject,
                "cover_letter_body": cover_body,
            }
            insert_lead(lead_row, source=f"autopilot:{ld.get('source','unknown')}")
            inserted += 1
        except Exception as e:
            errored += 1
            print(f"  queue error for {ld.get('company')}: {e}")
    return inserted, skipped, errored


def _guess_stack(lead):
    text = (lead.get("role", "") + " " + lead.get("raw_excerpt", "")).lower()
    bits = []
    for k in ("python", "pytorch", "tensorflow", "langchain", "llama",
              "rag", "llm", "openai", "anthropic", "aws", "azure", "gcp",
              "databricks", "snowflake", "spark", "kubernetes", "kafka",
              "airflow", "dbt", "vector", "embedding", "agent", "agentic",
              "mlops", "fine-tun", "transformer", "nlp", "cv", "computer vision"):
        if k in text:
            bits.append(k)
    return ", ".join(bits[:10]) or "AI / ML"


def _build_cover_letter(lead):
    """Render a short, role-aware Avilx cover letter.

    Subject is trimmed to ≤60 chars (Gmail truncates previews past ~70).
    Body pulls one verbatim phrase from the JD to prove we read it.
    Pricing is left OUT of the first email (recruiters screen for fit first;
    price in the reply sounds transactional).
    """
    company = (lead.get("company") or "").strip() or "your team"
    role = (lead.get("role") or "this role").strip()
    stack = _guess_stack(lead)
    excerpt = (lead.get("raw_excerpt") or "").strip()
    is_remote = "remote" in excerpt.lower() or "anywhere" in excerpt.lower()
    remote_phrase = "remote" if is_remote else "global"
    # Trim subject to ~60 chars
    comp_short = company if len(company) <= 25 else company[:22] + "…"
    role_short = role if len(role) <= 30 else role[:27] + "…"
    subject = f"Avilx for {comp_short} — {role_short}"
    if len(subject) > 70:
        subject = subject[:67] + "…"

    # Pull a verbatim phrase from the JD that mentions a key tool/area
    verbatim = _pull_verbatim_phrase(excerpt)
    stack_line = (
        f"Stack overlap I noticed: {stack}." if stack and stack != "AI / ML"
        else "Our pod is senior-only on the AI/Data/ML/Cloud side."
    )

    body = (
        f"Hi {company} team,\n\n"
        f"Saw the {role} role"
        + (f' — {verbatim}' if verbatim else "")
        + ". Quick context if useful: I'm Prem, I run Avilx (avilx.com), a "
        f"global Build·Deploy·Engineers pod out of Ha Noi. 6-20 senior engineers, "
        f"AI/Data/ML/Cloud, **Databricks Champion** team, 7+ clouds (AWS · Azure · "
        f"GCP · Tencent · Alibaba), 8+ yrs avg, regulated-industry work.\n\n"
        f"{stack_line}\n\n"
        f"If your timeline is tight, happy to run a 4-week pilot pod or staff-aug "
        f"a senior — 2-week kickoff, {remote_phrase} delivery, NDA + IP clean. "
        f"15-min call this week worth it?\n\n"
        f"{PERSONAL_SIG}"
    )
    return subject, body


_VERBATIM_PHRASES = [
    r"scaling (?:our )?RAG",
    r"(?:production|prod) RAG",
    r"agentic (?:KYC|workflow|AI)",
    r"multi[- ]agent",
    r"fine[- ]tun(?:e|ing)",
    r"(?:real[- ]?time )?CDC (?:lakehouse|pipeline)",
    r"Databricks (?:lakehouse|migration)",
    r"vector (?:search|database|store)",
    r"embedding (?:pipeline|model)",
    r"LangChain|LlamaIndex",
    r"(?:ML|model) (?:training|inference) (?:pipeline|infrastructure)",
    r"on[- ]call|incident response",
    r"SOC 2|HIPAA|PCI|MLPS 2\.0",
    r"trading|fintech|banking",
    r"recommendation (?:system|engine)",
    r"fraud detection|risk scoring",
]


def _pull_verbatim_phrase(excerpt: str) -> str | None:
    """Return the first matching phrase from the JD as a short verbatim
    fragment, lowercased and stripped. Used to make the cover letter feel
    like we read the JD."""
    if not excerpt:
        return None
    for pat in _VERBATIM_PHRASES:
        m = re.search(pat, excerpt, re.IGNORECASE)
        if m:
            phrase = m.group(0).strip().lower()
            if len(phrase) > 60:
                phrase = phrase[:57] + "…"
            return phrase
    return None


# =============================================================
# 5. EMAIL — send queued leads with daily cap
# =============================================================

def send_queued_emails(max_emails=None, dry=False):
    """Pull pending email leads from Postgres, send up to max_emails, mark sent."""
    from db.lead_store import get_pending_leads, update_status, is_opted_out
    if max_emails is None:
        max_emails = DAILY_LIMIT

    pending = [l for l in get_pending_leads()
               if l.get("contact_email") and l.get("apply_method") == "email"]
    pending = [l for l in pending if not is_opted_out(l["contact_email"])]
    pending = pending[:max_emails]

    sent, failed, bounced = 0, 0, 0
    for lead in pending:
        if dry:
            print(f"  [dry] would email {lead['contact_email']} re: {lead['company']}")
            sent += 1
            continue
        try:
            _send_one(lead)
            update_status(lead["id"], "sent_email")
            sent += 1
            print(f"  ✅ {lead['company']} → {lead['contact_email']}")
            if sent < len(pending):
                time.sleep(DELAY_BETWEEN_EMAILS_SEC)
        except RecipientInvalid as e:
            # _send_one already marked status='bounced' in the DB.
            bounced += 1
            print(f"  🚫 {lead['company']} → {lead['contact_email']}  bounced: {e.code} {e.reason[:60]}")
            # No sleep — bounced sends are cheap, no need to throttle.
        except Exception as e:
            update_status(lead["id"], "failed", error=str(e))
            failed += 1
            print(f"  ❌ {lead['company']} → {lead['contact_email']}  err: {e}")
    return sent, failed, bounced


def _pick_resume(lead) -> Optional[Path]:
    """Return the Path to the best resume to attach for this lead.

    Order:
      1. A JD-tailored .docx (or .pdf) generated for this (company, role).
      2. The resume_file path the lead row already has.
      3. The default RESUME_DIR / Prem_Resume_2026.pdf.

    Returns None if no resume is found at all.
    """
    # 1) JD-tailored: best fit if available
    try:
        from resume_tailor import tailor_resume
        tailored = tailor_resume(lead)
        if tailored and tailored.exists():
            return tailored
    except Exception as e:
        # Tailoring is best-effort — never break a send because of it.
        import sys
        print(f"    ⚠️  resume_tailor failed for lead {lead.get('id')}: {e}",
              file=sys.stderr)

    # 2) Lead's stored resume_file
    rf = lead.get("resume_file")
    if rf:
        p = RESUME_DIR / rf
        if p.exists():
            return p
        # Sometimes resume_file is an absolute path
        if Path(rf).exists():
            return Path(rf)

    # 3) Default fallback
    for name in ("Prem_Resume_2026.pdf", "Pv_Cv_Data_Ai_2026.pdf",
                 "PREM_2026.pdf", "Prem_Resume_2026.docx"):
        p = RESUME_DIR / name
        if p.exists():
            return p
    return None


def _render_email_html(lead: dict) -> str:
    """Render the designed HTML body of the email.

    Layout:
      - Navy gradient header with "Avilx" + tagline + role pill
      - Hi {company} line
      - The cover letter (cover_letter_body) — auto-converted \n to <br>
      - Value-prop strip: BUILD · DEPLOY · ENGINEERS
      - Stats strip: 15+ yrs · 7+ clouds · $40-70/hr · 8+ yrs avg
      - Signature block
      - Footer with tracking_id, unsubscribe mailto, anti-spam disclosure
    """
    company = (lead.get("company") or "your team").strip()
    role = (lead.get("role") or "this role").strip()
    tracking_id = (lead.get("tracking_id") or "").strip()
    body_text = (lead.get("cover_letter_body")
                 or "Hi — quick intro from Avilx, a senior AI/Data/ML/Cloud pod.")

    # Convert cover letter body to HTML (preserve paragraphs)
    # Each \n\n → </p><p>, single \n → <br>
    paragraphs = []
    for chunk in re.split(r"\n{2,}", body_text.strip()):
        chunk = chunk.strip()
        if not chunk:
            continue
        # Strip the PERSONAL_SIG lines from the body — we render our own sig
        if "Avilx — Global Build" in chunk or "Delivery:" in chunk[:30]:
            continue
        if "Prem Vishnoi" in chunk and "Avilx" in chunk and len(chunk) < 600:
            continue
        html_chunk = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", chunk)
        html_chunk = html_chunk.replace("\n", "<br>")
        paragraphs.append(f"<p>{html_chunk}</p>")

    # Footer (tracking + opt-out)
    unsub_mailto = (
        f"mailto:{YOUR_EMAIL}?subject=unsubscribe%20{urllib.parse.quote(company)}"
        f"&body=Please%20remove%20me%20from%20the%20Avilx%20outreach%20list."
    )
    tracking_pill = (
        f'<span style="display:inline-block;padding:2px 8px;'
        f'background:#f1f5f9;color:#475569;border-radius:10px;'
        f'font-size:11px;font-family:Menlo,monospace;">'
        f'tracking: {tracking_id}</span>'
    ) if tracking_id else ""

    # Escape any HTML in company/role for safety
    from html import escape
    company_safe = escape(company)
    role_safe = escape(role)

    # JD snippet (short, in italics) — to prove we read the JD
    jd_snippet = ""
    raw = (lead.get("jd_text") or "").strip()
    if raw:
        snippet = re.sub(r"\s+", " ", raw)[:160]
        if len(raw) > 160:
            snippet += "…"
        jd_snippet = (
            f'<p style="margin:14px 0 4px;font-size:12px;color:#94a3b8;'
            f'font-style:italic;line-height:1.5;border-left:3px solid #cbd5e1;'
            f'padding-left:10px;">{escape(snippet)}</p>'
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light only">
<title>Avilx × {company_safe}</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,
                          'Helvetica Neue',Arial,sans-serif;
             color:#1e293b;-webkit-font-smoothing:antialiased;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:#f1f5f9;padding:24px 12px;">
  <tr>
    <td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0"
             style="max-width:600px;background:#ffffff;border-radius:12px;
                    overflow:hidden;box-shadow:0 4px 20px rgba(15,23,42,0.08);">

        <!-- Header: navy gradient -->
        <tr>
          <td style="background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 60%,#1d4ed8 100%);
                     padding:28px 32px 24px;color:#ffffff;">
            <div style="font-size:13px;letter-spacing:0.18em;
                        text-transform:uppercase;color:#93c5fd;margin-bottom:4px;">
              Global Build · Deploy · Engineers
            </div>
            <div style="font-size:30px;font-weight:700;letter-spacing:-0.02em;
                        line-height:1.1;margin:0;">
              Avilx<span style="color:#60a5fa;">.</span>
            </div>
            <div style="font-size:14px;color:#cbd5e1;margin-top:10px;
                        line-height:1.5;">
              Senior-only AI · Data · ML · Cloud pod<br>
              Databricks Champion · 7+ clouds · 8+ yrs avg
            </div>
            <div style="margin-top:18px;display:inline-block;
                        background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.25);
                        padding:6px 14px;border-radius:99px;font-size:13px;
                        color:#e0e7ff;">
              re: <strong style="color:#ffffff;">{role_safe}</strong>
              {f' at <strong style="color:#ffffff;">{company_safe}</strong>' if company_safe != "your team" else ""}
            </div>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:28px 32px 12px;font-size:15px;line-height:1.7;
                     color:#1e293b;">
            {''.join(paragraphs)}
            {jd_snippet}
          </td>
        </tr>

        <!-- Value-prop strip -->
        <tr>
          <td style="padding:14px 32px 0;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                   style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                          overflow:hidden;">
              <tr>
                <td style="padding:14px 0;text-align:center;width:33.33%;
                           border-right:1px solid #e2e8f0;">
                  <div style="font-size:11px;color:#64748b;letter-spacing:0.1em;
                              text-transform:uppercase;">Build</div>
                  <div style="font-size:14px;font-weight:600;color:#0f172a;margin-top:2px;">
                    Production in 2 wks
                  </div>
                </td>
                <td style="padding:14px 0;text-align:center;width:33.33%;
                           border-right:1px solid #e2e8f0;">
                  <div style="font-size:11px;color:#64748b;letter-spacing:0.1em;
                              text-transform:uppercase;">Deploy</div>
                  <div style="font-size:14px;font-weight:600;color:#0f172a;margin-top:2px;">
                    On your cloud
                  </div>
                </td>
                <td style="padding:14px 0;text-align:center;width:33.33%;">
                  <div style="font-size:11px;color:#64748b;letter-spacing:0.1em;
                              text-transform:uppercase;">Engineers</div>
                  <div style="font-size:14px;font-weight:600;color:#0f172a;margin-top:2px;">
                    Senior-only, 8+ yrs
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Stats strip -->
        <tr>
          <td style="padding:18px 32px 0;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="text-align:center;width:25%;">
                  <div style="font-size:22px;font-weight:700;color:#1d4ed8;line-height:1;">15+</div>
                  <div style="font-size:11px;color:#64748b;margin-top:4px;
                              text-transform:uppercase;letter-spacing:0.08em;">years</div>
                </td>
                <td style="text-align:center;width:25%;">
                  <div style="font-size:22px;font-weight:700;color:#1d4ed8;line-height:1;">7+</div>
                  <div style="font-size:11px;color:#64748b;margin-top:4px;
                              text-transform:uppercase;letter-spacing:0.08em;">clouds</div>
                </td>
                <td style="text-align:center;width:25%;">
                  <div style="font-size:22px;font-weight:700;color:#1d4ed8;line-height:1;">$40-70</div>
                  <div style="font-size:11px;color:#64748b;margin-top:4px;
                              text-transform:uppercase;letter-spacing:0.08em;">/hr staff</div>
                </td>
                <td style="text-align:center;width:25%;">
                  <div style="font-size:22px;font-weight:700;color:#1d4ed8;line-height:1;">$120-180</div>
                  <div style="font-size:11px;color:#64748b;margin-top:4px;
                              text-transform:uppercase;letter-spacing:0.08em;">/hr squad</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Signature -->
        <tr>
          <td style="padding:24px 32px 4px;font-size:14px;line-height:1.7;
                     color:#1e293b;">
            <p style="margin:0 0 4px;">— Prem Vishnoi</p>
            <p style="margin:0;color:#475569;font-size:13px;">
              Founder · Avilx<br>
              <a href="{YOUR_WEBSITE}" style="color:#1d4ed8;text-decoration:none;">{YOUR_WEBSITE}</a>
              · <a href="mailto:{YOUR_EMAIL}" style="color:#1d4ed8;text-decoration:none;">{YOUR_EMAIL}</a>
              {f'· <a href="https://wa.me/{YOUR_WHATSAPP.lstrip("+")}" style="color:#1d4ed8;text-decoration:none;">WhatsApp</a>' if YOUR_WHATSAPP else ''}
            </p>
            <p style="margin:8px 0 0;color:#94a3b8;font-size:12px;">
              HQ: Ha Noi, Vietnam · Delivery: China · APAC · US · EU
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:18px 32px 24px;border-top:1px solid #e2e8f0;
                     margin-top:18px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="font-size:11px;color:#94a3b8;line-height:1.6;">
                  Sent because your team posted a role we can staff for.
                  You're not on a list — this is a 1:1 intro.
                  {tracking_pill}
                  <br>
                  <a href="{unsub_mailto}" style="color:#94a3b8;text-decoration:underline;">
                    Opt out of future outreach
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""


class RecipientInvalid(Exception):
    """Reserved for future use. NOT raised by current send path.

    Gmail's SMTP frontend says OK (250) to ANY RCPT TO request — it does
    not actually validate the recipient at that layer. Bounces come back
    asynchronously as a separate "Delivery Status Notification (Failure)"
    email, which `check_bounces.py` catches via IMAP.

    We keep this exception type so the caller (`send_queued_emails`) can
    still distinguish "rejected before send" from "rejected during send"
    in the future if/when we add a different verification mechanism
    (e.g. probing the destination MX directly).
    """
    def __init__(self, email, code, reason):
        self.email = email
        self.code = code
        self.reason = reason
        super().__init__(f"Recipient invalid: {email} ({code} {reason})")


def _verify_recipient(addr: str, timeout: int = 15) -> None:
    """Currently a no-op. Gmail's SMTP accepts any RCPT TO at send time.

    See the docstring on `RecipientInvalid` for why. The real bounce
    detection is in `check_bounces.py` (IMAP poll on the sender inbox).

    Kept as a stub so callers don't have to change if/when we add a
    real verification step (e.g. SMTP MX probe or 3rd-party validator
    like NeverBounce / ZeroBounce).
    """
    return


def _send_one(lead):
    """Build + send one email via SMTP with retry + backoff.

    Retries up to 3 times on transient failures (network blip, Gmail 4xx
    "try again later"). Only raises after the final attempt — the caller
    is then responsible for marking the lead as `failed`.

    Renders a multipart/alternative email:
      - text/plain: fallback for clients that strip HTML
      - text/html : designed email (gradient header, value-prop strip,
                    stats strip, JD-tailored summary, signature, footer)

    Tries to attach a JD-tailored resume (resume_tailor.tailor_resume).
    Falls back to the default resume file from the lead row, then to
    RESUME_DIR/Prem_Resume_2026.pdf.

    Note on bounce prevention: Gmail's SMTP accepts any RCPT TO at send
    time, so we can't pre-validate. The real bounce detection runs in
    `check_bounces.py` (IMAP poll on the sender inbox) — every morning
    the cron job reads the "Delivery Status Notification (Failure)"
    messages Gmail sent us and marks the corresponding leads as bounced.
    """
    addr = lead["contact_email"]
    if not addr:
        raise ValueError("Lead has no contact_email")
    # ---- PRE-VALIDATE: currently a no-op (see docstring) ----
    # Kept as a hook in case we add a 3rd-party validator later.
    _verify_recipient(addr)

    msg = MIMEMultipart("mixed")
    msg["From"] = f"{YOUR_NAME} <{SMTP_USER}>"
    msg["To"] = lead["contact_email"]
    subject = (lead.get("cover_letter_subject")
               or f"Avilx × {lead['company']}")
    # Strip CR/LF/tab from subject — multi-line subject is a malformed
    # MIME header and will bounce.
    subject = re.sub(r"[\r\n\t]+", " ", subject).strip()
    msg["Subject"] = subject
    msg["Reply-To"] = YOUR_EMAIL

    # ---- build body (HTML + plain-text alternative) ----
    text = (lead.get("cover_letter_body")
            or "Hi — quick intro from Avilx (avilx.com), senior AI/Data/ML/Cloud pod.")
    html = _render_email_html(lead)

    body = MIMEMultipart("alternative")
    body.attach(MIMEText(text, "plain", "utf-8"))
    body.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(body)

    # ---- pick the right resume ----
    resume_path = _pick_resume(lead)
    if resume_path and resume_path.exists() \
            and resume_path.stat().st_size <= 5 * 1024 * 1024:
        ctype = "application/pdf" if resume_path.suffix.lower() == ".pdf" \
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        maintype, subtype = ctype.split("/", 1)
        with open(resume_path, "rb") as f:
            part = MIMEBase(maintype, subtype)
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={resume_path.name}",
        )
        msg.attach(part)
        print(f"    📎 attached: {resume_path.name} "
              f"({resume_path.stat().st_size // 1024} KB)")

    def _do_send():
        if SMTP_USE_SSL:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as s:
                s.login(SMTP_USER, SMTP_PASS)
                refused = s.send_message(msg)
                return None, refused
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                refused = s.send_message(msg)
                return None, refused

    # Retry on transient errors only. We re-raise permanent errors (auth fail,
    # bad recipient) immediately so the lead is marked failed and we move on.
    # PERMANENT errors (don't retry):
    #   - SMTPAuthenticationError  — bad password, fix at config time
    #   - SMTPRecipientsRefused    — email bounced, retrying won't help
    #   - SMTPSenderRefused        — From address rejected
    # TRANSIENT errors (retry with backoff):
    #   - SMTPResponseException with 421/450/451/452/454
    #   - network/SSL/timeout errors
    last_err = None
    backoff = [0, 30, 120]  # 0s, 30s, 2m
    for attempt, sleep_s in enumerate(backoff, start=1):
        if sleep_s:
            time.sleep(sleep_s)
        try:
            _do_send()
            # SUCCESS: caller (send_queued_emails) does the atomic
            # update_status + log_send in a single transaction. We just return.
            return
        except smtplib.SMTPAuthenticationError:
            raise  # bad password — never transient
        except smtplib.SMTPRecipientsRefused:
            raise  # hard bounce — never transient
        except smtplib.SMTPSenderRefused:
            raise  # From address rejected — never transient
        except (smtplib.SMTPResponseException, smtplib.SMTPServerDisconnected,
                smtplib.SMTPConnectError, smtplib.SMTPHeloError,
                smtplib.SMTPDataError, smtplib.SMTPException,
                socket.timeout, ConnectionError, OSError) as e:
            last_err = e
            # Only retry on transient codes
            transient = (
                (isinstance(e, smtplib.SMTPResponseException)
                 and e.smtp_code in (421, 450, 451, 452, 454))
                or isinstance(e, (smtplib.SMTPServerDisconnected,
                                   smtplib.SMTPConnectError,
                                   smtplib.SMTPHeloError,
                                   smtplib.SMTPDataError,
                                   socket.timeout, ConnectionError, OSError))
            )
            if not transient or attempt == len(backoff):
                break
            # else loop: sleep + retry
    # All attempts exhausted
    raise last_err


# =============================================================
# 6. REPORT + main
# =============================================================

def run_pipeline(args):
    print(f"\n{'='*60}\n🤖 AVILX AUTOPILOT — {datetime.now().isoformat()}\n{'='*60}")
    report = {"started_at": datetime.now().isoformat()}
    # ---- Step 0: bounce-sync (auto-mark any new bounces) ----
    if not args.no_bounce_sync:
        try:
            from check_bounces import scan_bounces, mark_bounced
            print("\n[0/4] BOUNCE-SYNC — scan Gmail for delivery failures")
            bounce_map, _ = scan_bounces(since_days=7)
            if bounce_map:
                counts = mark_bounced(bounce_map, dry=args.dry)
                report["bounce_sync"] = counts
                print(f"  → marked {counts.get('marked', 0)} newly bounced, "
                      f"{counts.get('already_bounced', 0)} already, "
                      f"{counts.get('unknown', 0)} unknown")
            else:
                print("  → no new bounces in last 7 days")
                report["bounce_sync"] = {"marked": 0}
        except Exception as e:
            print(f"  ⚠️  bounce-sync failed: {e}")
            report["bounce_sync"] = {"error": str(e)}
    if not args.email_only:
        print("\n[1/4] SCRAPE — public sources")
        leads = scrape_all()
        report["scraped"] = len(leads)
        print(f"  → {len(leads)} unique candidates after dedup")
        print("\n[2/4] ENRICH — probe companies for missing emails")
        for ld in leads:
            if not ld.get("contact_email") and ld.get("source_url"):
                enrich_url_only_lead(ld)
        with_email = sum(1 for l in leads if l.get("contact_email"))
        report["with_email_after_enrich"] = with_email
        print(f"  → {with_email}/{len(leads)} have an email now")
        print("\n[3/4] QUEUE — insert net-new into Postgres")
        ins, skp, err = queue_leads(leads, dry=args.dry)
        report["queue"] = {"inserted": ins, "skipped_dup": skp, "errored": err}
        print(f"  → inserted {ins}, skipped {skp} dup, errored {err}")
    if not args.scrape_only:
        print("\n[4/4] EMAIL — send up to {} queued leads".format(args.max_emails))
        sent, failed, bounced = send_queued_emails(max_emails=args.max_emails, dry=args.dry)
        report["email"] = {"sent": sent, "failed": failed, "bounced": bounced}
        print(f"  → sent {sent}, bounced {bounced}, failed {failed}")
    report["finished_at"] = datetime.now().isoformat()
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n✅ Report → {REPORT_FILE}")
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scrape", action="store_true", help="Scrape + queue only (no send)")
    p.add_argument("--enrich", action="store_true", help="Enrich only (no scrape, no send)")
    p.add_argument("--email", action="store_true", help="Send queued emails only")
    p.add_argument("--dry", action="store_true", help="Preview, no writes, no sends")
    p.add_argument("--max-emails", type=int, default=DAILY_LIMIT,
                   help=f"Max emails to send this run (default {DAILY_LIMIT})")
    p.add_argument("--no-lock", action="store_true",
                   help="Skip cron lock (only for interactive debugging)")
    p.add_argument("--no-bounce-sync", action="store_true",
                   help="Skip the bounce-sync step at the start of the run")
    args = p.parse_args()

    scrape_only = args.scrape or args.enrich
    email_only = args.email

    def _run():
        if not (scrape_only or email_only):
            return run_pipeline(args)
        if scrape_only:
            print(f"\n🤖 AVILX AUTOPILOT — scrape/enrich only")
            leads = scrape_all()
            for ld in leads:
                if not ld.get("contact_email"):
                    enrich_url_only_lead(ld)
            ins, skp, err = queue_leads(leads, dry=args.dry)
            print(f"\n→ inserted {ins}, skipped {skp}, errored {err}")
            return
        if email_only:
            print(f"\n🤖 AVILX AUTOPILOT — email only")
            sent, failed, bounced = send_queued_emails(max_emails=args.max_emails, dry=args.dry)
            print(f"\n→ sent {sent}, bounced {bounced}, failed {failed}")
            return

    if args.no_lock:
        return _run()

    # Cron lock: prevent overlapping runs (would double-send).
    with cron_lock("avilx.autopilot") as got:
        if not got:
            print("⚠️  Another autopilot run is in progress. Exiting (no-op).")
            return
        return _run()


if __name__ == "__main__":
    main()
