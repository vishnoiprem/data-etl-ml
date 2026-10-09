# Months 2-6: Project Outlines
### 150 more hands-on AI projects, organized by data system

This file gives you the 30-project outline for each of Months 2-6. Each entry has the project title, the core concept, the data source, and a brief spec. Full code (like Month 1) is in `month-2-projects.md` through `month-6-projects.md` (the same level of detail as Month 1).

---

## MONTH 2: AI + REST APIs (Days 31-60)
**Theme:** "Build an AI that can call any API"
**Data system:** REST APIs + Webhooks
**Stack:** Python/JS, OpenAI, requests/httpx, ngrok (for webhooks), OAuth

### Week 1 (Days 31-37): Single API integration
- **Day 31:** Function-calling weather agent (OpenWeather API)
- **Day 32:** GitHub PR summarizer
- **Day 33:** Slack message classifier + router
- **Day 34:** Stripe payment analytics
- **Day 35:** Notion page Q&A
- **Day 36:** Linear issue triager
- **Day 37:** **WEEKEND** — Multi-API personal dashboard

### Week 2 (Days 38-44): Async + parallel calls
- **Day 38:** Async API client (httpx)
- **Day 39:** Parallel API calls (gather)
- **Day 40:** Retry with exponential backoff
- **Day 41:** Rate limit handling
- **Day 42:** Response caching (Redis)
- **Day 43:** Circuit breaker pattern
- **Day 44:** **WEEKEND** — Resilient API wrapper library

### Week 3 (Days 45-51): Webhooks + events
- **Day 45:** Webhook receiver (FastAPI)
- **Day 46:** Stripe webhook → AI categorization
- **Day 47:** GitHub webhook → AI code review
- **Day 48:** Slack webhook → AI moderation
- **Day 49:** ngrok for local webhooks
- **Day 50:** Webhook signature verification
- **Day 51:** **WEEKEND** — Event-driven AI system

### Week 4 (Days 52-58): OAuth + multi-user
- **Day 52:** OAuth 2.0 flow (GitHub)
- **Day 53:** Token refresh handling
- **Day 54:** Per-user API credentials
- **Day 55:** Multi-tenant API quotas
- **Day 56:** Audit log every API call
- **Day 57:** Anomaly detection on API usage
- **Day 58:** **WEEKEND** — OAuth dashboard

### Days 59-60: Month 2 capstone
- **Day 59:** Polish + tests
- **Day 60:** **MONTH PROJECT** — "Ops Agent" — an AI that manages your SaaS stack. You can ask it "show me all open P0 Linear issues, find the related Slack threads, summarize them, and post a status update." It calls Linear + Slack + GitHub + Notion APIs.

---

## MONTH 3: AI + Documents & Search (Days 61-90)
**Theme:** "Make AI understand your company's knowledge"
**Data system:** MongoDB + Elasticsearch + PDFs + Office docs
**Stack:** Python, elasticsearch-py, pymongo, pypdf, unstructured, OpenAI

### Week 1 (Days 61-67): Document ingestion
- **Day 61:** PDF text extraction (pypdf)
- **Day 62:** Word/Excel/PPT parsing (unstructured)
- **Day 63:** OCR for scanned PDFs (Tesseract)
- **Day 64:** Web scraping + chunking
- **Day 65:** Sitemap-based crawler
- **Day 66:** Notion/Confluence export
- **Day 67:** **WEEKEND** — Document ingestion pipeline

### Week 2 (Days 68-74): Full-text search (Elasticsearch)
- **Day 68:** Index docs in Elasticsearch
- **Day 69:** BM25 keyword search
- **Day 70:** Multi-field search (title + body + tags)
- **Day 71:** Faceted search (filters + aggregations)
- **Day 72:** Highlighting matched terms
- **Day 73:** Search autocomplete
- **Day 74:** **WEEKEND** — Search UI with filters

### Week 3 (Days 75-81): Semantic + hybrid search
- **Day 75:** Embed all docs
- **Day 76:** Vector search (ES + dense_vector)
- **Day 77:** Hybrid BM25 + vector
- **Day 78:** Re-ranking (Cohere)
- **Day 79:** Query understanding (spell fix, expansion)
- **Day 80:** Personalized ranking
- **Day 81:** **WEEKEND** — Search quality eval

