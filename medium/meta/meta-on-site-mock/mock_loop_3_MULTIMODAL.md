# LOOP 3: Multimodal RAG + Cost at 100M

**Theme:** PDF tables + images + $130k cost optimization
**Total Duration:** 3 hours 15 min
**Difficulty:** Hard (multimodal is rare L6 skill)

---

## Architecture Diagram (Master)

```
┌────────────────────────────────────────────────────────────────────┐
│                  MULTIMODAL RAG - 100M SCALE                       │
└────────────────────────────────────────────────────────────────────┘

                INGESTION                          QUERY
                ────────                          ──────
                                                         
┌──────────┐    ┌─────────┐    ┌──────────────┐    ┌──────────┐
│ PDF S3   │───▶│ PyMuPDF │───▶│ Modality     │───▶│ Qdrant   │
│ 100M     │    │ Extract │    │ Splitter     │    │ 10 shard │
│ files    │    │         │    │              │    │          │
└──────────┘    └────┬────┘    └──────┬───────┘    └────┬─────┘
                     │               │                 │
                     ▼               ▼                 ▼
              ┌────────────┐  ┌─────────────┐    ┌────────────┐
              │ Tables     │  │ Text 512tok │    │ Hybrid     │
              │ JSON rows  │  │ text-emb-3  │    │ Search     │
              │ +headers   │  │ -large      │    │ + Rerank   │
              └─────┬──────┘  └──────┬──────┘    └─────┬──────┘
                    │               │                 │
                    ▼               ▼                 ▼
              ┌────────────┐  ┌─────────────┐    ┌────────────┐
              │ Table      │  │ Qdrant      │    │ LLM w/     │
              │ Encoder    │  │ collection: │    │ evidence   │
              │ (custom)   │  │ text_chunks │    │ _json      │
              └─────┬──────┘  └─────────────┘    └─────┬──────┘
                    │                                   │
                    ▼                                   ▼
              ┌────────────┐                    ┌────────────┐
              │ Qdrant     │                    │ Grounded   │
              │ collection:│                    │ Answer     │
              │ table_     │                    │ +citation  │
              │ chunks     │                    │ row:3,col:2│
              └────────────┘                    └────────────┘
                                                         
              IMAGES                                OCR FALLBACK
              ──────                                ────────────
                                                         
┌──────────┐    ┌──────────┐    ┌──────────────┐
│ PDF S3   │───▶│ PIL      │───▶│ pHash dedup  │
│          │    │ Extract  │    │ (40% saved)  │
└──────────┘    └────┬─────┘    └──────┬───────┘
                     │                │
                     ▼                ▼
              ┌────────────┐    ┌─────────────┐
              │ CLIP       │    │ Qdrant      │
              │ embedding  │    │ collection: │
              │            │    │ image_chunks│
              └────────────┘    └─────────────┘
```

---

## Greet (15 min)

### Q1: Tell me about a time you had to work with non-text data - PDF tables, images?

**L6 Answer (90 sec):**

> "At APEX-RAG, I extended from text-only to multimodal for 10M enterprise PDFs. The challenge: **table chunking.** If I split a table row-by-row, I lose the header context — 'What is Q3 revenue?' becomes 'What is Q3 revenue when the column header is on page 5?'
>
> My solution: a **table-aware chunker** that keeps the header + 5 rows as a JSON object `{header: [...], rows: [[...]]}`. Text I chunk at 512 tokens. Images go through CLIP embedding. I dedupe images by **perceptual hash (pHash)** before embedding — saved 40% cost = $200k.
>
> Three collections in Qdrant: text_chunks, table_chunks, image_chunks, cross-referenced by doc_id. Query path is hybrid search across all three."

**L6 Keywords:** multimodal, table-aware chunker, JSON, CLIP, pHash, cost $200k saved, 3 collections, hybrid search.

---

### Q2: How do you measure cost of RAG at 100M scale?

**L6 Answer (60 sec):**

> "Three cost buckets, all tracked in ClickHouse `traces` table:
>
> 1. **Ingestion:** $0.0042/query × 100M docs = **$420k one-time** + $50k/month incremental via Flink CDC.
> 2. **Retrieval:** $0.0001 per Qdrant query × 1B queries/month = **$100k/month.**
> 3. **Generation:** $0.003 per LLM call × 1B = **$3M/month** — the biggest line item.
>
> Goal: **p50 cost per query <$0.005.** Semantic cache saves 30% on LLM cost = **$900k/month saved.**
>
> I track per-query cost by modality: text vs table vs image, and alert if cost increases >10% week-over-week."

