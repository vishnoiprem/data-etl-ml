#!/usr/bin/env python3
"""
find_clients.py — Find direct-client leads (companies that may need a CTO,
AI pod, or Build-Deploy-Engineers team), not job-board listings.

Strategy:
  1. Look for "we're hiring our first CTO / first AI engineer" signals
     via Google-style queries (Bing + DuckDuckGo HTML).
  2. Scan YC Work at a Startup for "Founding Engineer" / "First Hire" roles.
  3. Scan IndieHackers for "looking for technical cofounder" / "AI build".
  4. Pull from a curated list of "AI-native companies that recently raised"
     that are now scaling teams and need senior help.

Output: leads with `apply_method='email'` and the same derive-email flow
as find_more_leads.py. Inserts into Postgres.

Run:  python3 find_clients.py
"""

import json
import re
import sys
import time
import secrets
import hashlib
from pathlib import Path
from html import unescape
from urllib.parse import urlparse, quote_plus

import requests

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from find_more_leads import (
    UA, TIMEOUT, MIN_INTERVAL, BOUNCE_DENY, JUNK_EMAIL_RE, JUNK_COMPANY_RE,
    AI_DATA_TERMS, is_senior_eng, split_company_role,
    extract_email_from_text, derive_email_from_company,
    http_get, parse_rss, short_id,
)


# ============================================================
# 1. Bing search for "first CTO / founding engineer" signals
# ============================================================
BING_QUERIES = [
    '"we are hiring our first CTO" AI',
    '"first AI engineer" startup remote',
    '"founding engineer" AI/ML',
    '"we are looking for a CTO" AI startup',
    '"hiring our first" data engineer AI startup',
    '"staff+ AI engineer" "build the team"',
    '"build-deploy-engineers" OR "build deploy engineers" pod',
    '"AI pod" OR "AI engineering pod" OR "AI delivery pod"',
    '"looking for AI co-founder" OR "looking for technical co-founder" AI',
    '"we are building an AI team" remote',
]


def search_bing(query, max_results=15):
    """Lightweight Bing HTML scrape — no API key needed."""
    out = []
    try:
        url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
        html = http_get(url, headers={"Accept-Language": "en-US,en;q=0.9"}).text
        # Bing's organic results: <li class="b_algo">
        for m in re.finditer(r'<li class="b_algo".*?</li>', html, re.S | re.I):
            block = m.group(0)
            title_m = re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
            if not title_m:
                continue
            link = title_m.group(1)
            title = re.sub(r"<[^>]+>", " ", title_m.group(2)).strip()
            title = unescape(title)[:200]
            # Skip Bing's own properties
            if "bing.com" in link or "microsoft.com" in link:
                continue
            out.append({"title": title, "link": link,
                        "description": ""})  # we can fetch descriptions on demand
    except Exception as e:
        print(f"  [Bing] {e}")
    return out


# ============================================================
# 2. HN "Who is hiring?" latest thread
# ============================================================
def scrape_hn_who_is_hiring():
    """Fetch the latest Ask HN: Who is hiring? thread and parse top comments."""
    out = []
    try:
        # Get the latest thread ID. Firebase HN endpoint is generous but a
        # 1-askstories + 30-items + 60-kids loop is ~91 requests in a tight
        # burst — sleep between to stay well under any IP-based rate limit.
        r = http_get("https://hacker-news.firebaseio.com/v0/askstories.json")
        ids = r.json()[:30]
        for sid in ids:
            time.sleep(MIN_INTERVAL)
            item = http_get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json").json()
            if not item:
                continue
            title = (item.get("title") or "").lower()
            if "who is hiring" not in title:
                continue
            # Found a hiring thread — pull its top-level comments
            kids = item.get("kids", [])
            print(f"  [HN] thread: {item.get('title')} ({len(kids)} comments)")
            for kid in kids[:60]:  # cap
                try:
                    time.sleep(MIN_INTERVAL)
                    c = http_get(f"https://hacker-news.firebaseio.com/v0/item/{kid}.json").json()
                    if not c or c.get("deleted") or c.get("dead"):
                        continue
                    txt = (c.get("text") or "")
                    if not txt:
                        continue
                    # Strip HTML, decode entities
                    txt_clean = re.sub(r"<[^>]+>", " ", txt)
                    txt_clean = unescape(txt_clean).strip()
                    # Extract title from first line
                    first_line = txt_clean.split("\n", 1)[0].strip()
                    first_line = re.sub(r"^>\s*", "", first_line)
                    if not first_line or not is_senior_eng(first_line, txt_clean):
                        continue
                    # HN comments usually start with "Company | Role | Location | ..."
                    parts = [p.strip() for p in first_line.split("|")]
                    if len(parts) >= 2:
                        co, role = parts[0], parts[1]
                    else:
                        co, role = split_company_role(first_line)
                    if not co or not role:
                        continue
                    # Get the comment URL
                    hn_url = f"https://news.ycombinator.com/item?id={kid}"
                    em = (extract_email_from_text(txt_clean) or
                          derive_email_from_company(co))
                    if not em:
                        continue
                    out.append({
                        "company": co[:80], "role": role[:120], "contact_email": em,
                        "source_url": hn_url, "source": "hn_whoishiring",
                        "jd_text": txt_clean[:500],
                    })
                except Exception:
                    continue
            break  # only the latest thread
    except Exception as e:
        print(f"  [HN] {e}")
    return out


