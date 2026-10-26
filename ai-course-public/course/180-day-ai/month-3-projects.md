# Month 3: AI + Documents & Search — 30 Days of Hands-On Projects
### Theme: "Make AI understand your company's knowledge"

**Data system:** MongoDB + Elasticsearch + PDFs + Office docs
**Tools:** Python 3.10+, OpenAI, elasticsearch-py, pymongo, pypdf, pdfplumber, unstructured, Tesseract
**Setup time:** 30 min
**Time per project:** 30-90 min
**Total time:** ~28 hours over 30 days

---

## Setup (do this once, before Day 61)

```bash
mkdir ai-daily && cd ai-daily
python -m venv venv && source venv/bin/activate
pip install openai elasticsearch pymongo pypdf pdfplumber unstructured[all-docs] pytesseract Pillow python-dotenv

# Local services via Docker
docker run -d -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" docker.elastic.co/elasticsearch/elasticsearch:8.13.0

docker run -d -p 27017:27017 --name mongo mongo:7

brew install tesseract poppler  # for OCR and PDF→image
```

---

## Day 61: PDF Text Extraction (30 min)

```python
# day61_pdf_extract.py
from pypdf import PdfReader
from pathlib import Path
import re

def extract_text(pdf_path: str) -> dict:
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        # Clean up
        text = re.sub(r'\s+', ' ', text).strip()
        pages.append({"page": i + 1, "text": text, "chars": len(text)})
    return {
        "file": pdf_path,
        "pages": len(reader.pages),
        "total_chars": sum(p["chars"] for p in pages),
        "content": pages,
    }

if __name__ == "__main__":
    result = extract_text("sample.pdf")
    print(f"Pages: {result['pages']}, Total chars: {result['total_chars']}")
    print(f"First page preview: {result['content'][0]['text'][:200]}")
```

**Stretch:** Extract metadata (author, creation date), page-by-page chunking, image extraction.
**Architect note:** `pypdf` is fast but loses formatting; `pdfplumber` preserves layout. For scanned PDFs, you need OCR (Day 63).

---

## Day 62: Word/Excel/PPT Parsing with `unstructured` (45 min)

```python
# day62_unstructured.py
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
import json

def parse_document(file_path: str) -> list[dict]:
    elements = partition(filename=file_path, strategy="auto")
    chunks = chunk_by_title(elements, max_characters=1500, combine_text_under_n_chars=200)
    return [
        {
            "text": c.text,
            "type": type(c).__name__,
            "metadata": dict(c.metadata.to_dict()) if hasattr(c, "metadata") else {},
        }
        for c in chunks
    ]

if __name__ == "__main__":
    chunks = parse_document("quarterly_report.docx")
    for c in chunks[:3]:
        print(f"--- {c['type']} ---")
        print(c["text"][:300])
        print()
```

**Stretch:** Per-element-type handlers (tables → CSV, images → OCR), HTML output, metadata filtering.
**Architect note:** `unstructured` is heavy but it's the most general-purpose doc parser. For a single format, use specialized libs (`python-docx`, `openpyxl`).

---

## Day 63: OCR for Scanned PDFs (45 min)

```python
# day63_ocr_pdf.py
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io

def ocr_pdf(pdf_path: str, lang: str = "eng", dpi: int = 200) -> str:
    images = convert_from_path(pdf_path, dpi=dpi)
    full_text = []
    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img, lang=lang)
        full_text.append(f"\n=== Page {i+1} ===\n{text}")
    return "\n".join(full_text)

def ocr_image(image: Image.Image) -> str:
    return pytesseract.image_to_string(image)

# Demo
text = ocr_pdf("scanned_invoice.pdf")
print(text[:500])
```

**Stretch:** Multi-language OCR (`lang="eng+fra"`), bounding-box output for table extraction, confidence scoring.
**Architect note:** OCR is slow and expensive. Always run a "has text?" check first — `pypdf` is 100× faster than Tesseract for native PDFs.

---

## Day 64: Web Scraping + Chunking (60 min)

