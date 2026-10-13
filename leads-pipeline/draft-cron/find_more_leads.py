#!/usr/bin/env python3
"""
find_more_leads.py — Self-contained lead refresher.
Pulls from RSS feeds + career pages, derives recruiter emails, dedups,
and inserts into Postgres. Honors a per-domain bounce denylist so we
never re-send to addresses that already bounced.

Sources (all are public RSS / job feeds; we read but don't hammer):
  - WeWorkRemotely RSS
  - RemoteOK JSON API
  - HN "Who is hiring?" latest thread
  - YC Work at a Startup RSS
  - Wellfound RSS
  - Hiring.cafe RSS
  - Direct company careers pages (HTML fetch + email-link parse)

Run:  python3 find_more_leads.py
"""

import json
import os
import re
import sys
import time
import secrets
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

import requests
from html import unescape
import traceback

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# ============================================================
# CONFIG
# ============================================================
UA = "Mozilla/5.0 (Avilx-Leads/1.0; +https://avilx.com) AppleWebKit/605.1.15"
TIMEOUT = 12
MIN_INTERVAL = 0.5  # seconds between requests

# Per-domain bounce denylist (we won't try these again)
BOUNCE_DENY = {
    "hex.tech", "anthropic.com", "toggl.com", "samsara.com",
    "toptal.com", "redmimicry.com", "twikey.com", "futurefit.ai",
    "ml6.ai", "snowflake.com", "niuro.com", "wheelhouse.com",
    "eazyml.com", "crustdata.com", "crossinghurdles.com",
    "airbnb.com", "odysseyconsult.com", "vida.global", "m3usa.com",
    "starbridge.io", "mira-construction.com", "helloprint.com",
    "trexquant.com", "prudential.com", "crexi.com", "mistral.ai",
    "codewin.pt", "teneo.com", "boldmetrics.com", "pairio.com",
    "advtravel365.com", "servicelink.com",
}
# Persist any additions to state/bounce_deny.json so subprocesses (refine_pipeline,
# find_clients, backfill_emails) all see the same denylist. See state/bounce_deny_store.py.
try:
    from state.bounce_deny_store import BOUNCE_DENY as _PERSISTED_DENY  # noqa: F401
    BOUNCE_DENY |= _PERSISTED_DENY
except Exception:
    pass

# Senior-level filter — INCLUDES CTO/Head of/VP/Director for leadership roles
JUNIOR_TERMS = re.compile(
    r"\b(junior|jr\.?|intern|entry|graduate|new grad|co-?op|apprentice|"
    r"associate|asst\.?|assistant|level\s*[i1])\b", re.I
)
NON_ENG_TERMS = re.compile(
    r"\b(sales|marketing|recruiter|talent|hr|people ops|account exec|"
    r"customer success|sdr|bdr|ae\b|operations manager|office manager|"
    r"admin|designer|writer|editor|illustrator|animator|translator|"
    r"interpreter|content|social media)\b", re.I
)
AI_DATA_TERMS = re.compile(
    r"\b(ai|ml|llm|genai|rag|agent|mlops|ml platform|data engineer|"
    r"data platform|data science|analytics engineer|etl|elt|"
    r"kafka|spark|databricks|snowflake|bigquery|redshift|dbt|"
    r"airflow|dagster|prefect|terraform|kubernetes|cloud|aws|gcp|"
    r"azure|sre|devops|platform|backend|api|microservices|distributed|"
    r"python|pytorch|tensorflow|llmops|vector|embedding|fine.?tun|"
    r"prompt|chatbot|inference|training|cto|chief|vp\s+eng|"
    r"head\s+of\s+eng|head\s+of\s+data|head\s+of\s+ai|"
    r"head\s+of\s+platform|head\s+of\s+ml|head\s+of\s+infra)\b", re.I
)

JUNK_EMAIL_RE = re.compile(
    r"@(?:example\.com|example\.org|test\.com|localhost|invalid|"
    r"mailinator|yopmail|guerrillamail|10minutemail|tempmail|"
    r"trashmail|getnada|sharklasers|maildrop|dispostable)$", re.I
)
JUNK_COMPANY_RE = re.compile(r"^(?:TestCo|OldCo|DemoCo|SampleCo|FakeCo)[-_]?[a-f0-9]+$", re.I)

# Email-prefix candidates for derived recruiter addresses
EMAIL_PREFIXES = ["careers", "jobs", "talent", "ai-jobs", "hiring", "recruiting", "apply"]

# ============================================================
# SOURCES
# ============================================================
SOURCES = {
    "weworkremotely": {
        "type": "rss",
        "urls": [
            "https://weworkremotely.com/categories/remote-programming-jobs.rss",
            "https://weworkremotely.com/categories/remote-data-science-jobs.rss",
        ],
    },
    "remoteok": {
        "type": "json",
        "url": "https://remoteok.com/api",
    },
    "hnhiring": {
        "type": "rss",
        "url": "https://hnhiring.com/rss",
    },
    "workatastartup": {
        "type": "rss",
        "url": "https://www.workatastartup.com/jobs.rss",
    },
    "wellfound": {
        "type": "rss",
        "url": "https://wellfound.com/jobs.rss",
    },
    "hiringcafe": {
        "type": "rss",
        "url": "https://hiring.cafe/api/rss",
    },
}


