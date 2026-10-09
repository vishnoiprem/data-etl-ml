# Architecture — AI Sales Coach

> **The design decisions behind the starter.** Read this before you change anything.

## System diagram

```
                        ┌─────────────────┐
                        │   React UI      │
                        │  (or HTML)      │
                        └────────┬────────┘
                                 │ HTTPS
                                 ▼
                        ┌─────────────────┐
                        │   FastAPI       │
                        │   (uvicorn)     │
                        ├─────────────────┤
                        │ /calls/upload   │
                        │ /calls/:id/...  │
                        │ /analyze        │
                        └────┬──────┬─────┘
                             │      │
                  ┌──────────┘      └──────────┐
                  ▼                             ▼
         ┌─────────────────┐          ┌─────────────────┐
         │  PostgreSQL     │          │     S3          │
         │  (Neon free)    │          │   (audio)       │
         ├─────────────────┤          └────────┬────────┘
         │ - users         │                   │
         │ - calls         │                   │
         │ - transcripts   │                   ▼
         │ - analyses      │          ┌─────────────────┐
         │ - scores        │          │  Audio Pipeline │
         └─────────────────┘          │  (FFmpeg +      │
                                      │   Whisper)      │
                                      └────────┬────────┘
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │  OpenAI API     │
                                      ├─────────────────┤
                                      │ - Whisper       │
                                      │ - gpt-4o        │
                                      │ - gpt-4o-mini   │
                                      └─────────────────┘
```

## Component choices

| Component | Choice | Alternative | Why we picked this |
|---|---|---|---|
| Transcription | OpenAI Whisper API | Whisper self-hosted, Deepgram, AssemblyAI | Zero ops, 1% WER on clean audio, $0.006/min |
| Analysis LLM | GPT-4o | Claude 3.5 Sonnet, o1 | Function calling + long context, strong on nuance |
| Synthesis LLM | GPT-4o-mini | Claude Haiku | 30× cheaper for the long feedback write-up |
| Audio storage | S3 (or local in dev) | R2, GCS | Standard, easy to swap |
| Backend | FastAPI | Flask, Django | Async, OpenAPI, Pydantic |
| Database | Postgres (Neon) | MongoDB, SQLite | Relational data + free tier |
| Auth | JWT → Clerk | Auth0, Supabase | Clerk has 5-min setup, social logins, MFA |
| Hosting | Railway | Render, Fly.io | $5/mo free tier, Postgres included |

## Data flow: analyze a call

```
1. User uploads MP3 via /calls/upload
2. FastAPI saves to S3, creates call row (status: "uploaded")
3. Background worker downloads audio, normalizes (ffmpeg)
4. Whisper API transcribes with word-level timestamps
5. Save transcript + speaker labels to Postgres (status: "transcribed")
6. analyzer.analyze(transcript) — GPT-4o with function calling extracts:
   - summary (1 paragraph)
   - talk_ratio (rep % vs prospect %)
   - pace (words/min)
   - objections (list of {type, timestamp, rep_response})
   - key_moments (list of {timestamp, label, importance})
   - sentiment (overall + per-segment)
7. feedback_engine.score(analysis) — GPT-4o-mini generates:
   - 5 rubric scores (0-10): rapport, discovery, objections, value, close
   - 3 "top wins"
   - 3 "top improvements" with specific timestamps
   - 1 "drill" practice exercise
8. Save all to Postgres, mark call "analyzed"
9. User GETs /calls/:id to see results
```

## Capacity model

| Reps | Calls/day | Audio/min/day | Compute | Storage | Monthly cost |
|---|---|---|---|---|---|
| 10 | 30 | 600 | Railway free | Neon + S3 free | $0 |
| 100 | 300 | 6K | Railway $20 | S3 $5, Neon free | $25 |
| 1K | 3K | 60K | Railway $100, 4 workers | S3 $40, Neon $15 | $155 |
| 10K | 30K | 600K | Railway $500, autoscaling | S3 $400, Neon $50 | $950 |
| 100K | 300K | 6M | Railway $2K, dedicated workers | S3 $4K, Neon $200 | $6,200 |

**Per call (avg, 20-min call):**
- Whisper transcription = $0.12
- GPT-4o analysis (function call, 5K+3K tokens) = $0.10
- GPT-4o-mini feedback (2K+1.5K tokens) = $0.0014
- S3 storage (200MB × 12 mo) = $0.005/mo
- **Total per call = ~$0.22**

**Scaling cliffs:**

- **100 users**: Need to move transcription to a queue (CPU/IO bound, slow)
- **1K users**: Need to add Whisper batching and a worker pool (Celery + Redis)
- **10K users**: Need to consider self-hosted Whisper + GPU for cost (50% savings)
- **100K users**: Need to add streaming partial transcripts, multi-region S3

## Cost model (per 1K calls)

