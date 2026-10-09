# System Design Course — Read-Heavy Systems

A **fully working, runnable** System Design course covering 6 read-heavy systems.
Every module includes a design document, a working Python implementation, and
unit tests you can run end-to-end on your laptop.

> **Course format:** 6 lessons · 4 videos · ~6–10 hours of hands-on work.

## What you will build

| # | System | Pattern | Working code |
|---|--------|---------|--------------|
| 01 | URL Shortener (TinyURL) | Write-heavy key-gen, cache-heavy reads | `01_url_shortener/code/` |
| 02 | Typeahead / Search Suggest | Trie + ranked top-K, debounced | `02_typeahead/code/` |
| 03 | Instagram | Blob storage + metadata + fanout-on-read | `03_instagram/code/` |
| 04 | Twitter / X | Fanout-on-write + timeline merge | `04_twitter/code/` |
| 05 | Newsfeed (Facebook-style) | Ranking + fanout hybrid | `05_newsfeed/code/` |
| 06 | YouTube / Netflix | CDN, sharded metadata, recommendations | `06_yt_or_netflix/code/` |

Each system is a **real, runnable** Python service you can start, hit with
HTTP/CLI calls, and observe. No mocks, no fakes.

## Quick start

```bash
# 1. Clone is already done — you are in data-engineering-course
cd data-engineering-course

# 2. Run the smoke tests for all 6 systems
bash scripts/run_all_smoke_tests.sh

# 3. Start any system as an HTTP service
python3 01_url_shortener/code/app.py            # http://localhost:8001
python3 02_typeahead/code/app.py                # http://localhost:8002
python3 03_instagram/code/app.py                # http://localhost:8003
python3 04_twitter/code/app.py                  # http://localhost:8004
python3 05_newsfeed/code/app.py                 # http://localhost:8005
python3 06_yt_or_netflix/code/app.py            # http://localhost:8006
```

## Layout

```
data-engineering-course/
├── 01_url_shortener/        # Design + code + tests
├── 02_typeahead/            # Design + code + tests
├── 03_instagram/            # Design + code + tests
├── 04_twitter/              # Design + code + tests
├── 05_newsfeed/             # Design + code + tests
├── 06_yt_or_netflix/        # Design + code + tests
├── common/                  # Shared utilities (cache, hashing, etc.)
├── sample_data/             # Seed corpora for the systems
├── scripts/                 # Run-all, bootstrap, load-test helpers
├── tests/                   # Cross-system smoke tests
├── exercises/               # Extensions / TODO challenges per system
├── docs/                    # How to read a system design interview answer
└── notebooks/               # Optional Jupyter playbooks
```

## How the lessons are structured

Every module follows the same 5-step learning path:

1. **Read the design doc** — `XX_system/design/README.md`. This is your
   "interview answer" — requirements, capacity, API, data model, deep dive.
2. **Run the tests** — `pytest XX_system/tests`. They will fail until you
   have read the design and understood the contracts.
3. **Read the working code** — `XX_system/code/*.py`. The implementation is
   intentionally compact; comments point to the design doc.
4. **Start the service** — `python3 XX_system/code/app.py`. Hit it with curl.
5. **Do the exercises** — `exercises/XX_exercises.md`. Extend the system
   (add caching, add a feature, etc.).

## Prerequisites

- Python 3.10+
- Packages: `pip install -r scripts/requirements.txt`
- ~200 MB free disk (sample data + caches)

## How long does it take?

Plan for ~1 hour per module:
- 20 min reading the design
- 20 min reading & running the code
- 20 min doing the exercises

## Where to go next

After finishing the course, look at `data-enginnering-cloudvala/course-curricula/`
for a complementary data-warehousing + cloud data engineering track.