def http_get(url, *, headers=None, params=None):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    r = requests.get(url, headers=h, params=params, timeout=TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    return r


def parse_rss(xml_text):
    """Lightweight RSS/Atom feed parser (no feedparser dep)."""
    items = []
    # Try RSS items
    for m in re.finditer(r"<item[\s>](.*?)</item>", xml_text, re.S | re.I):
        block = m.group(1)
        title = _tag(block, "title") or ""
        link = _tag(block, "link") or _tag(block, "guid") or ""
        desc = _tag(block, "description") or _tag(block, "content:encoded") or ""
        pub = _tag(block, "pubDate") or _tag(block, "dc:date") or ""
        items.append({"title": unescape(title).strip(), "link": link.strip(),
                      "description": unescape(re.sub(r"<[^>]+>", " ", desc)).strip(),
                      "pubDate": pub})
    if not items:
        # Atom entries
        for m in re.finditer(r"<entry[\s>](.*?)</entry>", xml_text, re.S | re.I):
            block = m.group(1)
            title = _tag(block, "title") or ""
            link_m = re.search(r'<link[^>]+href=["\']([^"\']+)["\']', block)
            link = link_m.group(1) if link_m else ""
            desc = _tag(block, "summary") or _tag(block, "content") or ""
            items.append({"title": unescape(title).strip(), "link": link.strip(),
                          "description": unescape(re.sub(r"<[^>]+>", " ", desc)).strip(),
                          "pubDate": ""})
    return items


def _tag(block, tag):
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", block, re.S | re.I)
    if m:
        return m.group(1).strip()
    m = re.search(rf"<{tag}[^>]*/>", block, re.I)
    if m:
        return ""
    return None


# ============================================================
# LEAD EXTRACTION
# ============================================================
def extract_email_from_text(text):
    """Return the first plausible recruiter email in the text, or None."""
    if not text:
        return None
    # Find all emails
    candidates = re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
    for c in candidates:
        c_lower = c.lower()
        if JUNK_EMAIL_RE.search(c):
            continue
        # Prefer careers/jobs/talent/hiring patterns
        if any(p in c_lower for p in ("careers@", "jobs@", "talent@", "hiring@",
                                       "recruiting@", "ai-jobs@", "apply@", "ml-jobs@")):
            return c
    # Fall back to first non-junk candidate
    for c in candidates:
        c_lower = c.lower()
        if JUNK_EMAIL_RE.search(c):
            continue
        # Skip noreply/no-reply/info@ addresses
        if any(x in c_lower for x in ("noreply", "no-reply", "donotreply", "unsubscribe")):
            continue
        return c
    return None


def derive_email(company, url):
    """Pick a recruiter email for a company using its primary domain."""
    if not company or not url:
        return None
    # Skip if company-domain is in bounce denylist
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return None
    if not domain:
        return None
    # Check the bounce denylist at the registered-domain level
    reg = ".".join(domain.split(".")[-2:]) if domain.count(".") >= 1 else domain
    if reg in BOUNCE_DENY:
        return None
    # Prefer "careers" prefix
    return f"careers@{domain}"


def is_senior_eng(title, description):
    """Return True if this looks like a senior AI/ML/data/cloud/leadership role.
    Includes senior+ engineers, CTO, VP, Head of, Director, Principal, Staff,
    and Lead roles — for both Avilx BDE pod placements and direct-client CTO
    search.
    """
    t = f"{title} {description or ''}".lower()
    if JUNIOR_TERMS.search(t):
        return False
    if NON_ENG_TERMS.search(t):
        return False
    if not AI_DATA_TERMS.search(t):
        return False
    # Accept CTO/Chief/VP/Head/Director/Principal/Staff/Lead/Senior/Architect
    if re.search(r"\b(cto|chief\s+technology|chief\s+data|chief\s+ai|"
                 r"vp|vice\s+president|head\s+of|director|principal|"
                 r"staff|senior|lead|architect|manager|"
                 r"engineer\s*ii|engineer\s*iii|sr\.?)\b", t):
        return True
    if re.search(r"\b(\d{1,2})\+?\s*years?\b", t):
        return True
    # Default: include "engineer" titles that match AI/data terms and aren't junior
    if "engineer" in t and AI_DATA_TERMS.search(t):
        return True
    return False


def split_company_role(title):
    """Split 'Acme - Senior AI Engineer' or 'Senior AI Engineer at Acme' into (company, role)."""
    if not title:
        return None, None
    t = title.strip()
    # Common separators
    for sep in [" is hiring a ", " hiring ", " hiring: ", ": ", " — ", " – ",
                " - ", " @ ", " at "]:
        if sep.lower() in t.lower():
            idx = t.lower().find(sep.lower())
            if sep.lower() in (" at ", " @ "):
                left, right = t[:idx].strip(), t[idx + len(sep):].strip()
                # "Senior AI Engineer at Acme" -> company=Acme, role=Senior AI Engineer
                if "engineer" in left.lower() or "scientist" in left.lower() or "designer" in left.lower():
                    return right[:80] or "Unknown", left[:120]
                # "Acme at Senior AI Engineer" -> company=Acme, role=...
                return left[:80] or "Unknown", right[:120]
            else:
                left, right = t[:idx].strip(), t[idx + len(sep):].strip()
                # Usually "Acme - Senior AI Engineer" -> company=Acme
                return left[:80] or "Unknown", right[:120]
    # Fallback: take last token as company, rest as role
    parts = t.split()
    if len(parts) >= 2:
        return " ".join(parts[:-2])[:80] or "Unknown", " ".join(parts[-2:])[:120]
    return t[:80] or "Unknown", "Engineer"


# ============================================================
# SCRAPERS
# ============================================================
def scrape_weworkremotely():
    out = []
    for url in SOURCES["weworkremotely"]["urls"]:
        try:
            xml = http_get(url).text
            for item in parse_rss(xml):
                if not is_senior_eng(item["title"], item["description"]):
                    continue
                co, role = split_company_role(item["title"])
                # WWR link is /remote-jobs/<slug> on weworkremotely.com — must derive from company name
                em = (extract_email_from_text(item["description"]) or
                      derive_email_from_company(co))
                if not em:
                    continue
                out.append({
                    "company": co, "role": role, "contact_email": em,
                    "source_url": item["link"], "source": "weworkremotely",
                    "jd_text": item["description"][:500],
                })
            time.sleep(MIN_INTERVAL)
        except Exception as e:
            print(f"  [WWR] {e}")
    return out


def derive_email_from_company(company):
    """Pick a likely recruiter email for a company using well-known domain patterns.
    Returns None if company is unknown or its domain is in bounce deny list.
    """
    if not company:
        return None
    c = company.strip().lower()
    # Map known companies to their primary domain
    KNOWN_DOMAINS = {
        "dremio": "dremio.com", "glean": "glean.com", "hex technologies": "hex.tech",
        "toggl": "toggl.com", "samsara": "samsara.com", "toptal": "toptal.com",
        "acculynx": "acculynx.com", "twikey": "twikey.com", "tether": "tether.to",
        "tether operations limited": "tether.to", "redmimicry": "redmimicry.com",
        "elman ai": "elman.ai", "ml6": "ml6.ai", "snowflake": "snowflake.com",
        "clipboard": "clipboardhealth.com", "futurefit ai": "futurefit.ai",
        "niuro": "niuro.com", "wheelhouse": "wheelhouse.com", "eazyml": "eazyml.com",
        "crustdata": "crustdata.com", "crossing hurdles": "crossinghurdles.com",
        "airbnb": "airbnb.com", "odyssey consult": "odysseyconsult.com",
        "vida global": "vida.global", "m3 usa": "m3usa.com", "starbridge": "starbridge.io",
        "mira construction": "mira-construction.com", "helloprint": "helloprint.com",
        "jetbrains": "jetbrains.com", "trexquant investment": "trexquant.com",
        "prudential financial": "prudential.com", "crexi": "crexi.com",
        "scale ai": "scale.com", "anthropic": "anthropic.com", "mistral ai": "mistral.ai",
        "cohere": "cohere.com", "perplexity": "perplexity.ai",
        "hugging face": "huggingface.co", "datadog": "datadoghq.com",
        "stripe": "stripe.com", "cloudflare": "cloudflare.com", "vercel": "vercel.com",
        "modal": "modal.com", "replicate": "replicate.com", "together ai": "together.ai",
        "anyscale": "anyscale.com", "lambda": "lambda.ai", "figma": "figma.com",
        "notion": "notion.so", "linear": "linear.app", "supabase": "supabase.io",
        "railway": "railway.app", "render": "render.com", "fly.io": "fly.io",
        "planet": "planet.com", "dbt labs": "getdbt.com", "fivetran": "fivetran.com",
        "hex": "hex.tech", "monte carlo": "montecarlodata.com", "soda": "soda.io",
        "datafold": "datafold.com", "census": "getcensus.com", "hightouch": "hightouch.com",
        "airbyte": "airbyte.com", "dagster": "dagster.io", "prefect": "prefect.io",
        "mage": "mage.ai", "sticker mule": "stickermule.com",
        "edfinity": "edfinity.com", "proxify": "proxify.io", "lemon.io": "lemon.io",
        "stearns nutrition": "stearnsnutrition.com", "steuart nutrition": "stearnsnutrition.com",
        "bjak": "bjak.com", "magic eden": "magic Eden.com", "arango": "arangodb.com",
        "arangodb": "arangodb.com", "mirantis": "mirantis.com", "benzinga": "benzinga.com",
        "the ai whistleblower initiative": "aiwhistleblower.org",
        "physical superintelligence": "physical-intelligence.company",
        "evolve": "evolveinc.com", "clera": "clera.com", "tremendous": "tremendous.com",
        "seahub asia": "seahub.asia", "liberty mutual insurance": "libertymutual.com",
        "tessera labs": "tesseralabs.com", "prenosis": "prenosis.com",
        "siho insurance services": "siho.io",
        "roblox": "roblox.com", "discord": "discord.com", "roboflow": "roboflow.com",
        "labelbox": "labelbox.com", "superannotate": "superannotate.com",
        "encord": "encord.com", "voxel51": "voxel51.com", "arize": "arize.com",
        "fiddler": "fiddler.ai", "whylabs": "whylabs.ai", "langsmith": "langchain.com",
        "weights & biases": "wandb.ai", "wandb": "wandb.ai",
        "comet": "comet.com", "neptune": "neptune.ai", "determined ai": "determined.ai",
        "grid.ai": "determined.ai", "lightning ai": "lightning.ai",
        "tecton": "tecton.ai", "featureform": "featureform.com",
        "hopsworks": "hopsworks.ai", "feast": "feast.dev", "octai": "octai.io",
        "argilla": "argilla.io", "deepgram": "deepgram.com",
        "assemblyai": "assemblyai.com", "speechmatics": "speechmatics.com",
        "elevenlabs": "elevenlabs.io", "playht": "play.ht",
        "resemble ai": "resemble.ai", "descript": "descript.com",
        "runway": "runwayml.com", "pika": "pika.art", "luma": "lumalabs.ai",
        "stability": "stability.ai", "midjourney": "midjourney.com",
        "ideogram": "ideogram.ai", "recraft": "recraft.ai",
        "captions": "captions.com", "submagic": "submagic.co", "heygen": "heygen.com",
        "synthesia": "synthesia.io", "tavus": "tavus.io", "cresta": "cresta.com",
        "asapp": "asapp.com", "polyai": "polyai.io", "sierra": "sierra.ai",
        "decagon": "decagon.ai", "cognigy": "cognigy.com", "rasa": "rasa.com",
        "kore.ai": "kore.ai", "yellow.ai": "yellow.ai", "haptik": "haptik.ai",
        "observe.ai": "observe.ai", "gong": "gong.io", "chorus": "chorus.ai",
        "outreach": "outreach.io", "salesloft": "salesloft.com", "clari": "clari.com",
        "boostup": "boostup.ai", "eliseai": "eliseai.com",
        "moveworks": "moveworks.com", "forethought": "forethought.ai",
        "ada": "ada.cx", "intercom": "intercom.com", "zendesk": "zendesk.com",
        "freshworks": "freshworks.com", "hubspot": "hubspot.com", "salesforce": "salesforce.com",
        "snowflake": "snowflake.com", "databricks": "databricks.com",
        "palantir": "palantir.com", "c3.ai": "c3.ai", "workday": "workday.com",
        "servicenow": "servicenow.com", "twilio": "twilio.com", "okta": "okta.com",
        "auth0": "okta.com", "mongodb": "mongodb.com", "couchbase": "couchbase.com",
        "elastic": "elastic.co", "confluent": "confluent.io", "redis": "redis.com",
        "rabbitmq": "rabbitmq.com", "nats": "nats.io", "pulsar": "pulsar.apache.org",
        "kafka": "kafka.apache.org", "apache": "apache.org",
        "dataiku": "dataiku.com", "datarobot": "datarobot.com",
        "h2o.ai": "h2o.ai", "dataiku": "dataiku.com", "tibco": "tibco.com",
        "informatica": "informatica.com", "talend": "talend.com",
        "collibra": "collibra.com", "alation": "alation.com",
        "trifacta": "alteryx.com", "alteryx": "alteryx.com",
        "tableau": "tableau.com", "looker": "looker.com",
        "thoughtspot": "thoughtspot.com", "sigma": "sigmacomputing.com",
        "mode": "mode.com", "preset": "preset.io", "apache superset": "superset.apache.org",
        "metabase": "metabase.com", "redash": "redash.io",
        "kubeflow": "kubeflow.org", "mlflow": "mlflow.org",
        "argo": "argoproj.github.io", "temporal": "temporal.io",
        "kestra": "kestra.io", "flyte": "flyte.org",
        "bentoml": "bentoml.com", "ray": "ray.io", "anyscale": "anyscale.com",
        "weights and biases": "wandb.ai", "neptune.ai": "neptune.ai",
        # Enterprise & public companies (large — careers@X.com works)
        "jumio": "jumio.com",
        "webflow": "webflow.com",
        "posthog": "posthog.com",
        "figma": "figma.com",
        "qualcomm": "qualcomm.com",
        "oracle": "oracle.com",
        "etsy": "etsy.com",
        "instacart": "instacart.com",
        "thermo fisher scientific": "thermofisher.com",
        "bristol myers squibb": "bms.com",
        "booz allen hamilton": "bah.com",
        "kirkland & ellis": "kirkland.com",
        "bnp paribas": "mabanque.bnpparibas",
        "fis": "fisglobal.com",
        "manulife": "manulife.com",
        "pacific life": "pacificlife.com",
        "american express": "americanexpress.com",
        "aptiv": "aptiv.com",
        "adesso se": "adesso.de",
        "osapiens": "osapiens.com",
        "kainos": "kainos.com",
        "9fin": "9fin.com",
        "permitflow": "permitflow.com",
        "prima": "prima.co",
        "netbrain technologies": "netbrain.com",
        "futurice": "futurice.com",
        "oscar": "hioscar.com",
        "wisdomai": "wisdomai.com",
        "eve": "eve.com",
        "myob": "myob.com",
        "oho group": "ohogroup.com",
        "here technologies": "here.com",
        "doppel": "doppel.com",
        "modjo": "modjo.ai",
        "cander": "cander.io",
        "tala health": "talahealth.io",
        "delta technology hub": "deltatechnologyhub.com",
        "furiosaai": "furiosa.ai",
        "talentgigs": "talentgigs.com",
        "vectovateai": "vectovateai.com",
        "sutra.ai": "sutra.ai",
        "faktion": "faktion.com",
        "space inventive": "spaceinventive.com",
        "wissen technology": "wissentechnology.com",
        "stedi talent solution": "stedi.com.au",
        "jumbo consulting": "jumboconsulting.com",
        "virtusa": "virtusa.com",
        "sii poland": "sii.pl",
        "synechron": "synechron.com",
        "vma": "vma.eu",
        "harrison clarke": "harrisonclarke.co",
        "techwise digital": "techwisedigital.com",
        "code compass": "codecompass.io",
    }
    domain = KNOWN_DOMAINS.get(c)
    if not domain:
        # For unknown companies, try a guess at a primary domain
        slug = re.sub(r"[^a-z0-9]+", "", c)[:20]
        if not slug or len(slug) < 3:
            return None
        # We don't know the TLD; skip rather than guess
        return None
    # Bounce-deny
    reg = ".".join(domain.split(".")[-2:]) if domain.count(".") >= 1 else domain
    if reg in BOUNCE_DENY:
        return None
    return f"careers@{domain}"


def scrape_remoteok():
    out = []
    try:
        data = http_get(SOURCES["remoteok"]["url"],
                        headers={"Accept": "application/json"}).json()
        for item in data[1:]:
            if not isinstance(item, dict):
                continue
            title = item.get("position", "")
            company = item.get("company", "")
            desc = re.sub(r"<[^>]+>", " ", item.get("description", ""))
            url = item.get("url", "")
            if not is_senior_eng(title, desc):
                continue
            em = (extract_email_from_text(desc) or
                  derive_email_from_company(company))
            if not em:
                continue
            out.append({
                "company": company[:80], "role": title[:120], "contact_email": em,
                "source_url": url or f"https://remoteok.com/remote-jobs/{item.get('id', '')}",
                "source": "remoteok",
                "jd_text": desc[:500],
            })
    except Exception as e:
        print(f"  [RemoteOK] {e}")
    return out


def scrape_hnhiring():
    """Fetch hnhiring.com/locations/remote RSS."""
    out = []
    try:
        xml = http_get("https://hnhiring.com/locations/remote").text
        for item in parse_rss(xml):
            if not is_senior_eng(item["title"], item["description"]):
                continue
            co, role = split_company_role(item["title"])
            em = (extract_email_from_text(item["description"]) or
                  derive_email_from_company(co))
            if not em:
                continue
            out.append({
                "company": co, "role": role, "contact_email": em,
                "source_url": item["link"], "source": "hnhiring",
                "jd_text": item["description"][:500],
            })
    except Exception as e:
        print(f"  [HNHiring] {e}")
    return out


def scrape_hn_algolia_24h():
    """Scrape HN stories + comments from the last 24h that mention
    'hiring' alongside AI/ML keywords. Uses the public Algolia HN
    Search API (no auth). Replaces scrape_hnhiring.com (a JS-only SPA
    that returns empty for non-browser clients) and Twitter (Nitter
    is dead, X.com requires paid auth).
    """
    import time as _time
    out = []
    end_ts = int(_time.time())
    begin_ts = end_ts - 24 * 3600
    # Mix of "story" and "comment" queries — many hiring posts are in
    # comments (e.g. Show HN, Ask HN threads).
    queries = [
        ('hiring "machine learning"', 'story'),
        ('hiring AI engineer', 'story'),
        ('"we are hiring" AI', 'story'),
        ('"we are hiring" ML', 'story'),
        ('hiring AI', 'comment'),
        ('hiring "machine learning"', 'comment'),
    ]
    seen_ids: set[str] = set()
    base = "https://hn.algolia.com/api/v1/search_by_date"
    for q, tag in queries:
        try:
            r = requests.get(
                base,
                params={
                    "query": q,
                    "tags": tag,
                    "numericFilters": f"created_at_i>{begin_ts}",
                    "hitsPerPage": 30,
                },
                timeout=12,
                headers={"User-Agent": "AvilxBot/1.0 (leads-pipeline)"},
            )
            if r.status_code != 200:
                continue
            for hit in r.json().get("hits", []):
                oid = hit.get("objectID", "")
                if oid in seen_ids:
                    continue
                seen_ids.add(oid)
                title = (hit.get("title") or hit.get("story_title") or "").strip()
                # For comments, prepend the story title for context
                if not title and hit.get("story_title"):
                    title = hit["story_title"]
                text = hit.get("story_text") or hit.get("comment_text") or title
                if not is_senior_eng(title, text):
                    continue
                # Many HN hiring posts read like "Foo is hiring X engineers"
                # rather than "X at Foo". Handle that pattern.
                m = re.match(r"^([A-Z][\w&.'-]+(?:\s+[A-Z][\w&.'-]+)?)\s+is\s+hiring\b(.*)$",
                             title, re.S)
                if m:
                    co = m.group(1).strip()
                    rest = m.group(2).strip().rstrip(".")
                    # If the rest is empty, fall back to "Engineer"
                    role = rest or "Engineer"
                else:
                    co, role = split_company_role(title)
                # Filter out HN-internal noise that gets through the regex
                if not co or co.lower() in ("unknown", "n/a", ""):
                    # Try to mine from URL
                    url = hit.get("url") or hit.get("story_url") or ""
                    if "://" in url:
                        host = url.split("/")[2].replace("www.", "")
                        co = host.split(".")[0].title()
                co_l = co.lower().strip()
                if any(bad in co_l for bad in (
                    "ask hn", "show hn", "tell hn", "launch hn",
                    "ycombinator", "news.ycombinator", "hn hiring",
                    "mrbeast", "youtube", "tiktok", "twitter",
                )):
                    continue
                # Drop roles that are clearly questions / news headlines
                role_l = (role or "").lower()
                if role_l.startswith(("how ", "what ", "why ", "when ", "where ")):
                    continue
                item_url = hit.get("story_url") or hit.get("url") or ""
                if tag == "comment":
                    item_url = f"https://news.ycombinator.com/item?id={oid}"
                # Try multiple email-derivation strategies
                em = (extract_email_from_text(text) or
                      derive_email_from_company(co) or
                      derive_email(co, item_url))
                if not em:
                    continue
                out.append({
                    "company": co,
                    "role": role or "Engineer",
                    "contact_email": em,
                    "source_url": item_url,
                    "source": f"hn_algolia_24h_{tag}",
                    "jd_text": (text or "")[:500],
                })
        except Exception as e:
            print(f"  [HN-Algolia-24h] {q!r}: {e}")
    return out


# ============================================================
# hnhiring.com — static mirror of "Who is hiring" posts filtered to
# remote roles. Server-rendered HTML (no JS), no auth, ~150 jobs
# per page. Good complement to scrape_hn_algolia_24h: where Algolia
# returns 24h, hnhiring.com returns ~30 days of remote roles.
# ============================================================
HNHIRING_REMOTE_URL = "https://hnhiring.com/locations/remote"


# Pre-compiled patterns used by the hnhiring parser. Kept at module
# scope so the test suite can import them and verify the noise
# filtering directly.
_HNHIRING_NOISE_PREFIX = re.compile(
    r"^(?:Location|Technologies|Remote|Stack|Salary|Apply|"
    r"Full[-\s]?Time|FT|PT|HYBRID|REMOTE):\s*",
    re.I,
)
_HNHIRING_NOISE_PREFIX_ROLE = re.compile(
    r"^(?:Location|Remote|FT|PT|Full[-\s]?Time|"
    r"\$\d|HYBRID|REMOTE|Apply|Technologies):\s*",
    re.I,
)
_HNHIRING_PAREN_DOMAIN = re.compile(r"\s*\([^)]+\)\s*$")


def _parse_pipe_headline(head):
    """Parse a `Company (dom) | Role | FT | Remote | $N` headline.

    Returns (company, role). Tries the pipe-separated format first
    (the most common on hnhiring.com); falls through to
    `split_company_role` for non-pipe headlines. The noise-prefix
    segments (`Location:`, `Stack:`, `FT`, `Remote`, …) are skipped
    so a noisy first segment doesn't get mis-attributed as the
    company.

    Extracted from `scrape_hnhiring_remote` so the test suite can
    exercise the parsing without spinning up a real HTTP request.
    """
    if " | " not in head:
        return split_company_role(head)
    segments = [s.strip() for s in head.split(" | ") if s.strip()]
    co_hint = ""
    role_hint = ""
    for seg in segments[:3]:
        if _HNHIRING_NOISE_PREFIX.match(seg):
            continue
        co_hint = _HNHIRING_PAREN_DOMAIN.sub("", seg).strip()
        if co_hint and len(co_hint) <= 60:
            # Try to take the next non-noise segment as role
            try:
                idx = segments.index(seg)
            except ValueError:
                idx = -1
            if 0 <= idx < len(segments) - 1:
                nxt = segments[idx + 1]
                if not _HNHIRING_NOISE_PREFIX_ROLE.match(nxt):
                    role_hint = nxt
            break
    if co_hint:
        return co_hint, role_hint or "Engineer"
    return split_company_role(head)


# Generic-ATS domains: those mailboxes route to the ATS vendor's
# support team, not a real human at the hiring company. Sending
# cold outreach to `jobs@workable.com` etc. bounces or lands in
# the void, so `scrape_hnhiring_remote` filters them out before
# the row is written. Personal aliases (Gmail, Bridge, …) and the
# company's own domain pass through.
_GENERIC_ATS_DOMAINS = (
    "hnhiring.com",        # the source site itself
    "ashbyhq.com",         # Ashby ATS
    "workable.com",        # Workable ATS
    "greenhouse.io",       # Greenhouse ATS
    "lever.co",            # Lever ATS
    "jobvite.com",         # Jobvite ATS
    "bamboohr.com",        # BambooHR ATS
    "smartrecruiters.com", # SmartRecruiters ATS
    "icims.com",           # iCIMS ATS
    "workday.com",         # Workday ATS
)


def _is_generic_ats_email(email):
    """True if `email` lives on a known ATS-vendor domain.

    The check is case-insensitive and matches the registrable
    domain or any subdomain (e.g. `jobs@mail.workable.com`
    still matches because the registrable domain is
    `workable.com`). We do NOT match `workable.com.au` — only
    the exact domains listed in `_GENERIC_ATS_DOMAINS`, plus
    their subdomains.

    A Gmail address on the same company's block
    (e.g. `recruiter@gmail.com`) returns False — we only filter
    the vendor-domained addresses, not personal aliases.
    """
    if not email or "@" not in email:
        return False
    em_l = email.lower()
    # Split off the local part and walk the domain labels
    # right-to-left, matching any suffix of length 2 or more
    # against the known list. e.g. for "jobs@mail.workable.com":
    #   "workable.com"        → match
    #   "mail.workable.com"   → would also match if it were listed
    # For "alice@stripe.com" → "stripe.com" not in list → False.
    domain = em_l.rsplit("@", 1)[1]
    parts = domain.split(".")
    for i in range(len(parts) - 1):
        candidate = ".".join(parts[i:])
        if candidate in _GENERIC_ATS_DOMAINS:
            return True
    return False


def scrape_hnhiring_remote():
    """Scrape hnhiring.com/locations/remote for senior+ AI/ML/data roles.

    Page is server-rendered HTML — each posting is a <li class="job">.
    No auth, no rate limits observed. Returns [] on any failure.
    """
    out = []
    try:
        r = requests.get(
            HNHIRING_REMOTE_URL,
            timeout=15,
            headers={"User-Agent": "AvilxBot/1.0 (leads-pipeline)"},
        )
        if r.status_code != 200:
            print(f"  [hnhiring] HTTP {r.status_code} — skipping")
            return out
    except Exception as e:
        print(f"  [hnhiring] fetch error: {e}")
        return out

    html = r.text
    # Split on the job list-item wrapper. Each posting is a <li class="job">.
    # Note: the live page emits class="job  " (with trailing whitespace), so
    # accept any number of spaces. Use a non-greedy match to keep each block
    # small, but anchor on the literal closing </li> for that block.
    blocks = re.findall(
        r'<li\s+class="job\s*"[^>]*>(.*?)</li>', html, re.S | re.I
    )
    if not blocks:
        print("  [hnhiring] no <li class='job'> blocks found — markup changed?")
        return out

    for block in blocks:
        # Extract: HN handle, date, body text, first external link
        user_m = re.search(
            r'<a\s+href="https://news\.ycombinator\.com/user\?id=([^"]+)"',
            block, re.I,
        )
        user = user_m.group(1) if user_m else ""
        date_m = re.search(r'class="[^"]*gray[^"]*"[^>]*>(\d{4}-\d{2}-\d{2})',
                           block, re.I)
        post_date = date_m.group(1) if date_m else ""
        body_m = re.search(r'<div\s+class="body"\s*[^>]*>(.*?)</div>\s*</div>',
                           block, re.S | re.I)
        body_html = body_m.group(1) if body_m else block
        # Strip remaining tags
        text = re.sub(r"<[^>]+>", " ", body_html)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        if not is_senior_eng(text[:200], text):
            continue
        # Try the "Foo is hiring X" headline pattern first
        # (text often starts with "Chronograph (chronograph.pe) | Role | FT | ...")
        head = text[:200]
        m = re.match(
            r"^([A-Z][\w&.'-]+(?:\s+[A-Z][\w&.'-]+)?)\s+is\s+hiring\b(.*)$",
            head, re.S,
        )
        if m:
            co = m.group(1).strip()
            role = m.group(2).strip().rstrip(".") or "Engineer"
        else:
            co, role = _parse_pipe_headline(head)
        if not co or co.lower() in ("unknown", "n/a", ""):
            # Fall back to HN handle as a weak signal
            if user:
                co = user.title()
        # Strip trailing punctuation / pipes from sloppy segment splits
        co = co.rstrip(" |:;,.")
        co_l = co.lower().strip()
        if any(bad in co_l for bad in (
            "ask hn", "show hn", "tell hn", "launch hn",
            "ycombinator", "news.ycombinator", "hn hiring",
            "location", "technologies", "remote", "full-time", "full time",
            "senior", "staff", "principal", "lead ",
        )):
            continue
        # Pull first apply link
        link_m = re.search(
            r'<a\s+href="(https?://[^"]+)"', body_html, re.I
        )
        apply_url = link_m.group(1) if link_m else HNHIRING_REMOTE_URL
        em = (extract_email_from_text(text) or
              derive_email_from_company(co) or
              derive_email(co, apply_url))
        if not em:
            continue
        # Skip generic-ATS addresses: those mailboxes route to vendor
        # support teams, not a hiring manager, so the email bounces
        # or lands in the void. Real company emails live on the
        # company's own domain (or a Gmail/Bridge/etc. personal
        # alias), never on the ATS vendor's domain.
        if _is_generic_ats_email(em):
            continue
        out.append({
            "company": co,
            "role": role or "Engineer",
            "contact_email": em,
            "source_url": apply_url,
            "source": f"hnhiring_remote_{post_date}" if post_date else "hnhiring_remote",
            "jd_text": text[:500],
        })
    return out


# ============================================================
# X / Twitter (Playwright with stored auth cookies)
# ============================================================
# Why Playwright + cookies:
#   - X.com returns 403 for unauthenticated requests (verified Dec 2025+)
#   - All Nitter instances are dead
#   - The public GraphQL API requires a guest token (now also 403)
#   - Cookies (auth_token + ct0) let Playwright bypass the login wall
# Setup:
#   1. Log into x.com in a real browser
#   2. Open DevTools → Application → Cookies → https://x.com
#   3. Export auth_token and ct0 as JSON to state/x_cookies.json
#      (template: state/x_cookies.example.json)
#   4. Or set AVILX_X_AUTH_TOKEN and AVILX_X_CT0 env vars
# Cost: ~3s per page render (Playwright launch overhead is the bottleneck)
# Reliability: medium — X occasionally rotates ct0; re-export if you get
#   "Your session has expired" or empty body.

X_COOKIES_PATH = os.getenv(
    "AVILX_X_COOKIES_PATH",
    str(Path(__file__).resolve().parent / "state" / "x_cookies.json"),
)


def _load_x_cookies() -> list[dict] | None:
    """Load X.com auth cookies from file or env. Returns None if missing."""
    # File first
    p = Path(X_COOKIES_PATH)
    if p.exists():
        try:
            with open(p) as f:
                cookies = json.load(f)
            if isinstance(cookies, list) and cookies:
                return cookies
        except Exception as e:
            print(f"  [X.com] failed to read {p}: {e}")
    # Env fallback
    auth = os.getenv("AVILX_X_AUTH_TOKEN")
    ct0 = os.getenv("AVILX_X_CT0")
    if auth and ct0:
        return [
            {"name": "auth_token", "value": auth, "domain": ".x.com",
             "path": "/", "expires": -1, "httpOnly": True, "secure": True,
             "sameSite": "None"},
            {"name": "ct0", "value": ct0, "domain": ".x.com",
             "path": "/", "expires": -1, "httpOnly": False, "secure": True,
             "sameSite": "Lax"},
        ]
    return None


def scrape_x_com():
    """Scrape X.com search for hiring posts (last 24h by default).

    Requires auth cookies. If cookies are missing or invalid, returns
    [] and logs a clear message — does NOT block the loop.
    """
    cookies = _load_x_cookies()
    if not cookies:
        print("  [X.com] no auth cookies — skipping. Set AVILX_X_AUTH_TOKEN + "
              "AVILX_X_CT0 or create state/x_cookies.json")
        return []
    queries = os.getenv(
        "AVILX_X_QUERIES",
        "AI engineer hiring,ML engineer remote,senior AI hiring "
        "china remote hiring,USA remote AI hiring",
    ).split(",")
    queries = [q.strip() for q in queries if q.strip()]
    out: list[dict] = []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [X.com] playwright not installed — run: pip install playwright && playwright install chromium")
        return []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"),
            )
            ctx.add_cookies(cookies)
            page = ctx.new_page()
            for q in queries:
                try:
                    url = ("https://x.com/search?q=" +
                           requests.utils.quote(q) +
                           "&src=typed_query&f=live")
                    page.goto(url, wait_until="domcontentloaded",
                              timeout=30000)
                    # Wait up to 12s for tweets to render
                    try:
                        page.wait_for_selector(
                            'article[data-testid="tweet"]', timeout=12000,
                        )
                    except Exception:
                        # No tweets or session expired
                        body = (page.query_selector("body").inner_text()
                                if page.query_selector("body") else "")
                        if not body or "log in" in body.lower():
                            print(f"  [X.com] {q!r}: session expired or "
                                  "login wall — refresh cookies")
                            break
                        continue
                    articles = page.query_selector_all(
                        'article[data-testid="tweet"]')
                    for art in articles[:25]:
                        try:
                            # Tweet text
                            txt_el = art.query_selector(
                                '[data-testid="tweetText"]')
                            text = (txt_el.inner_text() if txt_el else "").strip()
                            # User handle
                            user_el = art.query_selector(
                                '[data-testid="User-Name"]')
                            user = (user_el.inner_text() if user_el else "").strip()
                            # Tweet permalink
                            link_el = art.query_selector(
                                'a[href*="/status/"]')
                            link = (link_el.get_attribute("href")
                                    if link_el else "")
                            if link and link.startswith("/"):
                                link = "https://x.com" + link
                            if not is_senior_eng(text or "", ""):
                                continue
                            # Try to extract company + role
                            m = re.match(
                                r"^([A-Z][\w&.'-]+(?:\s+[A-Z][\w&.'-]+)?)\s+is\s+hiring\b(.*)$",
                                text, re.S)
                            if m:
                                co = m.group(1).strip()
                                role = m.group(2).strip().rstrip(".") or "Engineer"
                            else:
                                co, role = split_company_role(text)
                            if not co or co.lower() in ("unknown", "n/a", ""):
                                # Try to mine from user handle
                                if user.startswith("@"):
                                    co = user[1:].title()
                            co_l = co.lower().strip()
                            if any(bad in co_l for bad in (
                                "ask x", "ask twitter", "show x", "show twitter",
                                "ycombinator", "x corp", "twitter inc",
                            )):
                                continue
                            em = (extract_email_from_text(text) or
                                  derive_email_from_company(co) or
                                  derive_email(co, link or ""))
                            if not em:
                                continue
                            out.append({
                                "company": co,
                                "role": role or "Engineer",
                                "contact_email": em,
                                "source_url": link or url,
                                "source": "x_com_search",
                                "jd_text": text[:500],
                            })
                        except Exception as e:
                            print(f"  [X.com] article parse error: {e}")
                except Exception as e:
                    print(f"  [X.com] {q!r}: {e}")
            browser.close()
    except Exception as e:
        print(f"  [X.com] playwright error: {e}")
    return out


