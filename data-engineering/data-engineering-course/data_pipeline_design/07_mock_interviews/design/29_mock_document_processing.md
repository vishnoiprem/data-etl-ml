# 29 — Mock Interview: Design a Document Processing Pipeline

> **Lesson 29 of 30 — Mock Interviews**

A full 30-minute mock interview transcript with a candidate
designing a document processing pipeline. The candidate is
a Senior Data Engineer (L5 level) at a hypothetical loop
modeled on the canonical question in
`docs/reference/de_interview_canonical_questions.md`.

---

## Setup

**Company:** Mid-sized SaaS (hypothetical).
**Role:** Senior Data Engineer.
**Level:** L5.
**Format:** 30-minute system design round, on-site whiteboard.
**Question:** *"Design a pipeline to ingest user-uploaded
documents (PDF, DOCX, images), extract structured data, and
make the content searchable. Volume: 5M documents per month,
average 2 MB each, 200-character average extracted text per
document, and a mix of structured (forms) and unstructured
(contracts) content."*

---

## Transcript (30 minutes)

### 0:00 — Opening framing

> **Candidate:** Before I draw, let me make sure I understand
> the problem. You said 5M documents per month — that's
> ~170K per day, ~2 per second average, with peaks maybe 10
> per second. Is that right?
>
> And the documents — what's the format mix? PDF, DOCX,
> scanned images? Are the scanned images OCR-able (i.e.
> typed text in the image) or are they handwritten?
>
> And the consumer — when you say "make searchable," do you
> mean full-text search (like Elasticsearch), or do you mean
> extract specific fields (like invoice number, total, date)
> for structured queries?

> **Interviewer:** Mix is 60% PDF, 25% DOCX, 15% scanned
> images. The scanned images are typed, not handwritten —
> standard OCR works. The consumer is both: full-text search
> for everything, plus extracted fields for invoices and
> contracts.

> **Candidate:** Great. So we have a mixed-mode pipeline:
> OCR for images, native text extraction for PDFs and DOCX,
> and a separate field-extraction step for structured
> documents. Two output stores: an Elasticsearch index for
> full-text search, and a Postgres table for extracted
> fields. The deep dive is the OCR + extraction stage.

### 3:00 — High-level architecture

> **Candidate:** Let me draw. **[DRAWING 1]**

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│ User       │───►│ Upload API │───►│ S3 landing │───►│ SQS / Kafka │
│ (browser)  │    │ (presigned │    │ (raw bytes)│    │ (queue)     │
│            │    │  URL POST) │    │            │    │            │
└────────────┘    └────────────┘    └────────────┘    └─────┬──────┘
                                                            │
                                                            ▼
                                                     ┌────────────┐
                                                     │ Worker pool│
                                                     │ (Python)   │
                                                     │            │
                                                     │ 1. OCR /   │
                                                     │    extract │
                                                     │ 2. NLP /   │
                                                     │    fields  │
                                                     │ 3. write   │
                                                     │    ES + DB │
                                                     └─────┬──────┘
                                                           │
                                          ┌────────────────┴────────────┐
                                          ▼                             ▼
                                   ┌────────────┐                ┌────────────┐
                                   │ Elastic   │                │ Postgres   │
                                   │ search    │                │ (fields)   │
                                   └────────────┘                └────────────┘
```

> **Candidate:** Five boxes. Upload API takes the file, writes
> to S3 with a presigned URL, and enqueues a message. Workers
> pull from the queue, run OCR + extraction, write to ES and
> Postgres. The hot path is the worker — that's where the
> latency, the failure modes, and the cost live.

### 6:00 — Back-of-envelope estimation

> **Candidate:** Sizing: 5M documents / month × 2 MB = 10 TB
> raw per month, 120 TB per year. That's modest — S3 standard
> is $30/month per TB, so $300/month for raw storage. The
> extracted text is much smaller — 5M × 200 chars × 1 byte
> = 1 GB. Even with 5x storage overhead for ES indexes, that's
> 5 GB. So storage is not the cost driver.
>
> The cost driver is the worker pool. At 170K docs/day with
> a 5-second p95 processing time, we need 170K × 5 sec /
> 86400 sec = 10 workers minimum. To handle 10x peak, I'd
> size for 50-100 workers, each on a small EC2 instance or
> container. At $50/instance/month, that's $2.5K-$5K/month.

### 8:00 — The deep dive: the worker

> **Interviewer:** Walk me through the worker. What does it
> do, step by step?

> **Candidate:** Six steps. **[DRAWING 2]**

```
1. Poll SQS for a new message
   { "doc_id": "abc-123", "s3_key": "raw/2024/01/15/abc-123.pdf",
     "format": "pdf", "doc_type": "invoice" }
   ↓