**L6 Keywords:** three buckets, $3M/month, semantic cache $900k, per-modality cost, alert >10%.

---

## AI-Native DE Full Stack (60 min)

### Q1 Data Model (15 min)

```
┌──────────────────────────────────────────────────────────┐
│                   MULTIMODAL DATA MODEL                  │
└──────────────────────────────────────────────────────────┘

pdf_files                    tables
┌──────────────────┐        ┌──────────────────────────┐
│ file_id      PK  │◀──────▶│ table_id     PK          │
│ uri              │  1:N   │ file_id     FK           │
│ is_scanned   BOOL│        │ header       JSON        │
│ total_pages  INT │        │ rows         JSON        │
│ modality_mask    │        │ page_number  INT         │
│   [text,table,   │        │ row_count    INT         │
│    image]        │        │ col_count    INT         │
│ sha256       STR │        │ embedding    VECTOR      │
│ created_at       │        │ chunk_index  INT         │
└────────┬─────────┘        └──────────────────────────┘
         │
         │ 1:N
         ▼
┌──────────────────┐        ┌──────────────────────────┐
│ text_chunks      │        │ image_chunks             │
├──────────────────┤        ├──────────────────────────┤
│ chunk_id     PK  │        │ image_id     PK          │
│ file_id     FK   │        │ file_id      FK          │
│ text             │        │ image_url                │
│ embedding VECTOR │        │ perceptual_hash 64-bit   │
│ token_count  INT │        │ clip_embedding VECTOR   │
│ chunk_index  INT │        │ width         INT        │
│ page_number  INT │        │ height        INT        │
│ embedding_cost $ │        │ page_number  INT         │
└──────────────────┘        │ embedding_cost $         │
                            └──────────────────────────┘
```

**SQL schema:**

```sql
CREATE TABLE pdf_files (
  file_id        BIGINT PRIMARY KEY,
  uri            STRING NOT NULL,
  is_scanned     BOOLEAN DEFAULT FALSE,
  total_pages    INT,
  modality_mask  ARRAY<STRING>,  -- ['text', 'table', 'image']
  sha256         STRING,
  created_at     TIMESTAMP
) PARTITIONED BY (DATE(created_at));

CREATE TABLE text_chunks (
  chunk_id        BIGINT PRIMARY KEY,
  file_id         BIGINT FK REFERENCES pdf_files(file_id),
  text            STRING,
  embedding       ARRAY<FLOAT>,
  token_count     INT,
  chunk_index     INT,
  page_number     INT,
  embedding_cost  FLOAT
);

CREATE TABLE tables (
  table_id        BIGINT PRIMARY KEY,
  file_id         BIGINT FK,
  header          JSON,        -- preserves col headers
  rows            JSON,        -- preserves row data [[row1], [row2]]
  page_number     INT,
  row_count       INT,
  col_count       INT,
  embedding       ARRAY<FLOAT>
);

CREATE TABLE image_chunks (
  image_id        BIGINT PRIMARY KEY,
  file_id         BIGINT FK,
  image_url       STRING,
  perceptual_hash BIGINT,      -- 64-bit pHash for dedup
  clip_embedding  ARRAY<FLOAT>,
  width           INT,
  height          INT,
  page_number     INT,
  embedding_cost  FLOAT
);
```

**Why table stored as JSON:** preserves row/col structure, queryable, citable.

---

### Q2 Pipeline Design (15 min)

```
┌──────────────────────────────────────────────────────────────┐
│            PDF INGESTION PIPELINE (10M PDFs)                 │
└──────────────────────────────────────────────────────────────┘

PDF S3 ──▶ PyMuPDF Parser ──▶ Branch by Type
              │                    │
              │                    ├─▶ Text stream
              │                    │     └─▶ 512 token chunks
              │                    │         └─▶ text-embedding-3-large
              │                    │             └─▶ text_chunks table
              │                    │
              │                    ├─▶ Table stream
              │                    │     └─▶ JSON: {header, rows}
              │                    │         └─▶ table-encoder
              │                    │             └─▶ tables table
              │                    │
              │                    └─▶ Image stream
              │                          └─▶ PIL extract
              │                              └─▶ pHash dedup (40% saved)
              │                                  └─▶ CLIP embedding
              │                                      └─▶ image_chunks
              │
              └─▶ If is_scanned=true
                       └─▶ Tesseract OCR
                              └─▶ Back to text stream
```