```python
# day64_scrape_chunk.py
import httpx
from bs4 import BeautifulSoup
import re
import uuid
from urllib.parse import urljoin, urlparse

def scrape(url: str, max_pages: int = 10) -> list[dict]:
    """Breadth-first scrape starting from `url`."""
    seen, queue, pages = set(), [url], []
    while queue and len(pages) < max_pages:
        url = queue.pop(0)
        if url in seen or urlparse(url).netloc != urlparse(queue[0]).netloc:
            continue
        seen.add(url)
        try:
            r = httpx.get(url, timeout=10, follow_redirects=True)
            r.raise_for_status()
        except Exception:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
        pages.append({"url": url, "text": text})
        for a in soup.find_all("a", href=True):
            queue.append(urljoin(url, a["href"]))
    return pages

def chunk(text: str, target: int = 800, overlap: int = 100) -> list[str]:
    """Sliding window chunking by character count."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + target
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

# Demo
pages = scrape("https://example.com/docs", max_pages=5)
all_chunks = []
for p in pages:
    for c in chunk(p["text"]):
        all_chunks.append({"id": str(uuid.uuid4()), "url": p["url"], "text": c})
print(f"Pages: {len(pages)}, Chunks: {len(all_chunks)}")
```

**Stretch:** robots.txt respect, sitemap.xml-based crawl, JS rendering with Playwright.
**Architect note:** Chunking is the single biggest factor in RAG quality. Bad chunks = bad answers, no matter how good your embedding model is.

---

## Day 65: Sitemap-Based Crawler (45 min)

```python
# day65_sitemap.py
import httpx
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

def get_sitemap_urls(sitemap_url: str) -> list[str]:
    r = httpx.get(sitemap_url, timeout=15)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = []
    for loc in root.findall(".//sm:loc", ns):
        urls.append(loc.text)
    return urls

def get_sitemap_index(domain: str) -> list[str]:
    r = httpx.get(f"{domain}/sitemap.xml", timeout=10)
    if r.status_code != 200:
        return [f"{domain}/sitemap.xml"]
    root = ET.fromstring(r.text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    # sitemapindex has nested sitemaps; urlset has direct urls
    if root.tag.endswith("sitemapindex"):
        return [loc.text for loc in root.findall(".//sm:loc", ns)]
    return [loc.text for loc in root.findall(".//sm:loc", ns)]

if __name__ == "__main__":
    domain = "https://docs.example.com"
    urls = get_sitemap_index(domain)
    print(f"Found {len(urls)} sitemap(s)")
    for sitemap in urls[:1]:
        page_urls = get_sitemap_urls(sitemap)
        print(f"  {sitemap}: {len(page_urls)} pages")
```

**Stretch:** Sitemap diff (find new pages), `<lastmod>` filtering, gzip decompression.
**Architect note:** sitemaps are 10× more polite than crawling — they tell the site owner what you want and respect `crawl-delay` hints.

---

## Day 66: Notion/Confluence Export (45 min)

```python
# day66_notion_confluence.py
import httpx
import os
import json
import time

NOTION = os.environ["NOTION_TOKEN"]
CONFLUENCE = os.environ.get("CONFLUENCE_TOKEN")
CONFLUENCE_BASE = os.environ.get("CONFLUENCE_BASE", "https://yourcompany.atlassian.net")

def export_notion(page_id: str) -> list[dict]:
    """Recursively walk a Notion page tree, return blocks as text."""
    r = httpx.get(
        f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100",
        headers={"Authorization": f"Bearer {NOTION}", "Notion-Version": "2022-06-28"},
    )
    r.raise_for_status()
    out = []
    for b in r.json()["results"]:
        btype = b["type"]
        if btype in ("paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item"):
            text = "".join(t["plain_text"] for t in b[btype].get("rich_text", []))
            if text:
                prefix = {"heading_1": "#", "heading_2": "##", "heading_3": "###"}.get(btype, "")
                out.append({"type": btype, "text": f"{prefix} {text}".strip()})
        elif btype == "child_page":
            out.append({"type": "child_page", "title": b["child_page"]["title"], "id": b["id"]})
            out.extend(export_notion(b["id"]))  # recurse
    return out

def export_confluence(space_key: str) -> list[dict]:
    """Get all pages in a Confluence space via REST API v2."""
    r = httpx.get(
        f"{CONFLUENCE_BASE}/wiki/api/v2/pages",
        params={"space-id": space_key, "limit": 100},
        headers={"Authorization": f"Bearer {CONFLUENCE}"},
    )
    r.raise_for_status()
    pages = []
    for p in r.json()["results"]:
        body = httpx.get(
            f"{CONFLUENCE_BASE}/wiki/api/v2/pages/{p['id']}/body",
            headers={"Authorization": f"Bearer {CONFLUENCE}"},
        ).json()
        pages.append({"id": p["id"], "title": p["title"], "body": body.get("value", "")})
    return pages

# Demo: notional
print(f"Notion blocks: {len(export_notion('your-page-id'))}")
```