### Week 4 (Days 82-88): Production RAG
- **Day 82:** RAG with citations (paragraph refs)
- **Day 83:** Conversational RAG (with chat history)
- **Day 84:** Multi-hop RAG (follow-up questions)
- **Day 85:** Streaming RAG responses
- **Day 86:** RAG evaluation (RAGAS)
- **Day 87:** RAG observability (LangSmith)
- **Day 88:** **WEEKEND** — RAG cost optimization

### Days 89-90: Month 3 capstone
- **Day 89:** Polish + load test
- **Day 90:** **MONTH PROJECT** — Customer Support AI that answers questions over 10K+ support tickets. Ingest → embed → hybrid search → LLM answer with citation. Deploy, get 5 users.

---

## MONTH 4: AI + Files & Media (Days 91-120)
**Theme:** "AI for images, audio, video, PDFs at scale"
**Data system:** S3-compatible object storage + media processing
**Stack:** Python, boto3, ffmpeg, Whisper, DALL-E, GPT-4V, Tesseract

### Week 1 (Days 91-97): Object storage + file upload
- **Day 91:** S3 file upload (presigned URLs)
- **Day 92:** Multi-part upload for large files
- **Day 93:** Image processing pipeline (resize, compress)
- **Day 94:** Virus scanning (ClamAV)
- **Day 95:** CDN integration (CloudFront/R2)
- **Day 96:** File metadata + tagging
- **Day 97:** **WEEKEND** — File upload service

### Week 2 (Days 98-104): Image AI
- **Day 98:** DALL-E 3 image generation
- **Day 99:** Stable Diffusion (local)
- **Day 100:** GPT-4V image understanding
- **Day 101:** Image similarity search (CLIP embeddings)
- **Day 102:** Image captioning
- **Day 103:** Object detection (YOLO)
- **Day 104:** **WEEKEND** — Visual search app

### Week 3 (Days 105-111): Audio AI
- **Day 105:** Whisper transcription
- **Day 106:** Speaker diarization
- **Day 107:** Real-time transcription
- **Day 108:** Audio embeddings (for similarity)
- **Day 109:** Text-to-speech (ElevenLabs, OpenAI)
- **Day 110:** Voice cloning (ethical, with consent)
- **Day 111:** **WEEKEND** — Podcast search engine

### Week 4 (Days 112-118): Video + PDF AI
- **Day 112:** Video frame extraction
- **Day 113:** Video scene detection
- **Day 114:** Video summarization
- **Day 115:** PDF table extraction
- **Day 116:** PDF figure/chart extraction
- **Day 117:** Form parsing (PDF → JSON)
- **Day 118:** **WEEKEND** — Document automation tool

### Days 119-120: Month 4 capstone
- **Day 119:** Polish + cost analysis
- **Day 120:** **MONTH PROJECT** — Media Processing Pipeline. Upload audio/video/PDF → auto-transcribe → summarize → index in search → webhook notifications. End-to-end async pipeline with monitoring.

---

## MONTH 5: AI + Real-Time Streams (Days 121-150)
**Theme:** "AI that reacts in real-time"
**Data system:** Kafka/Redpanda + Redis Streams + RabbitMQ
**Stack:** Python, kafka-python, redis, asyncio, OpenAI, observability

### Week 1 (Days 121-127): Queue basics
- **Day 121:** Redis Streams pub/sub
- **Day 122:** Producer/consumer pattern
- **Day 123:** Worker pool with concurrency
- **Day 124:** Dead-letter queue
- **Day 125:** Idempotency keys
- **Day 126:** Priority queues
- **Day 127:** **WEEKEND** — Async job system

### Week 2 (Days 128-134): Kafka fundamentals
- **Day 128:** Kafka producer (Redpanda)
- **Day 129:** Kafka consumer + offset management
- **Day 130:** Topic partitioning
- **Day 131:** Consumer groups
- **Day 132:** Schema registry (Avro/JSON)
- **Day 133:** Stream processing basics
- **Day 134:** **WEEKEND** — Real-time log pipeline

