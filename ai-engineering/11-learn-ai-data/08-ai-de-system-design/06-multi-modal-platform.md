# Lesson 6 — Multi-Modal Platform

> **Type:** Article · Module 8 · AI DE System Design
> Text + image + audio at scale, with unified embeddings and a single search API.

---

## The problem

> Design a multi-modal search and RAG platform for a media company. 50M documents: text articles, 5M images, 200k hours of audio/video. Users want to search across all modalities ("find clips where someone is talking about X and a chart is shown"). Need cross-modal search, citations, and freshness SLAs (5 min for new uploads).

---

## Step 1 — CLARIFY

```
   data:        50M documents (mixed modalities)
                text: 30M
                images: 5M
                audio/video: 200k hours
   queries:     ~10k QPS mixed
                text-only: 70%
                image-only: 10%
                cross-modal: 15% (text → image/audio, image → text)
                hybrid: 5%
   freshness:   new uploads: 5 min
                metadata edits: 1 min
   latency:     p95 < 1s (consumer-facing)
   ACL:         per-tenant content visibility
   cost:        < $200k/mo for storage + processing + serving
   failure mode: wrong modality match (image returns text)
                 freshness miss
                 ACL leak
```

---

## Step 2 — SKETCH

```
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   USER QUERY  (text or image)                                │
   │        │                                                     │
   │        ▼                                                     │
   │   [Query Router]   ─► if image → CLIP encode                │
   │        │            ─► if text → text embed                  │
   │        ▼                                                     │
   │   [Unified Vector DB]                                       │
   │     all modalities in same vector space (CLIP / Cohere)     │
   │        │                                                     │
   │        ▼                                                     │
   │   [Hybrid Filter]   ACL + metadata                           │
   │        │                                                     │
   │        ▼                                                     │
   │   [Reranker]                                                │
   │        │                                                     │
   │        ▼                                                     │
   │   [Multi-Modal Response]                                     │
   │     text answers + image thumbnails + audio clips           │
   │        │                                                     │
   │        ▼                                                     │
   │   [LLM for synthesis]   ◄──── if cross-modal RAG             │
   │                                                              │
   │   ──── ingest ────                                          │
   │                                                              │
   │   [Upload]                                                  │
   │        │                                                     │
   │        ▼                                                     │
   │   [Type Router]                                             │
   │     ├──► Text       ─► chunk ─► embed (text model)         │
   │     ├──► Image      ─► CLIP embed + caption (vision-LLM)   │
   │     ├──► Audio      ─► Whisper transcribe + embed          │
   │     └──► Video      ─► frames (CLIP) + audio (Whisper) +   │
   │                        transcribe, embed each               │
   │        │                                                     │
   │        ▼                                                     │
   │   [Metadata + ACL]                                           │
   │        │                                                     │
   │        ▼                                                     │
   │   [Unified Vector DB]                                       │
   │                                                              │
   │   ──── operations ────                                      │
   │                                                              │
   │   [Eval Harness]   [Drift]   [Cost]   [Audit]               │
   └──────────────────────────────────────────────────────────────┘
```

---

## Step 3 — DEEP-DIVE

### Box 1: Unified embedding space

The cross-modal search story requires all modalities in the **same vector space**.

```
   EMBEDDING SPACES (2026)
   ───────────────────────
   CLIP               text ↔ image (mature, 2026 standard)
   Cohere embed-v3    text, image, audio (multi-vector)
   ImageBind (Meta)   text, image, audio, depth, IMU (research-grade)
   Whisper + text embed   audio → text → vector (transcribe-then-embed)
```

For production, the **two main options** are:
1. **CLIP for image, text embed for text, Whisper for audio** — three separate indexes, but cross-modal via text bridge
2. **Cohere embed-v3 multimodal** — single unified index

Option 1 is more battle-tested; Option 2 is more elegant but newer.

### Box 2: Ingest pipeline per modality

```
   INGEST (per modality)
   ────────────────────

   TEXT
   ────
   upload → chunk (200-500 tokens, structure-aware)
        → embed (text-embedding-3-large or Cohere)
        → metadata + ACL
        → vector DB

   IMAGE
   ─────
   upload → CLIP embed
        → caption (vision-LLM, "describe this image in detail")
        → caption embed
        → metadata + ACL
        → vector DB
        (both the CLIP vector and the caption embed; user can search by either)

   AUDIO
   ─────
   upload → Whisper transcribe (with timestamps + diarization)
        → chunk by time (30s windows) or speaker turn
        → embed each chunk
        → metadata: timestamps, speakers
        → vector DB

   VIDEO
   ─────
   upload → extract frames (every 2s)
        → extract audio → transcribe (Whisper)
        → embed frames (CLIP)
        → embed transcript chunks
        → metadata: timestamps, frame indices
        → vector DB
```