**Pipeline details:**

1. **PyMuPDF** extracts text + tables + images per page
2. **If is_scanned** (empty text returned) → Tesseract OCR
3. **Text:** chunk at 512 tokens, embed with `text-embedding-3-large`
4. **Tables:** extract as JSON `{header: [...], rows: [[...]]}`, embed with custom table-encoder
5. **Images:** PIL extract bytes → perceptual hash → dedup (40% hit rate) → CLIP embed
6. **Batch 1000** at a time for API rate limits, **semaphore 100** concurrent
7. **Failure:** retry 3x with exponential backoff, send to DLQ `pdfs_failed`

**Cost math:** 10M PDFs × 10 chunks avg = 100M chunks. Dedup saves 40% on images = $200k.

---

### Q3 SQL (15 min)

**Q: Cost breakdown by modality**

```sql
WITH all_chunks AS (
  SELECT 'text'  AS modality, embedding_cost, token_count FROM text_chunks
  UNION ALL
  SELECT 'table' AS modality, embedding_cost, 0            FROM tables
  UNION ALL
  SELECT 'image' AS modality, embedding_cost, 0            FROM image_chunks
)
SELECT
  modality,
  COUNT(*)                       AS chunk_count,
  SUM(embedding_cost)            AS total_cost,
  AVG(embedding_cost)            AS avg_cost,
  AVG(token_count)               AS avg_tokens,
  ROUND(100.0 * SUM(embedding_cost) / SUM(SUM(embedding_cost)) OVER (), 2) AS pct_total
FROM all_chunks
GROUP BY modality
ORDER BY total_cost DESC;
```

**Output (expected):**
| modality | chunk_count | total_cost | avg_cost | pct_total |
|----------|-------------|------------|----------|-----------|
| text     | 80,000,000  | $336,000   | $0.0042  | 70%       |
| image    | 50,000,000  | $50,000    | $0.0010  | 10%       |
| table    | 10,000,000  | $84,000    | $0.0084  | 18%       |
| **TOTAL**| 140,000,000 | **$470,000** | -      | 100%      |

**Q: Find tables containing "Q3 revenue"**

```sql
SELECT
  table_id,
  file_id,
  page_number,
  header,
  rows
FROM tables
WHERE header @> '["Q3 revenue"]'  -- JSONB contains
   OR CAST(rows AS STRING) ILIKE '%Q3 revenue%'
ORDER BY table_id
LIMIT 100;
```

---

### Q4 Coding (15 min)

```python
import fitz  # PyMuPDF
import imagehash
from PIL import Image
import io
import json
from typing import List, Dict


def chunk_table(header: List[str], rows: List[List], max_rows: int = 5) -> List[Dict]:
    """
    Table-aware chunker: keeps header + 5 rows as JSON.
    Preserves row/col structure for citations like row:3,col:2.
    """
    chunks = []
    for i in range(0, len(rows), max_rows):
        chunk_rows = rows[i:i + max_rows]
        chunk = {
            "header": header,
            "rows": chunk_rows,
            "row_range": [i, i + len(chunk_rows) - 1],
            "col_count": len(header),
        }
        chunks.append(chunk)
    return chunks


def dedup_images(image_bytes_list: List[bytes]) -> List[bytes]:
    """
    Dedupe images by perceptual hash.
    Returns 40% fewer images on average for PDF datasets.
    """
    seen_hashes = set()
    unique = []
    for img_bytes in image_bytes_list:
        img = Image.open(io.BytesIO(img_bytes))
        phash = imagehash.phash(img)
        if phash not in seen_hashes:
            seen_hashes.add(phash)
            unique.append(img_bytes)
    return unique


def extract_pdf_multimodal(pdf_path: str) -> Dict:
    """Main extraction function: text + tables + images."""
    doc = fitz.open(pdf_path)
    result = {"text_chunks": [], "tables": [], "images": []}

    for page_num, page in enumerate(doc):
        # Text
        text = page.get_text()
        if not text.strip():
            text = ocr_page(page)  # Tesseract fallback
        result["text_chunks"].append({
            "page": page_num,
            "text": text[:2000],  # 512 tokens approx
        })

        # Tables
        tables = page.find_tables()
        for table in tables:
            rows = table.extract()
            result["tables"].append({
                "page": page_num,
                "header": rows[0] if rows else [],
                "rows": rows[1:] if len(rows) > 1 else [],
            })

        # Images
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            result["images"].append(base_image["image"])

    # Dedup images
    result["images"] = dedup_images(result["images"])
    return result
```

