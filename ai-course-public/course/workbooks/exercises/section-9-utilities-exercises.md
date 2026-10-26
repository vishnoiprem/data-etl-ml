# Codebook Exercises — Section 9: Common Utilities

> **Paired exercises for [`../ai-engineer-codebook.md` § 9](../ai-engineer-codebook.md#section-9-common-utilities).**
> These turn reference snippets into active practice. For each reference snippet in the codebook, here are 3-5 challenges that force you to modify, extend, and break the code.

---

## How to use these

1. Open the reference snippet in [`../ai-engineer-codebook.md`](../ai-engineer-codebook.md) — Section 9 (Utilities)
2. Read the snippet once
3. Do the exercises below IN ORDER — each builds on the previous
4. For each exercise, build the utility, run it on real data, note what you learned

**Time per exercise:** 25-40 min.
**Total time for this section:** 5-7 hours.

---

## Snippet 9.1 — Text Splitter

**Reference:** [`../ai-engineer-codebook.md#91-text-splitter`](../ai-engineer-codebook.md#91-text-splitter)

### Exercise 9.1.1: Compare splitters

```python
# TODO: Split the same 100-page book with 4 splitters:
# - Fixed-token (every 1000 tokens)
# - Sentence-boundary (every N sentences)
# - Paragraph-boundary (every paragraph)
# - Semantic (split where topic changes)
# For each: measure chunk count, average size, retrieval quality on 20 questions.
```

### Exercise 9.1.2: Overlap tuning

```python
# TODO: For fixed-token chunking, test overlap = 0, 100, 200, 500, 1000.
# Plot: retrieval recall@5 vs overlap. Cost = linearly with overlap.
# Find the sweet spot.
```

### Exercise 9.1.3: Markdown-aware splitter

```python
# TODO: Build a splitter that respects markdown structure:
# - Don't split inside a code block
# - Prefer splits at H2 / H3 boundaries
# - Keep tables together
# - Don't orphan headings (heading should be with its content)
# Test on a long markdown doc.
```

### Exercise 9.1.4: Streaming splitter

```python
# TODO: For a 10GB file, don't load it all in memory.
# Stream chunks of 10MB, split each, yield chunks.
# Use case: indexing Wikipedia, Common Crawl, SEC filings.
```

---

## Snippet 9.2 — PDF Loader

**Reference:** [`../ai-engineer-codebook.md#92-pdf-loader`](../ai-engineer-codebook.md#92-pdf-loader)

### Exercise 9.2.1: Multi-library fallback

```python
# TODO: Try pypdf first. If it returns empty (scanned PDF), try PyMuPDF.
# If still empty, fall back to OCR (tesseract or AWS Textract).
# Build a loader that returns the best available extraction.
# Test on 10 PDFs: some digital, some scanned, some mixed.
```

### Exercise 9.2.2: Page-aware extraction

```python
# TODO: For RAG, you need page numbers (for citations).
# Use pypdf or PyMuPDF to get text per page.
# Then split per page, then within page.
# Store: {page, text, page_number} metadata for each chunk.
# Verify: citations point to the correct page.
```

### Exercise 9.2.3: Table extraction

```python
# TODO: PDFs have tables. Naive extraction produces garbage.
# Use camelot-py or tabula-py to extract tables as DataFrames.
# For each table, render to markdown for the LLM.
# Test on a financial report with 20+ tables.
```

### Exercise 9.2.4: Image extraction

```python
# TODO: Extract images from a PDF.
# For each image: save to disk, embed with CLIP, store in vector DB.
# Now your RAG can find "the diagram showing the architecture".
# Test on a technical PDF with figures.
```

### Exercise 9.2.5: Speed

```python
# TODO: Time the loading of a 500-page PDF.
# pypdf: ~10s
# PyMuPDF: ~2s
# Parallelize across pages: ~0.5s
# At what scale do you need parallelism?
```

---

## Snippet 9.3 — Web Scraper

**Reference:** [`../ai-engineer-codebook.md#93-web-scraper`](../ai-engineer-codebook.md#93-web-scraper)

### Exercise 9.3.1: Robust extraction

```python
# TODO: Build a scraper that:
# - Uses trafilatura for main content (not BeautifulSoup + heuristics)
# - Falls back to readability-lxml
# - Strips nav, footer, ads, scripts
# - Returns {title, body, published_date, author, images: []}
# Test on 20 news articles. Measure: clean text, no nav residue.
```

### Exercise 9.3.2: Polite scraping

```python
# TODO: Add:
# - User-Agent string
# - Respect robots.txt (use robotexclusionrulesparser)
# - Rate limit: 1 request / 2s per domain
# - Retry with exponential backoff on 429/5xx
# - Skip if robots.txt says no
# This is what ethical scrapers do.
```

### Exercise 9.3.3: Concurrent scraper

```python
# TODO: Scrape 100 URLs in parallel.
# Use httpx.AsyncClient with concurrency limit (10).
# Measure: total time (10x faster), error rate.
# Add: progress callback, error log.
```

### Exercise 9.3.4: Handle JS-rendered pages

```python
# TODO: Some sites render content with JavaScript.
# Plain httpx gets the shell, not the content.
# Use Playwright or Selenium for those.
# Decision tree: try plain httpx first; if body is < 500 chars, fall back to Playwright.
# Measure: how many sites need JS rendering?
```

### Exercise 9.3.5: Extract structured data

```python
# TODO: From a product page, extract:
# - title, price, rating, reviews, images, specs
# Use CSS selectors or XPath. Save as JSON.
# Test on 5 e-commerce sites.
```

---

## Snippet 9.4 — Async Queue with Celery

**Reference:** [`../ai-engineer-codebook.md#94-async-queue-with-celery`](../ai-engineer-codebook.md#94-async-queue-with-celery)

### Exercise 9.4.1: Replace synchronous with async

```python
# TODO: You have a /upload endpoint that processes files synchronously.
# Move the processing to a Celery task.
# - POST /upload returns 202 + task_id
# - Client polls GET /upload/:task_id for status
# - Or use WebSocket / SSE for push
# Measure: how much faster is the API? How much can you scale?
```

### Exercise 9.4.2: Retry policy

```python
# TODO: For a task that calls an external API:
# - auto_retry=True
# - max_retries=3
# - retry_backoff=True (exponential)
# - retry_jitter=True
# Test: kill the external API. Watch Celery retry.
```

### Exercise 9.4.3: Dead letter queue

```python
# TODO: After max_retries, send the task to a "failed" queue.
# - Don't drop the task silently
# - Log + alert
# - Provide a way to retry from the dead letter queue
# This is "graceful failure" — you don't lose data, you just delay it.
```

### Exercise 9.4.4: Priority queues

```python
# TODO: Some tasks are more urgent than others.
# - high: real-time user requests
# - normal: background processing
# - low: bulk imports, evals
# Configure 3 Celery queues. Route by task type.
# Verify: high-priority tasks jump the line.
```

### Exercise 9.4.5: Celery vs alternatives

```python
# Compare:
# - Celery: battle-tested, complex, lots of features
# - RQ: simpler, Redis-only, fewer features
# - Dramatiq: middle ground
# - Arq: async-native
# - Cloud-native: AWS SQS, GCP Pub/Sub, Azure Service Bus
# When to use which?
```

---

## Cross-cutting challenges (Mid+)

### Challenge A: Build a complete RAG indexer

```python
# TODO: A production-grade indexer:
# 1. Upload (S3, with multipart)
# 2. Extract (PDF, DOCX, HTML, MD, code files)
# 3. Clean (remove nav, footers, boilerplate)
# 4. Split (semantic, with overlap)
# 5. Embed (batched, with retry)
# 6. Upsert (Pinecone, with backoff)
# 7. Status updates (user can see progress)
# Run on a 1000-doc corpus. Measure: time, cost, error rate.
```

### Challenge B: Multi-source RAG

```python
# TODO: Index from multiple sources:
# - PDFs (uploaded by user)
# - Websites (user provides a URL list)
# - Notion / Google Docs / Confluence (API integration)
# - S3 bucket (user-owned)
# Unified interface: each source has an "extractor" + "uploader".
```

### Challenge C: Cost-optimized indexing

```python
# TODO: For 1M documents:
# - Re-embed only changed docs (skip unchanged via hash)
# - Use smaller embedding model for low-priority docs
# - Batch embeddings (100 per call, 10x faster)
# - Cache embeddings in Postgres (don't re-embed the same text)
# Measure: cost reduction.
```

---

## Architect-level reflections (Senior+)

After completing these exercises, write a 1-page design doc answering:

1. **Text splitter of choice?** (size, overlap, semantic vs fixed)
2. **PDF loader strategy?** (library, fallback, OCR for scanned)
3. **Web scraper ethics?** (robots.txt, rate limits, attribution)
4. **JS rendering?** (Playwright, when worth the cost)
5. **Queue system?** (Celery, RQ, cloud-native SQS)
6. **Async-first?** (every long task should be async)
7. **Retry policy?** (max retries, backoff, jitter)
8. **Dead letter handling?** (don't drop data, just delay)
9. **Priority queues?** (when, why)
10. **Cost per million docs indexed?** (embeddings + storage + compute)

Save these answers. The plumbing is what makes or breaks an AI product.

---

## What's next

- Pair with [`../../practice/level-9-utilities/`](../../practice/level-9-utilities/) for the deeper labs
- Move to `section-10-cheatsheets-exercises.md` for model selection + pricing
- See [`../../PRACTICE-GUIDE.md`](../../PRACTICE-GUIDE.md) for the full learning path