Each modality has its own adapter. The chunk store + vector DB is shared.

### Box 3: Cross-modal query

The killer feature: **search across modalities with a single query**.

```
   QUERY: "the CEO talking about AI safety"
        │
        ▼
   query embedding (text)
        │
        ├──► ANN search over TEXT vector DB
        │     → finds articles mentioning "CEO" + "AI safety"
        │
        ├──► ANN search over IMAGE caption embeddings
        │     → finds images captioned "CEO at AI safety summit"
        │
        ├──► ANN search over AUDIO transcript embeddings
        │     → finds audio clips with the spoken phrase
        │
        └──► ANN search over VIDEO (transcript + frames)
              → finds clips where someone said it AND a face appeared

   ── fusion ──
   RRF over all modalities, top-20 candidates
   rerank with cross-encoder
   return top-5 with citations across modalities
```

### Box 4: Eval harness for multi-modal

```
   EVAL SET
   ────────
   200 text→text queries
   100 text→image queries
   100 text→audio queries
   50 cross-modal (text → mixed)
   30 image→text queries
   50 adversarial (wrong modality, off-topic, PII)

   METRICS
   ───────
   recall@10 per modality
   cross-modal recall@10
   freshness SLA adherence
   ACL pass rate
   latency p95
   cost per query
```

---

## Step 4 — TRADEOFFS

| Choice | Alternative | Why | Revisit if |
|---|---|---|---|
| **CLIP + text embed + Whisper** (3 indexes) | Cohere embed-v3 multimodal (1 index) | Battle-tested, mature, easier to debug | cross-modal recall insufficient |
| **Vision-LLM caption + text embed** for images | CLIP only | Better recall on semantic queries ("charts about X") | caption quality insufficient OR cost too high |
| **Whisper transcript for audio** | Direct audio embed | Transcribed audio is searchable by text query | low-resource languages; need raw audio similarity |
| **Frame extraction every 2s** for video | Scene detection | Simpler, more granular | cost too high OR frame rate inadequate |
| **Unified RRF fusion across modalities** | Modality-specific queries | One query → all relevant results | query type known in advance |

---

## Step 5 — SUMMARY

**Decision:**
- Type router + per-modality adapters (text, image, audio, video)
- CLIP for image embeddings, vision-LLM captions + text embed for semantic image search
- Whisper for audio transcription + text embed
- Frame extraction + transcript for video
- Unified vector DB (Pinecone / Weaviate / Cohere) with metadata ACL
- Cross-modal query: embed once (text), search all modalities, RRF fusion, rerank
- Eval harness per modality + cross-modal
- Per-modality freshness SLAs (5 min for new uploads)

**Cost (rough):**
- Storage (S3 + vector DB, 50M vectors): ~$15k/mo
- Vision-LLM captioning (5M images, $0.00255/image): ~$13k/mo (one-shot)
- Whisper transcription (200k hours, $0.006/min): ~$72k (one-shot)
- Embeddings (50M items × 1024-d): ~$5k/mo
- ANN serving (Pinecone / Weaviate): ~$10k/mo
- LLM synthesis: ~$5k/mo
- Ingest compute: ~$10k/mo
- **Total: ~$60k/mo recurring + ~$85k one-shot ingest**

**Revisit if:**
- Cross-modal recall@10 < 80% → add caption + better reranker
- Latency p95 > 1s → cache common queries, reduce candidate set
- Cost > $200k/mo → drop captions on low-value images, reduce frame rate
- New modality needed → add adapter, plug into type router

---

## The "cross-modal RAG" answer

When the user asks a question that requires multiple modalities:

```
   QUERY: "What did the CEO say about AI safety, with a chart?"

   1. Embed query (text)
   2. ANN search across all modalities
   3. RRF fusion → top-20
   4. Cross-encoder rerank → top-10
   5. Multimodal LLM (Claude / GPT-4o) sees:
      - text chunks
      - image thumbnails (base64)
      - audio timestamps + transcripts
   6. Generate answer with citations across modalities
   7. Render response: text + inline images + click-to-play audio
```

The LLM is multimodal; it can see images and reason across them. The vector DB finds the candidates; the LLM synthesises the answer.

---

## What Comes Next

> Lesson 7 — **Quiz: AI DE System Design** — self-check on the five design problems + the framework.