def scrape_yc_workatastartup():
    out = []
    try:
        xml = http_get(SOURCES["workatastartup"]["url"]).text
        for item in parse_rss(xml):
            if not is_senior_eng(item["title"], item["description"]):
                continue
            m = re.search(r"^(.+?)\s+at\s+(.+?)$", item["title"])
            if m:
                role, co = m.group(1).strip(), m.group(2).strip()
            else:
                co, role = split_company_role(item["title"])
            em = (extract_email_from_text(item["description"]) or
                  derive_email_from_company(co))
            if not em:
                continue
            out.append({
                "company": co, "role": role, "contact_email": em,
                "source_url": item["link"], "source": "workatastartup",
                "jd_text": item["description"][:500],
            })
    except Exception as e:
        print(f"  [YC] {e}")
    return out


def scrape_wellfound():
    out = []
    try:
        xml = http_get(SOURCES["wellfound"]["url"]).text
        for item in parse_rss(xml):
            if not is_senior_eng(item["title"], item["description"]):
                continue
            co, role = split_company_role(item["title"])
            em = (extract_email_from_text(item["description"]) or
                  derive_email_from_company(co))
            if not em:
                continue
            out.append({
                "company": co, "role": role, "contact_email": em,
                "source_url": item["link"], "source": "wellfound",
                "jd_text": item["description"][:500],
            })
    except Exception as e:
        print(f"  [Wellfound] {e}")
    return out