**Stretch:** Comment threads, attachments, version history, OAuth vs PAT.
**Architect note:** Notion's rate limit is ~3 req/s; Confluence Cloud is ~10 req/s. Bulk exports need a queue.

---

## Day 67: WEEKEND — Document Ingestion Pipeline (3 hours)

Combine Days 61-66 into a unified ingestion service:
- Watch a folder for new files (PDF/DOCX/PPTX/HTML)
- Auto-detect file type
- Extract text (pypdf / unstructured / OCR fallback)
- Chunk (semantic chunker, target 800 tokens)
- Embed (OpenAI text-embedding-3-small)
- Upsert to Elasticsearch (Day 68 setup)
- Track in SQLite (file → chunks → embeddings)
- CLI: `python ingest.py ./docs/`
- Deploy as a worker (RQ / Arq)

**Architect note:** This is the "ETL of RAG" — and the failure modes (broken PDFs, missing fonts, weird encodings) are why production teams build custom validators per format.

---

## Day 68: Index Documents in Elasticsearch (45 min)

```python
# day68_es_index.py
from elasticsearch import Elasticsearch
import os
from openai import OpenAI
import time

es = Elasticsearch("http://localhost:9200")
client = OpenAI()

INDEX = "documents"

def create_index():
    if es.indices.exists(index=INDEX):
        es.indices.delete(index=INDEX)
    es.indices.create(
        index=INDEX,
        body={
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "body": {"type": "text"},
                    "tags": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 1536,
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
        },
    )

def embed(text: str) -> list[float]:
    return client.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding

def index_doc(doc_id: str, title: str, body: str, tags: list[str] = None):
    es.index(
        index=INDEX,
        id=doc_id,
        document={
            "title": title,
            "body": body,
            "tags": tags or [],
            "created_at": int(time.time() * 1000),
            "embedding": embed(f"{title}\n{body[:1000]}"),
        },
    )

create_index()
for i, t in enumerate(["How to deploy", "API reference", "Troubleshooting guide"]):
    index_doc(f"doc_{i}", t, f"Sample body for {t}", ["docs", f"cat_{i}"])
es.indices.refresh(index=INDEX)
print(f"Indexed, total docs: {es.count(index=INDEX)['count']}")
```

**Stretch:** Bulk API for 100× throughput, async indexing, ILM policy for cold storage.
**Architect note:** `dense_vector` field was added in ES 8.0. Before that, you had to store embeddings as base64 binary and script_score queries.

---

## Day 69: BM25 Keyword Search (30 min)

```python
# day69_bm25.py
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

def search(query: str, size: int = 10) -> list[dict]:
    resp = es.search(
        index="documents",
        body={
            "size": size,
            "query": {
                "match": {"body": {"query": query, "operator": "or"}}
            },
            "highlight": {
                "fields": {"body": {"fragment_size": 150, "number_of_fragments": 2}}
            },
        },
    )
    return [
        {
            "id": h["_id"],
            "score": h["_score"],
            "title": h["_source"]["title"],
            "highlights": h.get("highlight", {}).get("body", []),
        }
        for h in resp["hits"]["hits"]
    ]

for r in search("deployment error"):
    print(f"{r['score']:.2f}  {r['title']}  {' / '.join(r['highlights'])}")
```

**Stretch:** `multi_match` across fields, `query_string` for power users, fuzziness for typos.
**Architect note:** BM25 is the underrated workhorse. For keyword-heavy queries (error codes, product SKUs), it beats every neural model.

---

## Day 70: Multi-Field Search (45 min)

```python
# day70_multi_field.py
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

def search(query: str, size: int = 10) -> list[dict]:
    resp = es.search(
        index="documents",
        body={
            "size": size,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title^3",          # 3x weight
                        "body",
                        "tags^2",
                    ],
                    "type": "best_fields",  # or "most_fields" / "cross_fields"
                    "tie_breaker": 0.3,
                }
            },
        },
    )
    return [{"id": h["_id"], "score": h["_score"], "title": h["_source"]["title"]} for h in resp["hits"]["hits"]]

print(search("kubernetes deployment"))
```

**Stretch:** `function_score` for custom ranking, decay functions for recency boost, per-field analyzers.
**Architect note:** `best_fields` for "find the most relevant single field", `most_fields` for "find docs that match across many fields" (good for tagged content).

