# AI Sales Coach — Capstone Starter

> **Build a sales-call analyzer that improves every rep in 8 weeks using this starter.**

This is the runnable starter for **Capstone Template 3** from [`../../projects/ai-engineer-capstone-guide.md`](../../projects/ai-engineer-capstone-guide.md). The starter gives you a complete working skeleton: upload a sales call recording, Whisper transcribes it, GPT-4o analyzes the call with structured function calling, the feedback engine produces a coaching report. Your job is to extend it to a production-grade, paid SaaS over 8 weeks.

---

## What you start with

A working AI Sales Coach with:

- ✅ **Audio upload** — MP3 / WAV / M4A up to 200MB
- ✅ **Whisper transcription** — word-level timestamps, speaker diarization (optional)
- ✅ **Structured analysis** — GPT-4o with function calling extracts: objections, sentiment, talk ratio, key moments
- ✅ **Coaching feedback** — rubric-based scoring (rapport, discovery, objection-handling, close)
- ✅ **Backend** — FastAPI with `/calls`, `/analyze`, `/report/:id` endpoints
- ✅ **Auth** — JWT-based auth (replace with Clerk/Auth0 in production)
- ✅ **Persistence** — Postgres for users, calls, transcripts, analyses
- ✅ **Tests** — pytest suite covering the analyzer
- ✅ **Docker** — Dockerfile + docker-compose for local dev
- ✅ **Architecture doc** — [`ARCHITECTURE.md`](./ARCHITECTURE.md) with system diagram, cost model, capacity model

What you add in 8 weeks:

- [ ] Replace JWT with Clerk
- [ ] Add Stripe for payments ($99/mo per rep)
- [ ] Add team / manager dashboards (roll up scores across reps)
- [ ] Add real-time call coaching (live whisper during a call)
- [ ] Add custom playbooks per industry (SaaS, real estate, financial services)
- [ ] Add CRM integrations (HubSpot, Salesforce, Pipedrive)
- [ ] Add per-rep progress tracking (trends over time)
- [ ] Add Slack notifications when a new call is analyzed
- [ ] Deploy to Railway / Render
- [ ] Get 10 paying users

---

## How to run locally

```bash
# 1. Install dependencies (Whisper needs ffmpeg)
cd 03-ai-sales-coach
brew install ffmpeg        # or apt-get install ffmpeg
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Add OPENAI_API_KEY

# 3. Start the server
uvicorn app:app --reload

# 4. Open the UI
open http://localhost:8000
```

---

## Folder structure

```
03-ai-sales-coach/
├── README.md               # this file
├── ARCHITECTURE.md         # system design + cost model + capacity model
├── app.py                  # FastAPI entry point
├── audio_processor.py      # Whisper transcription
├── analyzer.py             # GPT-4o call analysis with function calling
├── feedback_engine.py      # Coaching feedback generation
├── frontend/
│   └── index.html          # minimal UI (replace with React in week 5)
├── tests/
│   └── test_agent.py       # pytest suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/signup` | Create account, returns JWT |
| `POST` | `/auth/login` | Login, returns JWT |
| `POST` | `/calls/upload` | Upload an audio file, returns call_id |
| `POST` | `/calls/:id/analyze` | Run analysis on a transcribed call |
| `GET` | `/calls` | List user's past calls |
| `GET` | `/calls/:id` | Get transcript + analysis + feedback |
| `GET` | `/health` | Health check (no auth) |

See `app.py` for the OpenAPI spec.

---

## The 8-week build path

| Week | Goal | Deliverable |
|---|---|---|
| 1 | Pick idea, validate, set up repo | 5 user interviews, 1-page PRD |
| 2 | Use this starter end-to-end | Working MVP on localhost |
| 3 | Add real auth (Clerk) + database | Multi-user login |
| 4 | Add Stripe + admin dashboard | Payment flow works |
| 5 | Replace frontend with React | Polished UI |
| 6 | Get first 10 users | Soft launch |
| 7 | Polish + blog post | Portfolio-ready |
| 8 | Demo day + iterate | Public launch |

For week-by-week tasks and common mistakes, see [`../../projects/ai-engineer-capstone-guide.md`](../../projects/ai-engineer-capstone-guide.md).

---

## What makes this starter "architect-grade"

This isn't a 200-line hackathon project. It includes:

- **Streaming transcription** — process the audio in chunks so partial transcripts are visible
- **Function-calling extraction** — structured schema, validated with Pydantic, deterministic JSON
- **Rubric-based scoring** — score across 5 dimensions (rapport, discovery, objections, value, close)
- **Talk ratio + pace metrics** — derived from the transcript, not from the audio
- **Objection library** — match detected objections against a known library
- **Observability** — every Whisper call and GPT call logged with latency + cost
- **Capacity model** — see ARCHITECTURE.md for the 1K/10K/100K user projections
- **Trade-offs documented** — Whisper API vs self-hosted, GPT-4o vs Claude for nuance

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full document.

---

## Paired learning resources

- **Lesson labs** — [`../../practice/level-6-multimodal/`](../../practice/level-6-multimodal/) covers Whisper + multimodal patterns
- **Codebook** — [`../../workbooks/ai-engineer-codebook.md`](../../workbooks/ai-engineer-codebook.md) § 5 covers function calling patterns
- **Exercises** — [`../../workbooks/exercises/section-3-prompt-engineering-exercises.md`](../../workbooks/exercises/section-3-prompt-engineering-exercises.md) extends what you build here

---

## License

MIT — use freely in your own products.
