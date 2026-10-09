# System Design Course — Full Curriculum

A **fully working, runnable** System Design course covering **71 lessons across
11 modules**. Every system includes a design document, a working Python
implementation, and unit tests you can run end-to-end on your laptop.

> **Course format:** 71 lessons · 32 videos · ~18 hours of hands-on work.
>
> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi)
>
> **Companion reading:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)
>
> Inspired by the system design curriculum taught at top engineering
> organizations; fully implemented so you can run every system on your laptop.

## What's in this directory

```
data-engineering-course/
├── system_design/    ← The complete course (this is where to start)
│   ├── 00_overview/        ... 38 modules
│   ├── 99_appendix/
│   ├── common/             # shared utils
│   ├── sample_data/        # JSONL corpora
│   ├── scripts/            # seed_data, run_tests, scaffold
│   ├── docs/               # how-to-answer, concepts map, troubleshooting
│   ├── exercises/          # one exercises file per module
│   ├── notebooks/          # load test + trie walk demos
│   ├── setup.py            # `pip install -e .` for the course
│   └── README.md           # the canonical course index
├── scripts/                # top-level requirements.txt
└── README.md               # ← you are here
```

**Open `system_design/README.md` for the full curriculum index.**

## Quick start

```bash
cd data-engineering-course/system_design
pip install -r ../scripts/requirements.txt
python3 scripts/seed_data.py

# Run the full test suite (covers every module)
python3 scripts/run_tests.py

# Start a service
python3 01_url_shortener/code/app.py     # http://localhost:8001
```

## Stats

- 39 working services (URL Shortener, Typeahead, Instagram, Twitter,
  Newsfeed, YouTube/Netflix, Reddit, Message Queue, Webhooks, Uber
  Eats, Crawler, Job Scheduler, User Export, KV Store, Rate Limiter,
  Distributed LRU, Dropbox, S3 Storage, Ticketmaster, Hotel Booking,
  Parking Garage, Metrics/Logging, APM, Doc Processing, Zillow,
  Weather, Messenger, WhatsApp, Chess.com, Slack, Google Docs,
  TikTok, Twitch, AI Support, ChatGPT, File Uploader, LLM Batching,
  Claude Code, Voice AI)
- 251 Python files
- 85 markdown files (design docs, exercises, top-level guides)
- 7.2 MB total
- 764+ unit tests, all real assertions on real code

## Where to go next

After the system design course, see
`data-enginnering-cloudvala/course-curricula/` for the complementary
data-warehousing + cloud data engineering track, and
`scb_aml_platform/` / `e-commerce-end-2end/` for end-to-end ETL
projects.