### Week 3 (Days 135-141): Event-driven AI
- **Day 135:** Event → AI → action pattern
- **Day 136:** Stream enrichment with LLM
- **Day 137:** Real-time content moderation
- **Day 138:** Live chat AI assistant
- **Day 139:** Real-time translation pipeline
- **Day 140:** Anomaly detection on streams
- **Day 141:** **WEEKEND** — Real-time AI dashboard

### Week 4 (Days 142-148): Observability + ops
- **Day 142:** OpenTelemetry tracing
- **Day 143:** Metrics: throughput, latency, errors
- **Day 144:** Cost attribution per consumer
- **Day 145:** Auto-scaling workers
- **Day 146:** Backpressure handling
- **Day 147:** Multi-region replication
- **Day 148:** **WEEKEND** — Production-grade stream app

### Days 149-150: Month 5 capstone
- **Day 149:** Load test + chaos test
- **Day 150:** **MONTH PROJECT** — AI Incident Response for SREs. Logs stream in → LLM classifies → severity scored → PagerDuty/Slack alerted → runbook auto-attached. Real-time, observable, cost-tracked.

---

## MONTH 6: AI + Vector Search at Scale (Days 151-180)
**Theme:** "Production-grade vector AI"
**Data system:** Pinecone/Weaviate/Qdrant/Chroma
**Stack:** Python, vector DB SDKs, hybrid search libs, re-rankers

### Week 1 (Days 151-157): Vector DB fundamentals
- **Day 151:** Pinecone basics (insert, search, delete)
- **Day 152:** Weaviate schema design
- **Day 153:** Qdrant payloads + filtering
- **Day 154:** Chroma for local dev
- **Day 155:** Embedding model comparison
- **Day 156:** Vector index types (HNSW vs IVFFlat)
- **Day 157:** **WEEKEND** — Multi-DB benchmark

### Week 2 (Days 158-164): Advanced search
- **Day 158:** Metadata filtering
- **Day 159:** Hybrid search (vector + keyword)
- **Day 160:** Re-ranking with cross-encoders
- **Day 161:** Multi-vector search (per-field)
- **Day 162:** Sparse + dense (SPLADE)
- **Day 163:** Late interaction (ColBERT)
- **Day 164:** **WEEKEND** — Search quality benchmark

### Week 3 (Days 165-171): Production patterns
- **Day 165:** Sharding strategies
- **Day 166:** Replication + read replicas
- **Day 167:** Backup + restore
- **Day 168:** Cost optimization (right-sizing)
- **Day 169:** Multi-tenancy (namespaces)
- **Day 170:** Vector DB monitoring
- **Day 171:** **WEEKEND** — Production-ready search service

### Week 4 (Days 172-178): Multi-modal + capstone prep
- **Day 172:** Multi-modal embeddings (CLIP)
- **Day 173:** Image + text search
- **Day 174:** Cross-lingual search
- **Day 175:** Personalized ranking
- **Day 176:** A/B test search quality
- **Day 177:** Capstone MVP
- **Day 178:** **WEEKEND** — Capstone polish

### Days 179-180: Demo Day + capstone
- **Day 179:** Record demo video, write launch post
- **Day 180:** **CAPSTONE LAUNCH** — Your AI SaaS goes live. Get 10 paying users. Demo Day live stream.

---

## Cross-Month Themes

Each month, the same 5 themes repeat, but deeper:

1. **Real data from real systems** — Never lorem ipsum
2. **Live in production** — Every project deployed
3. **Observable** — Logs, metrics, traces
4. **Costed** — Track every API dollar
5. **Portfolio-grade** — Every project on GitHub

---

## What You Have at Day 180

- 180 deployed AI projects
- 6 monthly capstones (all live, with users)
- 1 capstone SaaS (with paying users)
- Public GitHub with 180 repos
- Portfolio website (auto-generated)
- Demo video (your best 10 projects)
- 1,500+ hours of hands-on AI engineering
- Job-ready or SaaS-ready

---

## See Also

- `month-1-projects.md` — Full code for all 30 Month 1 projects
- `month-2-projects.md` — Full code for Month 2
- `month-3-projects.md` — Full code for Month 3
- `month-4-projects.md` — Full code for Month 4
- `month-5-projects.md` — Full code for Month 5
- `month-6-projects.md` — Full code for Month 6
- `180-day-overview.html` — Visual calendar
