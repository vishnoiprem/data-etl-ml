# System Design Course — Full Curriculum

> **71 lessons · 32 videos · ~18 hours of hands-on work**
>
> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi)
>
> **Companion articles:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

A complete, runnable System Design course. Every system below has a
design doc (`design/README.md`), a working Python service
(`code/service.py` + `code/app.py`), and tests (`tests/`) you can
actually run. No mocks. No "left as an exercise to the reader" handwaves.

The course is organized into **11 modules**. Spend ~1 hour per module
in a first pass; revisit at 2× and 3× speed to internalize.

---

## The 11 modules

| # | Module | Lessons | What you'll build |
|---|---|---|---|
| [00](00_overview/) | **Overview** | 5 | Interview framework, the 8 must-know patterns, whiteboard rubric |
| [01](01_url_shortener/) | **Read-Heavy Systems** | 6 | URL Shortener, Typeahead, Instagram, Twitter, Newsfeed, YouTube/Netflix, **Reddit** |
| 02 | **Event-Driven Systems** | 3 | Distributed Message Queue, Webhook Delivery, Uber Eats |
| 03 | **Async Jobs & Workers** | 3 | Web Crawler, Job Scheduler, User Data Export |
| 04 | **Distributed Storage** | 5 | Key-Value Store, Rate Limiter, Distributed LRU, Dropbox, S3 Storage |
| 05 | **Transactional Systems** | 3 | Ticketmaster, Hotel Booking, Parking Garage |
| 06 | **Batch Processing** | 5 | Metrics & Logging, APM, Doc Processing, Zillow, Weather App |
| 07 | **Real-Time & Collaborative** | 5 | Messenger, WhatsApp, Chess.com, Slack, Google Docs |
| 08 | **Media Streaming** | 4 | YouTube, Netflix, TikTok, Twitch |
| 09 | **Agentic AI** | 6 | AI Support, ChatGPT, File Uploader, LLM Batching, Claude Code, Voice AI |
| [10](99_appendix/) | **Appendix: Concepts** | 18 | Glossary, blogs, caching, CDN, protocols, APIs, LB, CAP, SQL vs NoSQL, sharding, replication, consistent hashing, async, encryption, auth, cloud, availability, reliability |

**Total: 71 lessons.**

---

## Quick start

```bash
cd data-engineering-course/system_design

# 1. Install deps (one time)
pip install -r ../scripts/requirements.txt

# 2. Seed sample data
python3 scripts/seed_data.py

# 3. Run a service
python3 01_url_shortener/code/app.py            # http://localhost:8001

# 4. Run all tests for all modules
python3 -m unittest discover -s . -p 'test_*.py' -v
```

Each service exposes the same surface:
- `GET  /health` — liveness
- `GET  /metrics` — counters + histograms
- `GET  /` — index of endpoints
- module-specific REST endpoints

---

## Layout

```
system_design/
├── 00_overview/             # Interview framework, patterns
├── 01_url_shortener/        # design/ + code/ + tests/
├── 02_typeahead/
├── 03_instagram/
├── 04_twitter/
├── 05_newsfeed/
├── 06_yt_or_netflix/
├── 07_message_queue/
├── 08_webhook_delivery/
├── 09_uber_eats/
├── 10_web_crawler/
├── 11_job_scheduler/
├── 12_user_data_export/
├── 13_kv_store/
├── 14_rate_limiter/
├── 15_distributed_lru/
├── 16_dropbox/
├── 17_s3_storage/
├── 18_ticketmaster/
├── 19_hotel_booking/
├── 20_parking_garage/
├── 21_metrics_logging/
├── 22_apm/
├── 23_doc_processing/
├── 24_zillow/
├── 25_weather_app/
├── 26_messenger/
├── 27_whatsapp/
├── 28_chess/
├── 29_slack/
├── 30_google_docs/
├── 31_tiktok/
├── 32_twitch/
├── 33_ai_support/
├── 34_chatgpt/
├── 35_file_uploader/
├── 36_llm_batching/
├── 37_claude_code/
├── 38_voice_ai/
├── 39_reddit_homepage/
├── 99_appendix/             # Concepts reference
├── common/                  # Shared utils: cache, hashing, KV store, metrics, Snowflake IDs
├── sample_data/             # JSONL corpora for the services
├── scripts/                 # seed_data.py, scaffold.py
├── conftest.py              # pytest config
└── README.md                # ← you are here
```

Every module follows the same 5-step learning path:

1. **Read the design doc** — `XX_system/design/README.md`. This *is*
   your interview answer.
2. **Run the tests** — `python3 -m unittest XX_system/tests/`.
3. **Read the working code** — `XX_system/code/*.py`. Compact, with
   comments pointing to the design doc.
4. **Start the service** — `python3 XX_system/code/app.py`. Hit with curl.
5. **Do the exercises** — `exercises/XX_exercises.md`.

---

## How to use this course

**First pass (1× speed, ~18h):** read each design doc top-to-bottom,
run the code, read the code, run the tests, move on.

**Second pass (2× speed, ~9h):** re-read each design doc, this time
out loud, as if the interviewer just said "design X". Pause at every
diagram and explain it.

**Third pass (3× speed, ~6h):** close the doc, open a blank editor,
re-derive the design from the requirements. Compare.

By the third pass you'll be able to produce each design in 30-45 min
on a whiteboard. **That's the target.**

---

## Where to go next

- For data engineering foundations, see
  `data-engineering/data-enginnering-cloudvala/course-curricula/`.
- For ETL / ML projects, see `data-engineering/scb_aml_platform/`
  and `data-engineering/e-commerce-end-2end/`.
- Author articles: <https://medium.com/@premvishnoi>