---

## Day 71: Faceted Search with Aggregations (45 min)

```python
# day71_facets.py
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

def search_with_facets(query: str, filters: dict = None) -> dict:
    filter_clauses = []
    if filters:
        for field, value in filters.items():
            filter_clauses.append({"term": {field: value}})

    resp = es.search(
        index="documents",
        body={
            "size": 10,
            "query": {
                "bool": {
                    "must": [{"match": {"body": query}}],
                    "filter": filter_clauses,
                }
            },
            "aggs": {
                "by_tag": {"terms": {"field": "tags", "size": 10}},
                "by_month": {
                    "date_histogram": {"field": "created_at", "calendar_interval": "month"}
                },
            },
        },
    )
    return {
        "hits": [h["_source"] for h in resp["hits"]["hits"]],
        "facets": {
            "by_tag": {b["key"]: b["doc_count"] for b in resp["aggregations"]["by_tag"]["buckets"]},
            "by_month": {b["key_as_string"]: b["doc_count"] for b in resp["aggregations"]["by_month"]["buckets"]},
        },
    }

result = search_with_facets("api", filters={"tags": "docs"})
print(f"Hits: {len(result['hits'])}, Facets: {result['facets']}")
```

**Stretch:** Range sliders, multi-select facets, post-filter vs query-time filter.
**Architect note:** `post_filter` runs aggregations on the *pre-filter* set, `filter` runs them on the post-filter set. The difference matters for facet UX.

---

## Day 72: Search Highlighting (30 min)

```python
# day72_highlight.py
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

def search_with_highlights(query: str) -> list[dict]:
    resp = es.search(
        index="documents",
        body={
            "size": 5,
            "query": {"match": {"body": query}},
            "highlight": {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
                "fields": {
                    "body": {
                        "fragment_size": 200,
                        "number_of_fragments": 3,
                        "no_match_size": 0,
                    }
                },
            },
        },
    )
    return [
        {
            "id": h["_id"],
            "title": h["_source"]["title"],
            "fragments": h.get("highlight", {}).get("body", []),
        }
        for h in resp["hits"]["hits"]
    ]

for r in search_with_highlights("error"):
    print(f"\n{r['title']}")
    for f in r["fragments"]:
        print(f"  → {f}")
```

**Stretch:** Unified highlighter (faster, less accurate), `fvh` (fast vector highlighter), sentence-aware splitting.
**Architect note:** Highlighting is *expensive* — for 1000+ results, only highlight top N (e.g., 20) and skip the rest.

---

## Day 73: Search Autocomplete (30 min)

```python
# day73_autocomplete.py
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

# Index with completion suggester field
def setup():
    if es.indices.exists(index="ac"):
        return
    es.indices.create(
        index="ac",
        body={
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "suggest": {"type": "completion"},
                }
            },
        },
    )
    for term in ["how to deploy kubernetes", "how to debug python", "how to write tests",
                 "how to configure nginx", "how to scale redis", "how to monitor prometheus"]:
        es.index(index="ac", document={"title": term, "suggest": {"input": [term]}})

def autocomplete(prefix: str, size: int = 5) -> list[str]:
    resp = es.search(
        index="ac",
        body={"suggest": {"s": {"prefix": prefix, "completion": {"field": "suggest", "size": size}}}},
    )
    return [o["text"] for o in resp["suggest"]["s"][0]["options"]]

setup()
print(autocomplete("how to d"))  # ["how to deploy kubernetes", "how to debug python"]
```

**Stretch:** Fuzzy autocomplete (typo-tolerant), context-based (per-tenant), analytics on query frequency.
**Architect note:** Completion suggester uses an in-memory FST — sub-millisecond, but rebuild cost is O(N) so only use for small dictionaries (<1M terms).

---

## Day 74: WEEKEND — Search UI with Filters (3 hours)

Build a Streamlit search app over the `documents` index:
- Search bar
- Filters: tag, date range, score
- Result list with title, snippet, score
- Pagination
- Highlighted matches
- Save searches per user (SQLite)
- Deploy to Streamlit Cloud

**Architect note:** Search UX is 90% layout. A clean Streamlit page beats a fancy React UI for an internal tool.

---

## Day 75: Embed All Documents (45 min)