---

## Sr Tech Design (60 min) - AI Doc Parser

```
┌────────────────────────────────────────────────────────────────────┐
│         AI DOC PARSER - 100M PDFs, GROUNDED TO CELL                │
└────────────────────────────────────────────────────────────────────┘

   "What is Q3 revenue from table?"
                │
                ▼
        ┌───────────────┐
        │ Embed query   │  text-embedding-3-large
        └───────┬───────┘
                │
                ▼
        ┌───────────────────────────────────┐
        │ Parallel hybrid search           │
        │  - Qdrant text_chunks collection  │
        │  - Qdrant table_chunks collection │
        │  - Qdrant image_chunks collection │
        └───────────────┬───────────────────┘
                        │ Top 50 each
                        ▼
                ┌───────────────┐
                │ Cohere Rerank │  Top 8
                └───────┬───────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │ LLM Prompt (with evidence_json)       │
        │                                       │
        │ "Answer using only this evidence:     │
        │  [{type:'table', page:5, row:3,        │
        │    col:2, value: '$4.2B',             │
        │    header: ['Quarter', 'Revenue']}]   │
        │                                       │
        │  Question: What is Q3 revenue?        │
        │                                       │
        │  If not in evidence, say 'Not found'" │
        └───────────────┬───────────────────────┘
                        │
                        ▼
                ┌───────────────┐
                │ Grounded      │
                │ Answer        │
                │ + citation    │
                │ row:3, col:2  │
                └───────────────┘
```

**Key design decisions:**

1. **Grounded generation**: LLM only answers from `evidence_json`, refuses if not in evidence
2. **Citation format**: `table:row:col` is citable, parseable, verifiable
3. **OCR fallback**: Tesseract for scanned PDFs (5% of corpus)
4. **Freshness**: Flink CDC on S3 PDF events → re-parse → re-embed
5. **Scale**: 100M PDFs × 100 chunks = 10B chunks, 50 Qdrant shards, 200M/shard

**Scale math:** 10B chunks > Qdrant single-cluster capacity (1B). Solutions:
- **Time-based filter** (last 90 days hot, older summarized)
- **Tiered storage** (hot in Qdrant, cold in S3 + re-embed on query)
- **Per-collection sharding** by date or domain

---

## Sr Ownership (30 min)

### Q1: Reduced cost 50% — what tradeoff?

**L6 STAR:**

**S:** APEX-RAG LLM cost hit $3M/month, unsustainable for v1.

**T:** Reduce 50% without dropping quality below SLA.

**A:**
1. **Semantic cache** (SHA256 of query embedding) → 30% hit rate → saved $900k
2. **gpt-4 → gpt-3.5** for simple queries (LLM classifier routes) → $2M → $400k, Recall dropped 0.89→0.85
3. **Top-20 → Top-8** context chunks → $500k saved, Recall 0.85→0.83

**R:** $1.5M → $750k/month (50% reduction). Recall 0.83 still above 0.80 SLA. **Tradeoff: 6% Recall drop for 50% cost.** Owner happy, users happy, finance happy.

---

### Q2: Corrupted PDFs breaking pipeline

**L6 STAR:**

**S:** 5% of 1M PDFs were corrupted (50k), crashed PyMuPDF, pipeline stuck for 6 hours.

**T:** Handle gracefully, don't break 98%.

**A:**
1. Wrapped PyMuPDF in `try/except`, sent failures to DLQ `pdfs_failed`
2. Pre-flight validation: file size > 0, PDF header check
3. Quarantine table for manual review UI
4. Alert: DLQ depth > 1000 → page oncall
5. Wrote runbook with 4 common error types + fixes

**R:** 50k quarantined, 0 pipeline downtime, 99.5% success rate. MTTR 6h → 30min.

---

## Full Stack (60 min) - Multimodal Trace Viewer