2. Download from S3
   ↓
3. Route by format:
     PDF:    extract text with pdfplumber, fallback OCR
     DOCX:   extract with python-docx
     IMAGE:  OCR with Textract or Tesseract
   ↓
4. Run field extraction (if doc_type is invoice/contract):
     - Regex for known patterns (invoice #, date, total)
     - Or a small ML model for variable layouts
   ↓
5. Write to ES (full-text) and Postgres (extracted fields)
   ↓
6. Mark the message complete; SQS deletes the message
```

> **Candidate:** The format router is the first decision:
> PDF text is usually selectable, so pdfplumber is fast
> (100ms). If pdfplumber returns empty, the PDF is
> scanned, so we fall back to OCR. DOCX is python-docx,
> straightforward. Images go straight to Textract. The
> average time is 1-3 seconds per document.
>
> Field extraction is the second decision. For invoices
> with a known layout, regex patterns work (invoice number
> is `INV-\d{6}`, total is `Total: \$[\d,]+\.\d{2}`). For
> variable layouts, we'd use a small layout-aware model —
> LayoutLMv3, or AWS Textract's "forms" feature. The model
> call adds 2-5 seconds.

### 14:00 — The DLQ and idempotency

> **Interviewer:** What happens when OCR fails? Or when the
> model is unsure about a field?

> **Candidate:** Three failure modes. **[DRAWING 3]**

```
                  ┌────────────┐
                  │ Worker     │
                  │            │
                  └─────┬──────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐
   │ Success │    │ Retry   │    │ DLQ     │
   │ (write  │    │ (queue  │    │ (human  │
   │  to ES) │    │  again) │    │  review)│
   └─────────┘    └─────────┘    └─────────┘
```

> **Candidate:** Success — write to ES and Postgres, mark
> the SQS message complete.
>
> Retry — transient failures (S3 timeout, ES 5xx). The
> worker has exponential backoff: 1s, 2s, 4s, 8s, 16s.
> After 5 retries, the message goes to the DLQ. The DLQ
> is a separate SQS queue; a human reviews it once a day.
>
> DLQ — non-transient failures: corrupt PDF, OCR confidence
> too low, no fields extracted when fields were expected.
> These need human review. We track DLQ depth as a metric;
> if it's growing, something systemic is wrong.
>
> Idempotency is the third concern. The `doc_id` is the
> idempotency key. The ES write uses `doc_id` as the
> document id; the Postgres write uses `INSERT ... ON
> CONFLICT (doc_id) DO UPDATE`. A re-run of the same
> message is a no-op.

### 19:00 — The search side

> **Interviewer:** How does the user search?

> **Candidate:** The user types a query in the search bar.
> The frontend sends the query to a search API, which
> queries Elasticsearch with a multi-match across
> `title`, `body_text`, and `extracted_fields`. ES returns
> the top N documents with snippets. **[DRAWING 4]**

```
Search API:
  POST /search
  { "q": "invoice ACME 2024", "filters": { "doc_type": "invoice" } }

  ES query:
  {
    "query": {
      "bool": {
        "must": [
          { "multi_match": { "query": "invoice ACME 2024",
                             "fields": ["title^2", "body_text"] } }
        ],
        "filter": [
          { "term": { "doc_type": "invoice" } }
        ]
      }
    },
    "highlight": { "fields": { "body_text": {} } }
  }
```

> **Candidate:** The search is a multi-match across text
> fields with a `doc_type` filter. The filter is a
> structured query (Postgres could do this too, but ES is
> faster for text). The highlight returns snippets with
> the matched terms in bold.
>
> The deep dive on the search side is the relevance
> tuning: how do we rank an invoice match higher than a
> contract match for the query "ACME invoice 2024"?
> That's TF-IDF + a doc_type boost. The interview answer
> for "relevance" is a separate conversation; in this
> pipeline I'd start with multi-match + doc_type boost
> and tune from search logs.

### 23:00 — Schema evolution and the contract

> **Interviewer:** What happens when the field-extraction
> model changes? Or when the document format changes?

> **Candidate:** Two scenarios. **[DRAWING 5]**
>
> First, the model changes. We version the model output
> the same way we version the schema: every extracted
> field has a `model_version` field. Old documents keep
> their old version; new documents get the new version.
> Re-extraction is opt-in (a backfill job, not on the
> hot path).
>
> Second, the document format changes. The format router
> has a fallback: if pdfplumber returns empty (new PDF
> variant), we fall back to OCR. The OCR result is the
> same shape as the text extraction, so downstream
> doesn't care.
>
> The contract test: a sample document of each known
> type is in the test suite. On every deploy, we run
> the worker against the sample and assert the
> extracted fields match the expected output. A
> regression in extraction blocks the deploy.

### 27:00 — Failure modes

> **Interviewer:** Five things that can go wrong, please.

> **Candidate:** Five failure modes. **[DRAWING 6]**
>
> One, S3 is down. The worker can't download. Retry
> with backoff; if S3 is down for >5 minutes, the
> DLQ depth grows and we page on-call.
>
> Two, ES is down. The worker can't write the search
> index. We write to a backup S3 path first, then
> asynchronously load to ES when it's back. The
> Postgres write is independent.
>
> Three, the OCR service is rate-limited. Textract has
> a 100 req/sec default. We use a token bucket; if
> exhausted, we batch and slow down.
>
> Four, the model is slow. The 5-second p95 budget is
> blown. We alert on p95 > 10 seconds; the on-call
> scales up the worker pool.
>
> Five, a poison document — a malformed PDF that
> crashes the worker. The worker has a try/except
> wrapper; the document goes to DLQ. We never
> silently drop.

### 30:00 — Wrap-up

> **Candidate:** That's the pipeline. The deep dive is
> the worker — the format router, the field extraction,
> the DLQ. The contract test is what keeps it stable.
> The cost driver is the worker pool size; the latency
> driver is OCR. If the OCR service is overloaded, the
> pipeline backs up, and that's what on-call sees
> first.

---

## Post-interview analysis

**What was good:**

- Strong opening with clarifying questions on format mix,
  document types, and consumer.
- The format router idea is a good abstraction — the rest
  of the pipeline doesn't care if it's PDF, DOCX, or image.
- DLQ pattern is named and the human review process is
  described.
- Idempotency via `doc_id` is clean.
- Five failure modes are named unprompted.

**What was missing:**

- Could have addressed security: documents may contain PII
  (SSN, addresses). The pipeline needs encryption at rest
  + in transit, access logging, and possibly a redaction
  step before indexing.
- The cost calculation is rough; could be more specific on
  Textract pricing ($1.50 per 1000 pages for detect-text).
- The schema registry wasn't named explicitly for the
  extracted-fields payload.
- Search relevance tuning was punted; in a real interview
  the interviewer might push.

**Score against the rubric:**

| Bucket | Score |
|---|---|
| Problem framing (15%) | 5/5 |
| Estimation (10%) | 4/5 |
| High-level architecture (20%) | 4/5 |
| Hot-path deep dive (35%) | 5/5 — worker stages, DLQ, idempotency |
| Tradeoff articulation (20%) | 4/5 — model versioning, format router, but missed security |

**Overall: senior answer.** Would pass at L5.

---

## Try it

Re-do this mock interview out loud. Pay particular attention
to the format router and the DLQ patterns. Both are the
hot path.