```python
# day75_embed_docs.py
from elasticsearch import Elasticsearch
from openai import OpenAI
import time

es = Elasticsearch("http://localhost:9200")
client = OpenAI()

def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed up to 2048 texts in a single API call (saves 99% on calls)."""
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]

def backfill(batch_size: int = 100):
    """Find docs without embeddings and embed them."""
    total = 0
    while True:
        resp = es.search(
            index="documents",
            body={"size": batch_size, "query": {"bool": {"must_not": [{"exists": {"field": "embedding"}}]}}},
        )
        hits = resp["hits"]["hits"]
        if not hits:
            break
        texts = [f"{h['_source']['title']}\n{h['_source']['body'][:1000]}" for h in hits]
        embs = embed_batch(texts)
        for h, e in zip(hits, embs):
            es.update(index="documents", id=h["_id"], doc={"embedding": e})
        total += len(hits)
        print(f"  embedded {total} docs")
        time.sleep(0.5)

backfill()
```

**Stretch:** Async embedding, cost tracking per doc, "needs re-embed" flag for content changes.
**Architect note:** OpenAI's `text-embedding-3-small` allows 2048 inputs per call — use it. Single-doc embedding is 100× slower and costs the same per token.

---

## Day 76: Vector Search in Elasticsearch (45 min)

```python
# day76_vector_search.py
from elasticsearch import Elasticsearch
from openai import OpenAI

es = Elasticsearch("http://localhost:9200")
client = OpenAI()

def vector_search(query: str, k: int = 10) -> list[dict]:
    qvec = client.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding
    resp = es.search(
        index="documents",
        body={
            "size": k,
            "knn": {
                "field": "embedding",
                "query_vector": qvec,
                "k": k,
                "num_candidates": 100,  # higher = more accurate, slower
            },
            "source": ["title", "body", "tags"],
        },
    )
    return [
        {"id": h["_id"], "score": h["_score"], "title": h["_source"]["title"]}
        for h in resp["hits"]["hits"]
    ]

for r in vector_search("how do I make my service more reliable"):
    print(f"{r['score']:.3f}  {r['title']}")
```

**Stretch:** Filtered kNN (combine with `filter` clause), `k` vs `num_candidates` trade-off tuning.
**Architect note:** `num_candidates` is the HNSW `ef` parameter. Higher = more accurate at higher latency. 100 is a good default; 1000 for precision-critical.

---

## Day 77: Hybrid BM25 + Vector (60 min)

```python
# day77_hybrid.py
from elasticsearch import Elasticsearch
from openai import OpenAI

es = Elasticsearch("http://localhost:9200")
client = OpenAI()

def hybrid_search(query: str, k: int = 10, bm25_weight: float = 0.5) -> list[dict]:
    qvec = client.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding
    vector_weight = 1.0 - bm25_weight
    resp = es.search(
        index="documents",
        body={
            "size": k,
            "query": {
                "match": {"body": {"query": query, "boost": bm25_weight * 10}}
            },
            "knn": {
                "field": "embedding",
                "query_vector": qvec,
                "k": k,
                "num_candidates": 100,
                "boost": vector_weight * 10,
            },
        },
    )
    return [
        {"id": h["_id"], "score": h["_score"], "title": h["_source"]["title"]}
        for h in resp["hits"]["hits"]
    ]

for r in hybrid_search("kubernetes pod restart loop"):
    print(f"{r['score']:.3f}  {r['title']}")
```

**Stretch:** Reciprocal Rank Fusion (RRF), per-query weight tuning, learned weights via click data.
**Architect note:** ES 8.8+ supports RRF natively (`"rank": {"rrf": {...}}`) — better than manual score fusion because it normalizes across systems.

---

## Day 78: Re-Ranking with Cohere (45 min)

```python
# day78_rerank.py
import os
import httpx
from typing import Callable

def cohere_rerank(query: str, documents: list[str], top_n: int = 5) -> list[dict]:
    r = httpx.post(
        "https://api.cohere.ai/v1/rerank",
        headers={"Authorization": f"Bearer {os.environ['COHERE_API_KEY']}"},
        json={
            "model": "rerank-english-v3.0",
            "query": query,
            "documents": documents,
            "top_n": top_n,
        },
    )
    r.raise_for_status()
    return r.json()["results"]

# Use after a hybrid search
from day77_hybrid import hybrid_search  # hypothetical
candidates = hybrid_search("how to debug a memory leak", k=20)
texts = [c["title"] for c in candidates]  # in real use, get the actual body
reranked = cohere_rerank("how to debug a memory leak", texts, top_n=5)
for r in reranked:
    print(f"{r['relevance_score']:.3f}  {texts[r['index']]}")
```