# ============================================================
# 3. YC Work at a Startup: "Founding Engineer" filter
# ============================================================
def scrape_yc_founding_roles():
    """Hit the WaaS founding-roles RSS feed."""
    out = []
    urls = [
        "https://www.workatastartup.com/roles.rss?role=founding-engineer",
        "https://www.workatastartup.com/jobs.rss",
    ]
    for url in urls:
        try:
            xml = http_get(url, headers={"Accept": "application/rss+xml, */*"}).text
            for item in parse_rss(xml):
                title = item["title"]
                # Founding roles often have "Founding" or "First" in the title
                if not is_senior_eng(title, item["description"]):
                    continue
                m = re.search(r"^(.+?)\s+at\s+(.+?)$", title)
                if m:
                    role, co = m.group(1).strip(), m.group(2).strip()
                else:
                    co, role = split_company_role(title)
                em = (extract_email_from_text(item["description"]) or
                      derive_email_from_company(co))
                if not em:
                    continue
                out.append({
                    "company": co, "role": role, "contact_email": em,
                    "source_url": item["link"], "source": "yc_founding",
                    "jd_text": item["description"][:500],
                })
            time.sleep(MIN_INTERVAL)
        except Exception as e:
            print(f"  [YC founding] {e}")
    return out


# ============================================================
# 4. Curated list of "AI-native recently-funded" companies
# (Updated: October 2026, AI/infra/data tooling)
# ============================================================
CURATED_AI_NATIVE = [
    {"company": "Anysphere", "role": "AI Engineer (Cursor)", "domain": "anysphere.com",
     "jd_text": "Cursor AI code editor team hiring engineers to build AI-native IDE features."},
    {"company": "Codeium", "role": "AI Engineer", "domain": "codeium.com",
     "jd_text": "AI code completion platform hiring senior engineers to scale inference."},
    {"company": "Cognition AI", "role": "AI Engineer (Devin)", "domain": "cognition.ai",
     "jd_text": "Devin AI software engineer team hiring senior AI/platform engineers."},
    {"company": "Factory AI", "role": "Senior AI Engineer", "domain": "factory.ai",
     "jd_text": "AI coding agents team hiring senior engineers to ship autonomous dev agents."},
    {"company": "Braintrust", "role": "Senior AI Engineer", "domain": "braintrust.dev",
     "jd_text": "AI evals + observability platform hiring senior engineers."},
    {"company": "Sierra", "role": "Senior AI Engineer", "domain": "sierra.ai",
     "jd_text": "Conversational AI for enterprises hiring senior AI engineers."},
    {"company": "Decagon", "role": "Senior AI Engineer", "domain": "decagon.ai",
     "jd_text": "AI customer support agents hiring senior engineers."},
    {"company": "Glean", "role": "Senior AI Engineer", "domain": "glean.com",
     "jd_text": "Enterprise search + AI hiring senior engineers."},
    {"company": "Hebbia", "role": "Senior AI Engineer", "domain": "hebbia.com",
     "jd_text": "AI for finance & law hiring senior engineers."},
    {"company": "Writer", "role": "Senior AI Engineer", "domain": "writer.com",
     "jd_text": "Enterprise LLMs platform hiring senior AI engineers."},
    {"company": "Harvey", "role": "Senior AI Engineer", "domain": "harvey.ai",
     "jd_text": "Legal AI platform hiring senior engineers."},
    {"company": "EvenUp", "role": "Senior AI Engineer", "domain": "evenup.ai",
     "jd_text": "Legal AI for personal injury hiring senior engineers."},
    {"company": "Ironclad", "role": "Senior AI Engineer", "domain": "ironcladapp.com",
     "jd_text": "Contract AI platform hiring senior engineers."},
    {"company": "Casetext", "role": "Senior AI Engineer", "domain": "casetext.com",
     "jd_text": "Legal AI (acquired by Thomson Reuters) hiring senior engineers."},
    {"company": "Eve", "role": "Senior AI Engineer", "domain": "eve.com",
     "jd_text": "Legal practice platform hiring senior engineers."},
    {"company": "Spellbook", "role": "Senior AI Engineer", "domain": "spellbook.legal",
     "jd_text": "AI for lawyers hiring senior engineers."},
    {"company": "Lavender", "role": "Senior AI Engineer", "domain": "lavender.ai",
     "jd_text": "AI sales email coach hiring senior engineers."},
    {"company": "Regie.ai", "role": "Senior AI Engineer", "domain": "regie.ai",
     "jd_text": "AI sales platform hiring senior engineers."},
    {"company": "Clay", "role": "Senior Data Engineer", "domain": "clay.com",
     "jd_text": "Data-driven outbound hiring senior data engineers."},
    {"company": "Attio", "role": "Senior AI Engineer", "domain": "attio.com",
     "jd_text": "AI-native CRM hiring senior engineers."},
    {"company": "Folk", "role": "Senior Data Engineer", "domain": "folk.app",
     "jd_text": "Modern CRM hiring senior data engineers."},
    {"company": "Tavus", "role": "Senior AI Engineer", "domain": "tavus.io",
     "jd_text": "AI video personalization hiring senior engineers."},
    {"company": "HeyGen", "role": "Senior AI Engineer", "domain": "heygen.com",
     "jd_text": "AI video generation hiring senior engineers."},
    {"company": "Synthesia", "role": "Senior AI Engineer", "domain": "synthesia.io",
     "jd_text": "AI avatar video platform hiring senior engineers."},
    {"company": "ElevenLabs", "role": "Senior AI Engineer", "domain": "elevenlabs.io",
     "jd_text": "Voice AI platform hiring senior engineers."},
    {"company": "PlayHT", "role": "Senior AI Engineer", "domain": "play.ht",
     "jd_text": "AI voice generation hiring senior engineers."},
    {"company": "Deepgram", "role": "Senior AI Engineer", "domain": "deepgram.com",
     "jd_text": "Speech AI platform hiring senior engineers."},
    {"company": "AssemblyAI", "role": "Senior AI Engineer", "domain": "assemblyai.com",
     "jd_text": "Speech-to-text AI hiring senior engineers."},
    {"company": "Runway", "role": "Senior AI Engineer", "domain": "runwayml.com",
     "jd_text": "Creative AI tools hiring senior engineers."},
    {"company": "Pika", "role": "Senior AI Engineer", "domain": "pika.art",
     "jd_text": "AI video generation hiring senior engineers."},
    {"company": "Luma", "role": "Senior AI Engineer", "domain": "lumalabs.ai",
     "jd_text": "AI video / 3D hiring senior engineers."},
    {"company": "Stability", "role": "Senior AI Engineer", "domain": "stability.ai",
     "jd_text": "Open-source generative AI hiring senior engineers."},
    {"company": "Midjourney", "role": "Senior AI Engineer", "domain": "midjourney.com",
     "jd_text": "AI image generation hiring senior engineers."},
    {"company": "Ideogram", "role": "Senior AI Engineer", "domain": "ideogram.ai",
     "jd_text": "AI image generation hiring senior engineers."},
    {"company": "Recraft", "role": "Senior AI Engineer", "domain": "recraft.ai",
     "jd_text": "AI design tool hiring senior engineers."},
    {"company": "Captions", "role": "Senior AI Engineer", "domain": "captions.com",
     "jd_text": "AI video editing hiring senior engineers."},
    {"company": "Submagic", "role": "Senior AI Engineer", "domain": "submagic.co",
     "jd_text": "AI short-form video hiring senior engineers."},
    {"company": "Descript", "role": "Senior AI Engineer", "domain": "descript.com",
     "jd_text": "AI video/audio editing hiring senior engineers."},
    {"company": "Resemble AI", "role": "Senior AI Engineer", "domain": "resemble.ai",
     "jd_text": "Voice cloning AI hiring senior engineers."},
    {"company": "Cresta", "role": "Senior AI Engineer", "domain": "cresta.com",
     "jd_text": "Contact center AI hiring senior engineers."},
    {"company": "ASAPP", "role": "Senior AI Engineer", "domain": "asapp.com",
     "jd_text": "AI for customer service hiring senior engineers."},
    {"company": "PolyAI", "role": "Senior AI Engineer", "domain": "polyai.io",
     "jd_text": "Voice AI for enterprise hiring senior engineers."},
    {"company": "Cognigy", "role": "Senior AI Engineer", "domain": "cognigy.com",
     "jd_text": "Conversational AI platform hiring senior engineers."},
    {"company": "Rasa", "role": "Senior AI Engineer", "domain": "rasa.com",
     "jd_text": "Open-source conversational AI hiring senior engineers."},
    {"company": "Kore.ai", "role": "Senior AI Engineer", "domain": "kore.ai",
     "jd_text": "Enterprise AI agents hiring senior engineers."},
    {"company": "Yellow.ai", "role": "Senior AI Engineer", "domain": "yellow.ai",
     "jd_text": "Conversational AI platform hiring senior engineers."},
    {"company": "Haptik", "role": "Senior AI Engineer", "domain": "haptik.ai",
     "jd_text": "Conversational AI hiring senior engineers."},
    {"company": "Observe.AI", "role": "Senior AI Engineer", "domain": "observe.ai",
     "jd_text": "AI for contact centers hiring senior engineers."},
    {"company": "Gong", "role": "Senior AI Engineer", "domain": "gong.io",
     "jd_text": "Revenue intelligence AI hiring senior engineers."},
    {"company": "Chorus", "role": "Senior AI Engineer", "domain": "chorus.ai",
     "jd_text": "Conversation intelligence hiring senior engineers."},
    {"company": "Outreach", "role": "Senior AI Engineer", "domain": "outreach.io",
     "jd_text": "Sales engagement AI hiring senior engineers."},
    {"company": "Salesloft", "role": "Senior AI Engineer", "domain": "salesloft.com",
     "jd_text": "Sales engagement platform hiring senior engineers."},
    {"company": "Clari", "role": "Senior AI Engineer", "domain": "clari.com",
     "jd_text": "Revenue platform AI hiring senior engineers."},
    {"company": "BoostUp", "role": "Senior AI Engineer", "domain": "boostup.ai",
     "jd_text": "Revenue intelligence hiring senior engineers."},
    {"company": "Moveworks", "role": "Senior AI Engineer", "domain": "moveworks.com",
     "jd_text": "Enterprise AI for IT support hiring senior engineers."},
    {"company": "Forethought", "role": "Senior AI Engineer", "domain": "forethought.ai",
     "jd_text": "AI for customer support hiring senior engineers."},
    {"company": "Ada", "role": "Senior AI Engineer", "domain": "ada.cx",
     "jd_text": "AI customer service platform hiring senior engineers."},
    {"company": "Intercom", "role": "Senior AI Engineer", "domain": "intercom.com",
     "jd_text": "AI customer service platform hiring senior engineers (Fin AI)."},
    {"company": "Zendesk", "role": "Senior AI Engineer", "domain": "zendesk.com",
     "jd_text": "Customer service AI hiring senior engineers."},
    {"company": "HubSpot", "role": "Senior AI Engineer", "domain": "hubspot.com",
     "jd_text": "CRM + AI features (ChatSpot) hiring senior engineers."},
    {"company": "Salesforce", "role": "Senior AI Engineer (Einstein)", "domain": "salesforce.com",
     "jd_text": "Einstein AI platform hiring senior engineers."},
    {"company": "Palantir", "role": "Senior AI Engineer (AIP)", "domain": "palantir.com",
     "jd_text": "AIP (AI Platform) for enterprise hiring senior engineers."},
    {"company": "C3.ai", "role": "Senior AI Engineer", "domain": "c3.ai",
     "jd_text": "Enterprise AI applications hiring senior engineers."},
    {"company": "ServiceNow", "role": "Senior AI Engineer", "domain": "servicenow.com",
     "jd_text": "Now Assist AI hiring senior engineers."},
    {"company": "Workday", "role": "Senior AI Engineer", "domain": "workday.com",
     "jd_text": "Workday AI features hiring senior engineers."},
    {"company": "Twilio", "role": "Senior AI Engineer", "domain": "twilio.com",
     "jd_text": "Twilio AI / CustomerAI hiring senior engineers."},
    {"company": "MongoDB", "role": "Senior AI Engineer", "domain": "mongodb.com",
     "jd_text": "MongoDB AI features (Atlas Vector Search) hiring senior engineers."},
    {"company": "Elastic", "role": "Senior AI Engineer", "domain": "elastic.co",
     "jd_text": "Elastic AI Assistant hiring senior engineers."},
    {"company": "Confluent", "role": "Senior Data Engineer", "domain": "confluent.io",
     "jd_text": "Kafka + Flink hiring senior data engineers."},
    {"company": "Redis", "role": "Senior AI Engineer", "domain": "redis.com",
     "jd_text": "Redis AI features hiring senior engineers."},
    {"company": "Dataiku", "role": "Senior AI Engineer", "domain": "dataiku.com",
     "jd_text": "Enterprise AI/ML platform hiring senior engineers."},
    {"company": "DataRobot", "role": "Senior AI Engineer", "domain": "datarobot.com",
     "jd_text": "Enterprise AI platform hiring senior engineers."},
    {"company": "H2O.ai", "role": "Senior AI Engineer", "domain": "h2o.ai",
     "jd_text": "Open-source GenAI platform hiring senior engineers."},
    {"company": "Weights & Biases", "role": "Senior AI Engineer", "domain": "wandb.ai",
     "jd_text": "MLOps platform hiring senior engineers."},
    {"company": "Comet", "role": "Senior AI Engineer", "domain": "comet.com",
     "jd_text": "MLOps platform hiring senior engineers."},
    {"company": "Neptune", "role": "Senior AI Engineer", "domain": "neptune.ai",
     "jd_text": "ML metadata store hiring senior engineers."},
    {"company": "Determined AI", "role": "Senior AI Engineer", "domain": "determined.ai",
     "jd_text": "AI training platform hiring senior engineers."},
    {"company": "Lightning AI", "role": "Senior AI Engineer", "domain": "lightning.ai",
     "jd_text": "PyTorch Lightning + Studio hiring senior engineers."},
    {"company": "Modal", "role": "Senior AI Engineer", "domain": "modal.com",
     "jd_text": "Serverless GPU runtime hiring senior engineers."},
    {"company": "Replicate", "role": "Senior AI Engineer", "domain": "replicate.com",
     "jd_text": "Open-source model inference hiring senior engineers."},
    {"company": "Together AI", "role": "Senior AI Engineer", "domain": "together.ai",
     "jd_text": "Distributed AI training/inference hiring senior engineers."},
    {"company": "Anyscale", "role": "Senior AI Engineer", "domain": "anyscale.com",
     "jd_text": "Ray platform hiring senior engineers."},
    {"company": "Lambda", "role": "Senior AI Engineer", "domain": "lambda.ai",
     "jd_text": "GPU cloud + training hiring senior engineers."},
    {"company": "Tecton", "role": "Senior AI Engineer", "domain": "tecton.ai",
     "jd_text": "Feature platform hiring senior engineers."},
    {"company": "Featureform", "role": "Senior Data Engineer", "domain": "featureform.com",
     "jd_text": "Feature store for ML hiring senior engineers."},
    {"company": "Hopsworks", "role": "Senior AI Engineer", "domain": "hopsworks.ai",
     "jd_text": "Feature store + MLOps hiring senior engineers."},
    {"company": "Feast", "role": "Senior Data Engineer", "domain": "feast.dev",
     "jd_text": "Open-source feature store hiring senior engineers."},
    {"company": "Arize", "role": "Senior AI Engineer", "domain": "arize.com",
     "jd_text": "ML observability platform hiring senior engineers."},
    {"company": "Fiddler", "role": "Senior AI Engineer", "domain": "fiddler.ai",
     "jd_text": "Responsible AI platform hiring senior engineers."},
    {"company": "WhyLabs", "role": "Senior AI Engineer", "domain": "whylabs.ai",
     "jd_text": "AI observability hiring senior engineers."},
    {"company": "Gantry", "role": "Senior AI Engineer", "domain": "gantry.io",
     "jd_text": "ML observability + eval hiring senior engineers."},
    {"company": "Voxel51", "role": "Senior AI Engineer", "domain": "voxel51.com",
     "jd_text": "FiftyOne open-source ML data hiring senior engineers."},
    {"company": "Labelbox", "role": "Senior AI Engineer", "domain": "labelbox.com",
     "jd_text": "Data labeling platform hiring senior engineers."},
    {"company": "Scale AI", "role": "Senior AI Engineer", "domain": "scale.com",
     "jd_text": "Data labeling + evaluation hiring senior engineers."},
    {"company": "Roboflow", "role": "Senior AI Engineer", "domain": "roboflow.com",
     "jd_text": "Computer vision platform hiring senior engineers."},
    {"company": "SuperAnnotate", "role": "Senior AI Engineer", "domain": "superannotate.com",
     "jd_text": "Data annotation platform hiring senior engineers."},
    {"company": "Encord", "role": "Senior AI Engineer", "domain": "encord.com",
     "jd_text": "Data-centric AI platform hiring senior engineers."},
    {"company": "Argilla", "role": "Senior AI Engineer", "domain": "argilla.io",
     "jd_text": "Open-source data labeling hiring senior engineers."},
    {"company": "LangChain", "role": "Senior AI Engineer", "domain": "langchain.com",
     "jd_text": "LLM framework hiring senior engineers."},
    {"company": "LlamaIndex", "role": "Senior AI Engineer", "domain": "llamaindex.ai",
     "jd_text": "LLM data framework hiring senior engineers."},
    {"company": "Pinecone", "role": "Senior AI Engineer", "domain": "pinecone.io",
     "jd_text": "Vector database hiring senior engineers."},
    {"company": "Weaviate", "role": "Senior AI Engineer", "domain": "weaviate.io",
     "jd_text": "Open-source vector DB hiring senior engineers."},
    {"company": "Chroma", "role": "Senior AI Engineer", "domain": "trychroma.com",
     "jd_text": "Embeddings database hiring senior engineers."},
    {"company": "Qdrant", "role": "Senior AI Engineer", "domain": "qdrant.tech",
     "jd_text": "Vector search engine hiring senior engineers."},
    {"company": "Vespa", "role": "Senior AI Engineer", "domain": "vespa.ai",
     "jd_text": "AI search platform hiring senior engineers."},
    {"company": "Marqo", "role": "Senior AI Engineer", "domain": "marqo.ai",
     "jd_text": "Vector search for AI hiring senior engineers."},
]