```
┌─────────────────────────────────────────────────────────────────────┐
│                  MULTIMODAL TRACE VIEWER                            │
├──────────────┬──────────────────────┬───────────────────────────────┤
│ TEXT CHUNKS  │ TABLES (JSON)        │ IMAGES (with bbox)            │
├──────────────┼──────────────────────┼───────────────────────────────┤
│ [chunk 0]    │ ┌────┬────┬────┐     │ ┌──────────────────┐          │
│ Lorem ipsum  │ │Quart│Rev │Cost│    │ │  [thumbnail]     │          │
│ dolor sit... │ ├────┼────┼────┤     │ │   ┌──────┐       │          │
│              │ │Q1  │$2B │$1M │     │ │   │ bbox │       │          │
│ [chunk 1]    │ │Q2  │$3B │$1M │◀━━highlighted│   │      │          │
│ More text... │ │Q3  │$4B*│$2M │    │ │   └──────┘       │          │
│              │ │Q4  │$5B │$2M │     │ │                  │          │
│ [chunk 2]    │ └────┴────┴────┘     │ │  page 5, fig 2   │          │
│ Even more... │                      │ └──────────────────┘          │
└──────────────┴──────────────────────┴───────────────────────────────┘
              [Vote thumbs up/down]    [Citation: table:row:3,col:2]
```

```tsx
import { useState } from "react";

const MultimodalTraceViewer = ({ trace }) => {
  const [highlightCell, setHighlightCell] = useState(null);
  const [highlightBbox, setHighlightBbox] = useState(null);

  return (
    <div className="grid grid-cols-3 gap-4 p-6 h-screen">
      {/* LEFT: Text chunks */}
      <div className="overflow-y-auto border-r pr-4">
        <h3 className="font-bold mb-2">Text Chunks ({trace.text_chunks.length})</h3>
        {trace.text_chunks.map((c, i) => (
          <div key={i} className="border p-2 mb-2 rounded">
            <small className="text-gray-500">page {c.page} · chunk {i}</small>
            <p className="text-sm">{c.text}</p>
          </div>
        ))}
      </div>

      {/* MIDDLE: Tables with row/col highlight */}
      <div className="overflow-y-auto border-r pr-4">
        <h3 className="font-bold mb-2">Tables ({trace.tables.length})</h3>
        {trace.tables.map((t, ti) => (
          <div key={ti} className="mb-4">
            <small className="text-gray-500">page {t.page}</small>
            <table className="w-full border mt-1 text-sm">
              <thead>
                <tr>{t.header.map((h, ci) => <th key={ci} className="border p-1">{h}</th>)}</tr>
              </thead>
              <tbody>
                {t.rows.map((row, ri) => (
                  <tr key={ri}>
                    {row.map((cell, ci) => (
                      <td
                        key={ci}
                        onClick={() => setHighlightCell({row: ri, col: ci})}
                        className={`border p-1 cursor-pointer ${
                          highlightCell?.row === ri && highlightCell?.col === ci
                            ? "bg-yellow-300 font-bold"
                            : ""
                        }`}
                      >
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>

      {/* RIGHT: Images with bounding box */}
      <div className="overflow-y-auto">
        <h3 className="font-bold mb-2">Images ({trace.images.length})</h3>
        {trace.images.map((img, i) => (
          <div key={i} className="relative mb-3 border rounded">
            <img src={img.url} alt={`page ${img.page}`} className="w-full" />
            {img.bbox && (
              <div
                onClick={() => setHighlightBbox(img.bbox)}
                className="absolute border-2 border-red-500 cursor-pointer"
                style={{
                  left:   `${img.bbox.x * 100}%`,
                  top:    `${img.bbox.y * 100}%`,
                  width:  `${img.bbox.w * 100}%`,
                  height: `${img.bbox.h * 100}%`,
                }}
              />
            )}
            <small className="text-gray-500 block p-1">page {img.page}, fig {i}</small>
          </div>
        ))}
      </div>

      {/* Footer: citation */}
      <div className="col-span-3 border-t pt-2 text-sm text-gray-600">
        Citation: {highlightCell
          ? `table:row:${highlightCell.row},col:${highlightCell.col}`
          : highlightBbox
            ? `image:bbox(${highlightBbox.x},${highlightBbox.y})`
            : "Click a cell or bbox to cite"
        }
      </div>
    </div>
  );
};
```

---

## Day 1 Checkpoint

Before moving on, can you:
- [ ] Explain **why** table chunking preserves header + rows as JSON (not row-by-row)?
- [ ] Compute **per-modality cost SQL** with `UNION ALL`?
- [ ] Draw the **multimodal trace viewer** with text + table + image + bbox highlight?
- [ ] State the **3 cost buckets** of RAG at 100M scale?
- [ ] Explain **pHash dedup** saves 40% on image cost?

If yes to all 5, you're ready for Loop 4. If not, re-read the relevant section.