**Stretch:** Multi-stage re-ranking (BM25 → vector → cross-encoder), A/B test with/without reranker.
**Architect note:** Re-rankers (Cohere, bge-reranker) are slow and expensive. Always re-rank a small candidate set (10-50), never the full corpus.

---

## Day 79: Query Understanding (60 min)

```python
# day79_query_understand.py
import json
from openai import OpenAI

client = OpenAI()

def understand(query: str) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""Analyze this search query. Return JSON:
{{
  "intent": "informational|navigational|transactional|troubleshooting",
  "entities": ["..."],   // technical terms, product names, error codes
  "expanded": ["..."],    // synonyms and related terms
  "filters": {{ "tags": "...", "date": "..." }},  // implicit filters
  "rewrite": "...",        // cleaned/expanded version
  "should_answer_directly": true
}}
Query: "{query}"
"""}],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)

print(json.dumps(understand("why is my python script OOM-killed on kubernetes"), indent=2))
```

**Stretch:** Spell-check, entity linking, multi-intent detection, click prediction.
**Architect note:** Query understanding rarely helps simple queries — it shines on ambiguous or malformed queries. A/B test ruthlessly.

---

## Day 80: Personalized Ranking (60 min)

```python
# day80_personalized.py
from openai import OpenAI
import json

client = OpenAI()

def personalize(query: str, user_history: list[dict], candidates: list[dict]) -> list[dict]:
    """Re-rank candidates based on user's past interactions."""
    history_text = "\n".join(
        f"- clicked: {h.get('title', '')} (tags: {h.get('tags', [])})" for h in user_history[-20:]
    )
    cand_text = "\n".join(f"{i}. {c['title']} (tags: {c.get('tags', [])})" for i, c in enumerate(candidates))
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""Re-rank these search results for the user.

User history:
{history_text}

Query: {query}

Candidates:
{cand_text}

Return JSON: {{"ranking": [3, 0, 5, 1, 2, 4], "reasoning": "..."}}
"""}],
        response_format={"type": "json_object"},
    )
    result = json.loads(resp.choices[0].message.content)
    return [candidates[i] for i in result["ranking"]]

# Demo
candidates = [
    {"id": 0, "title": "Python OOM debugging", "tags": ["python", "k8s"]},
    {"id": 1, "title": "Java GC tuning", "tags": ["java"]},
    {"id": 2, "title": "Kubernetes pod limits", "tags": ["k8s"]},
]
history = [{"title": "Python OOM in production", "tags": ["python", "k8s"]}]
for c in personalize("memory leak in production", history, candidates):
    print(c["title"])
```

**Stretch:** Embedding-based personalization, multi-armed bandit for explore/exploit, privacy-preserving.
**Architect note:** Personalization can hurt diversity. Always include some "explore" slots (10-20% of results).

---

## Day 81: WEEKEND — Search Quality Evaluation (3 hours)

Build a search quality harness:
- 30+ labeled queries with expected results
- Metrics: nDCG@10, MRR, recall@20
- Compare BM25, vector, hybrid, hybrid+rerank
- Track over time in a results table
- Generate weekly quality report

**Architect note:** Search quality is the difference between "users find things" and "users complain." A 2% nDCG improvement is a 10% business improvement.

---

## Day 82: RAG with Citations (60 min)

```python
# day82_rag_citations.py
from elasticsearch import Elasticsearch
from openai import OpenAI

es = Elasticsearch("http://localhost:9200")
client = OpenAI()

def retrieve(query: str, k: int = 5) -> list[dict]:
    qvec = client.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding
    resp = es.search(
        index="documents",
        body={
            "size": k,
            "knn": {"field": "embedding", "query_vector": qvec, "k": k, "num_candidates": 50},
        },
    )
    return [
        {
            "id": h["_id"],
            "title": h["_source"]["title"],
            "body": h["_source"]["body"],
            "score": h["_score"],
        }
        for h in resp["hits"]["hits"]
    ]

def answer(query: str) -> dict:
    docs = retrieve(query)
    context = "\n\n".join(
        f"[{i+1}] {d['title']}\n{d['body'][:500]}" for i, d in enumerate(docs)
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""Answer using ONLY the numbered sources. Cite like [1], [2]. If the answer is not in the sources, say "I don't know."

{context}"""},
            {"role": "user", "content": query},
        ],
    )
    return {"answer": resp.choices[0].message.content, "sources": docs}

result = answer("How do I configure TLS on the API server?")
print(result["answer"])
print("\nSources:")
for s in result["sources"]:
    print(f"  [{s['id']}] {s['title']} (score: {s['score']:.2f})")
```