def emit_curated():
    """Emit the curated AI-native list as leads."""
    out = []
    for c in CURATED_AI_NATIVE:
        dom = c["domain"]
        if ".".join(dom.split(".")[-2:]) in BOUNCE_DENY:
            continue
        out.append({
            "company": c["company"], "role": c["role"],
            "contact_email": f"careers@{dom}",
            "source_url": f"https://{dom}/careers",
            "source": "curated_ai_native",
            "jd_text": c["jd_text"],
        })
    return out


# ============================================================
# MAIN
# ============================================================
def main():
    print(f"[find_clients] {__import__('datetime').datetime.now().isoformat()}")
    all_leads = []

    # 1. Curated AI-native (always emit)
    curated = emit_curated()
    print(f"  [curated] {len(curated)} AI-native companies")
    all_leads.extend(curated)

    # 2. HN Who is hiring
    print("  [HN Who is hiring]")
    hn = scrape_hn_who_is_hiring()
    print(f"    -> {len(hn)} candidates")
    all_leads.extend(hn)
    time.sleep(MIN_INTERVAL)

    # 3. YC founding roles
    print("  [YC founding]")
    yc = scrape_yc_founding_roles()
    print(f"    -> {len(yc)} candidates")
    all_leads.extend(yc)
    time.sleep(MIN_INTERVAL)

    # 4. Bing search for "first CTO" / founding signals
    print("  [Bing searches]")
    for q in BING_QUERIES:
        results = search_bing(q, max_results=8)
        for r in results:
            if not is_senior_eng(r["title"], ""):
                continue
            co, role = split_company_role(r["title"])
            em = derive_email_from_company(co) or extract_email_from_text(r["description"])
            if not em:
                continue
            all_leads.append({
                "company": co, "role": role, "contact_email": em,
                "source_url": r["link"], "source": "bing",
                "jd_text": r["description"][:500],
            })
        time.sleep(MIN_INTERVAL)

    print(f"[find_clients] total {len(all_leads)} candidates")
    from find_more_leads import insert_leads
    ins, skp, err = insert_leads(all_leads, dry=False)
    print(f"[find_clients] inserted={ins} skipped={skp} errs={err}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