def scrape_hiringcafe():
    out = []
    try:
        xml = http_get(SOURCES["hiringcafe"]["url"]).text
        for item in parse_rss(xml):
            if not is_senior_eng(item["title"], item["description"]):
                continue
            co, role = split_company_role(item["title"])
            em = (extract_email_from_text(item["description"]) or
                  derive_email_from_company(co))
            if not em:
                continue
            out.append({
                "company": co, "role": role, "contact_email": em,
                "source_url": item["link"], "source": "hiring.cafe",
                "jd_text": item["description"][:500],
            })
    except Exception as e:
        print(f"  [HiringCafe] {e}")
    return out


def scrape_cocomby():
    """Cocomby is a curated AI/ML job board. Their jobs page exposes a
    public JSON-ish listing at /jobs. We try the public listings URL
    and parse any structured job links.
    """
    out = []
    urls = [
        "https://cocomby.com/jobs",
        "https://cocomby.com/ai-jobs",
        "https://cocomby.com/remote-jobs",
    ]
    for url in urls:
        try:
            html = http_get(url).text
            # Look for job cards: <a href="/jobs/<slug>">...</a>
            for m in re.finditer(
                r'<a[^>]+href=["\']([^"\']*cocomby\.com/jobs/[^"\']+)["\'][^>]*>(.*?)</a>',
                html, re.S | re.I,
            ):
                link = m.group(1)
                if not link.startswith("http"):
                    link = urljoin(url, link)
                inner = m.group(2)
                # Title is usually inside an <h*> or first text node
                title_m = re.search(r"<h\d[^>]*>(.*?)</h\d>", inner, re.S)
                title = re.sub(r"<[^>]+>", " ", title_m.group(1) if title_m else inner)
                title = unescape(title).strip()[:200]
                if not title or not is_senior_eng(title, ""):
                    continue
                # Co and role
                co, role = split_company_role(title)
                # Cocomby is a job board, not a company — derive company email
                em = (extract_email_from_text(inner) or
                      derive_email_from_company(co))
                if not em:
                    continue
                out.append({
                    "company": co, "role": role, "contact_email": em,
                    "source_url": link, "source": "cocomby",
                    "jd_text": "",
                })
            time.sleep(MIN_INTERVAL)
        except Exception as e:
            print(f"  [Cocomby] {e}")
    return out