**Stretch:** Inline citation parsing, clickable citation links, citation-accuracy eval.
**Architect note:** "I don't know" is the most important behavior in RAG. A model that confidently hallucinates is worse than a model that says "I don't know."

---

## Day 83: Conversational RAG (60 min)

```python
# day83_conversational_rag.py
from day82_rag_citations import retrieve
from openai import OpenAI

client = OpenAI()

def answer_with_history(question: str, history: list[dict]) -> dict:
    # Step 1: rewrite question with context
    if history:
        rewrite = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Rewrite the user's question as a standalone question, resolving any references to prior conversation. Return only the rewritten question."},
                *history,
                {"role": "user", "content": question},
            ],
        ).choices[0].message.content
    else:
        rewrite = question

    # Step 2: retrieve using the rewritten question
    docs = retrieve(rewrite)

    # Step 3: answer with history
    context = "\n\n".join(f"[{i+1}] {d['title']}\n{d['body'][:500]}" for i, d in enumerate(docs))
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Answer with citations. Use chat history for context.\n\nSources:\n{context}"},
            *history,
            {"role": "user", "content": question},
        ],
    )
    return {"answer": resp.choices[0].message.content, "rewrite": rewrite, "sources": docs}

history = []
for q in ["What is the API rate limit?", "And how do I increase it?"]:
    r = answer_with_history(q, history)
    print(f"Q: {q}\nA: {r['answer']}\n")
    history.extend([{"role": "user", "content": q}, {"role": "assistant", "content": r["answer"]}])
```

**Stretch:** Condensed history (summarize old turns), entity tracking, session-based retrieval.
**Architect note:** Question rewriting is the cheapest and most effective conversational trick. Re-retrieving with the rewritten question gives 30% better results.

---

## Day 84: Multi-Hop RAG (60 min)

```python
# day84_multihop.py
from day82_rag_citations import retrieve
from openai import OpenAI
import json

client = OpenAI()

def multihop(question: str, max_hops: int = 3) -> dict:
    """Decompose a complex question into sub-questions, answer each, then synthesize."""
    plan = json.loads(client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""Decompose this question into 1-3 sub-questions that can be answered independently. Return JSON: {{"sub_questions": ["...", "..."]}}

Question: {question}"""}],
        response_format={"type": "json_object"},
    ).choices[0].message.content)

    intermediate = []
    for sub in plan["sub_questions"][:max_hops]:
        docs = retrieve(sub, k=3)
        ans = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Answer based on these docs.\n\n{chr(10).join(d['body'][:500] for d in docs)}\n\nQuestion: {sub}"}],
        ).choices[0].message.content
        intermediate.append({"sub_q": sub, "answer": ans, "sources": docs})

    final = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""Original question: {question}

Sub-answers:
{chr(10).join(f'Q: {i["sub_q"]}\\nA: {i["answer"]}' for i in intermediate)}

Synthesize a final answer. Cite the sub-question numbers."""}],
    )
    return {"answer": final.choices[0].message.content, "intermediate": intermediate}

print(multihop("What does the API rate limit depend on, and how do I check it?")["answer"])
```

**Stretch:** DAG-based decomposition, parallel sub-question answering, answer verification.
**Architect note:** Multi-hop is 3-5x more expensive but answers questions BM25/vector cannot. Use it for complex questions only.

---

## Day 85: Streaming RAG Responses (45 min)

```python
# day85_streaming_rag.py
from day82_rag_citations import retrieve
from openai import OpenAI

client = OpenAI()

def stream_answer(question: str):
    docs = retrieve(question)
    context = "\n\n".join(f"[{i+1}] {d['title']}\n{d['body'][:500]}" for i, d in enumerate(docs))
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        stream=True,
        messages=[
            {"role": "system", "content": f"Answer with citations. Sources:\n{context}"},
            {"role": "user", "content": question},
        ],
    )
    print("Answer: ", end="", flush=True)
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()

stream_answer("How do I configure TLS?")
```