Assumes: avg 20-min calls.

| Component | Cost per 1K calls |
|---|---|
| Whisper API ($0.006/min × 20 min) | $120 |
| GPT-4o analysis (function call) | $100 |
| GPT-4o-mini feedback | $1 |
| S3 storage (200MB × 1K × 12mo / 1M = 2.4TB) | $55 |
| Postgres writes | $1 |
| **Total per 1K calls** | **$277** |

At $99/mo per rep with 3 calls/day = 90 calls/month = $1.10 per call. Cost $0.22. **80% margin.**

## Security checklist

- [x] JWT tokens with expiry (replace with Clerk for refresh tokens)
- [x] Per-user data isolation (user_id filter on every query)
- [x] Input validation (Pydantic, file size, file type)
- [x] Pre-signed S3 URLs for downloads (never expose S3 creds)
- [ ] Rate limiting per user (add in week 4)
- [ ] PII redaction before sending transcripts to OpenAI (sales calls have customer data!)
- [ ] GDPR right-to-delete (must be able to hard-delete a call and its analysis)
- [ ] Consent flag on upload (rep + prospect must consent to recording)
- [ ] HTTPS only (handled by hosting platform)
- [ ] CORS restricted to your domain
- [ ] Audio virus scanning before Whisper submission

## Observability checklist

- [x] Structured logs (JSON, request_id, user_id, timing)
- [x] Every Whisper call logged with duration + cost
- [x] Every GPT call logged with token counts + cost
- [x] Per-call timing (upload, transcribe, analyze, score)
- [ ] Add LangSmith for end-to-end trace (week 3)
- [ ] Add Sentry for error tracking (week 3)
- [ ] Add PostHog for product analytics (week 4)
- [ ] Add an eval pipeline: a held-out set of human-scored calls (week 5)
- [ ] Add uptime monitoring (week 4)

## Failure modes

| Failure | Detection | Recovery |
|---|---|---|
| Audio too long (>2h) | ffmpeg probe | Reject > 2h calls (split into 2 calls) |
| Audio is silent / corrupted | Whisper empty result | Mark call "unprocessable", notify user |
| Whisper rate limit | 429 | Backoff 2x, max 3 retries, fail job if exhausted |
| Whisper down | 5xx | Queue job, retry every 5 min for 1h, then fail |
| GPT-4o returns bad JSON | Pydantic validation | Retry once with "fix this" prompt, then fail with raw output |
| GPT-4o hallucinates timestamps | Cross-check vs transcript | Validation step: every cited timestamp must exist in transcript |
| User has 1000s of calls | DB CPU | Paginate (limit 50 per page), add indexes |
| User uploads PII without consent | (process) | Require consent flag on upload, redact names in feedback |

## When to migrate off this stack

| Trigger | Migration |
|---|---|
| >$5K/mo in OpenAI | Self-host Whisper on GPU (50% cost reduction); route analysis to Claude for cost diversity |
| >100 concurrent transcriptions | Move from per-request uvicorn to dedicated worker pool |
| >10K users | Move auth to Clerk, add team/manager dashboards, add CRM sync |
| EU users | Move to EU region (OpenAI EU), EU S3, add EU Whisper via Azure |
| Need on-prem | Self-host Whisper + Llama 3 70B for analysis (privacy) |
| Need real-time coaching | Add streaming whisper + WebSocket feedback loop |

## Trade-off log (ADRs)

- **ADR-001**: Whisper API over self-hosted — API is zero-ops, $0.006/min is cheap. Self-host only at >$5K/mo in transcriptions.
- **ADR-002**: GPT-4o over Claude for analysis — function calling is more deterministic, schema validation is cleaner. Claude is better for nuance but harder to validate.
- **ADR-003**: Two-stage LLM (analyze + feedback) — analysis extracts facts (function call), feedback generates narrative (mini). Mixing them wastes tokens.
- **ADR-004**: Word-level timestamps via Whisper — needed for click-to-play in the UI and for objection matching.
- **ADR-005**: Per-call, not per-user, scoring — each call is independent. Trends come from aggregating per call.
- **ADR-006**: Store raw audio for 30 days only — most users re-listen 1-2 times. Auto-purge after 30d, keep transcript + analysis forever.

## Future work

- [ ] Add speaker diarization (Whisper doesn't do this well; use pyannote)
- [ ] Add real-time call coaching (WebSocket-based, mid-call suggestions)
- [ ] Add custom playbooks per industry
- [ ] Add team leaderboards
- [ ] Add CRM integrations (HubSpot, Salesforce, Pipedrive)
- [ ] Add per-rep progress tracking (trends, line charts)
- [ ] Add Slack notifications when a new call is analyzed
- [ ] Add a mobile app for recording calls on the go
- [ ] Add multi-language support (Whisper supports 50+ languages)
- [ ] Add call-library search (find similar past calls)