SCRAPERS = [
    ("WWR", scrape_weworkremotely),
    ("RemoteOK", scrape_remoteok),
    ("HNHiring", scrape_hnhiring),
    ("HN-Algolia-24h", scrape_hn_algolia_24h),
    ("HNHiring-Remote", scrape_hnhiring_remote),
    ("X.com", scrape_x_com),
    ("YC", scrape_yc_workatastartup),
    ("Wellfound", scrape_wellfound),
    ("HiringCafe", scrape_hiringcafe),
    ("Cocomby", scrape_cocomby),
]


# ============================================================
# DEDUP + INSERT
# ============================================================
def short_id(company, role, email=""):
    """Build a short public tracking id for the email link.

    The id includes the email so two different leads at the same company
    (e.g. (Anyscale, Senior AI Engineer, careers@) vs (Anyscale, Senior
    AI Engineer, talent@) — the latter created by _better_email swap)
    get distinct ids. Without email, both hashes would collide on
    leads_tracking_id_key and the 2nd insert would error.
    """
    h = hashlib.md5(f"{company}|{role}|{email}".encode()).hexdigest()[:6]
    slug = re.sub(r"[^a-z0-9]+", "-", company.lower())[:12].strip("-") or "lead"
    return f"{slug}-{h}"


def insert_leads(leads, dry=False):
    """Insert a batch of leads with role-aware dedup.

    Dedup key: (LOWER(company), LOWER(contact_email), LOWER(role))
    so the same company+recruiter with a *different* role is treated as
    a new lead. Empty role still de-dupes on (company, email) to avoid
    inflating generic backlog rows.
    """
    from db.lead_store import get_cursor
    inserted = 0
    skipped = 0
    errs = 0
    existing = set()
    with get_cursor() as cur:
        cur.execute("""
            SELECT LOWER(company) AS co, LOWER(contact_email) AS em,
                   LOWER(role) AS role
            FROM leads WHERE contact_email IS NOT NULL
        """)
        for r in cur.fetchall():
            existing.add((r["co"] or "", r["em"] or "", r["role"] or ""))

    seen = set()
    for ld in leads:
        co = (ld.get("company") or "").strip()
        em = (ld.get("contact_email") or "").strip()
        role = (ld.get("role") or "").strip()
        if not co or not em or JUNK_EMAIL_RE.search(em) or JUNK_COMPANY_RE.match(co):
            skipped += 1
            continue
        # Generic-ATS catch-all addresses (`jobs@workable.com`,
        # `recruiter@ashbyhq.com`, …) route to the platform's
        # support team, not a real human. Sending cold email
        # to one of these is wasted send budget. We already
        # filter this in scrape_hnhiring_remote, but check
        # again at insert time so a future scraper that
        # forgets the filter doesn't pollute the DB.
        if _is_generic_ats_email(em):
            skipped += 1
            continue
        # Per-domain bounce deny
        try:
            dom = em.split("@", 1)[1].lower()
            reg = ".".join(dom.split(".")[-2:]) if dom.count(".") >= 1 else dom
            if reg in BOUNCE_DENY:
                skipped += 1
                continue
        except Exception:
            pass
        # Role-aware dedup. If role is empty, fall back to (co, em) only.
        key = (co.lower(), em.lower(), role.lower())
        if key in existing or key in seen:
            skipped += 1
            continue
        if dry:
            print(f"  [DRY] would insert {co} {em} {role[:40]}")
            inserted += 1
            seen.add(key)
            continue
        try:
            tid = short_id(co, role, em)
            with get_cursor() as cur:
                cur.execute("""
                    INSERT INTO leads
                        (tracking_id, company, role, contact_email, source_url,
                         jd_text, source, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', NOW(), NOW())
                    ON CONFLICT (LOWER(company), LOWER(contact_email), LOWER(role))
                    WHERE contact_email IS NOT NULL
                      AND role IS NOT NULL
                      AND role != ''
                    DO NOTHING
                    RETURNING id
                """, (tid, co[:80], role[:120], em,
                      ld.get("source_url", "")[:500],
                      (ld.get("jd_text") or "")[:1500],
                      ld.get("source", "auto")))
                row = cur.fetchone()
            if row:
                inserted += 1
                seen.add(key)
                print(f"  ✅ #{row['id']:3d} {co[:30]:30s} {role[:50]:50s} {em}")
            else:
                skipped += 1
        except Exception as e:
            errs += 1
            print(f"  ❌ {co[:30]} {e}")
            # Log full traceback so silent SQL/DB regressions are visible.
            # Without this, a broken ON CONFLICT or schema mismatch would
            # just look like a flood of one-line errors and the operator
            # would have no way to see the underlying cause.
            try:
                _err_log = HERE / "queue_errors.log"
                with open(_err_log, "a") as _ef:
                    _ef.write(f"[{datetime.now().isoformat()}] {co!r} {em!r}\n")
                    _ef.write(traceback.format_exc())
                    _ef.write("\n")
            except Exception:
                pass
    return inserted, skipped, errs


def main():
    print(f"[find_more_leads] {datetime.now().isoformat()}")
    all_leads = []
    for name, fn in SCRAPERS:
        print(f"  scraping {name}...")
        try:
            leads = fn()
            print(f"    -> {len(leads)} candidates")
            all_leads.extend(leads)
        except Exception as e:
            print(f"    -> error: {e}")
        time.sleep(MIN_INTERVAL)
    print(f"[find_more_leads] total {len(all_leads)} candidates")
    ins, skp, err = insert_leads(all_leads, dry=False)
    print(f"[find_more_leads] inserted={ins} skipped={skp} errs={err}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