**Stretch:** Server-Sent Events (SSE) over FastAPI, citation streaming after first chunk, token-by-token UI.
**Architect note:** Streaming cuts perceived latency from 3s to 0.5s. Always stream in a chat UI.

---

## Day 86: RAG Evaluation with RAGAS (45 min)

```bash
pip install ragas datasets
```

```python
# day86_ragas_eval.py
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset
from day82_rag_citations import answer

# Test set: (question, ground_truth)
test = [
    {"question": "How do I configure TLS?", "ground_truth": "Edit the tls section in config.yaml and set cert_path and key_path."},
    {"question": "What's the rate limit?", "ground_truth": "1000 requests per minute per API key."},
    # ... more
]

records = []
for t in test:
    r = answer(t["question"])
    records.append({
        "question": t["question"],
        "answer": r["answer"],
        "contexts": [s["body"] for s in r["sources"]],
        "ground_truth": t["ground_truth"],
    })

ds = Dataset.from_list(records)
result = evaluate(ds, metrics=[faithfulness, answer_relevancy, context_precision, context_recall])
print(result)
```

**Stretch:** Track metrics over time, alert on regression, per-intent metrics.
**Architect note:** RAGAS is a "starting point" metric suite. For production, build domain-specific metrics (legal accuracy, code correctness, etc.).

---

## Day 87: RAG Observability with LangSmith (45 min)

```bash
pip install langsmith
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=<your-key>
export LANGCHAIN_PROJECT=ai-daily-rag
```

```python
# day87_langsmith.py
from langsmith import traceable
from day82_rag_citations import retrieve
from openai import OpenAI

client = OpenAI()

@traceable(name="rag_pipeline", tags=["month3", "rag"])
def answer_traced(question: str) -> str:
    docs = retrieve(question)  # automatically traced
    context = "\n\n".join(f"[{i+1}] {d['body'][:500]}" for i, d in enumerate(docs))
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": f"Answer with citations.\n{context}"},
                  {"role": "user", "content": question}],
    )
    return resp.choices[0].message.content

answer_traced("How do I deploy?")
```

**Stretch:** Custom evaluators in LangSmith, dataset-backed regression tests, cost tracking.
**Architect note:** LangSmith is the easiest way to debug RAG. The "trace" view shows exactly which docs were retrieved for each question.

---

## Day 88: WEEKEND — RAG Cost Optimization (3 hours)

Profile and optimize a RAG system:
- Measure: cost per query, latency, retrieval precision
- Tries: smaller embedding model, smaller chunk size, fewer retrieved docs, prompt compression, smaller LLM
- Pick the best (cost × quality) Pareto point
- Document the trade-offs in a blog post

**Architect note:** RAG cost = embedding cost + LLM cost. Embedding is the bigger lever at scale (re-embeddable, cacheable). LLM cost matters per query.

---

## Day 89: Polish + Load Test (60 min)

Take the search service from Days 68-87:
- Add k6 or Locust load test
- 100 RPS, p99 latency target
- Cache embeddings
- Async embedding for bulk ingest
- Health check endpoint
- README with runbook

**Architect note:** A 100 RPS RAG system needs ~3-4 LLM API keys and 5-10 Elasticsearch shards. Plan capacity before launch.

---

## Day 90: MONTH PROJECT — Customer Support AI (6 hours)

**Goal:** AI that answers questions over 10K+ support tickets.

**Spec:**
- Ingest 10K+ tickets (Zendesk / Intercom / CSV export)
- Embed with `text-embedding-3-small`
- Index in Elasticsearch with hybrid search
- Conversational RAG with history
- Web UI (Streamlit) + REST API (FastAPI)
- Analytics: most-asked questions, resolution rate
- 5 beta users (your team)
- Deploy to Fly.io

**Architect note:** This is "the killer RAG app" — every company has support tickets, and a 30% deflection rate is a $100K+ win.

---

## Month 3 Summary

**Built:** 30 projects · 1 document ingestion pipeline · 1 search service · 1 RAG app
**Time:** ~28 hours over 30 days
**Cost:** ~$15 in API + cloud fees

**Key skills learned:**
- Document parsing (PDF, DOCX, OCR)
- Elasticsearch (BM25, vector, hybrid, aggregations)
- RAG patterns (citations, multi-hop, conversational)
- Evaluation (RAGAS, nDCG)
- Observability (LangSmith)

**Next:** Month 4 — AI + Files & Media. 30 projects on S3, Whisper, DALL-E, GPT-4V, video processing.
