"""Generate generic exercises for any module that doesn't have one yet.

Reads the module directory, examines the design doc + code, and writes
a templated exercises file. The author can edit it to make it specific.
"""

from __future__ import annotations

import sys
from pathlib import Path

TEMPLATE = '''# Exercises — {title}

Pick 3-5 of these to extend the system. Each one is a real feature a
production {short_title} has. Implementing them will teach you more
about the design than re-reading the doc.

## 1. Add metrics for cache hit rate
Expose the cache's hit_rate at `/metrics`; add a counter for misses.

## 2. Add a pagination cursor
Replace `?limit=` with `?cursor=<id>&limit=` so clients can page
through without offset drift.

## 3. Add per-user rate limiting
Reuse the **Rate Limiter** module (14_rate_limiter). Apply 60 req/min
per IP. Return 429 with Retry-After.

## 4. Add persistence audit
The KeyValueStore is JSON-on-disk. Add a write-ahead log so a crash
mid-write doesn't corrupt state.

## 5. Add structured logging
Emit a JSON line per request: `{{ts, ip, method, path, status,
latency_ms, request_id}}`. Pipe to file; demo a grep for 5xx.

## 6. Add a /health/ready vs /health/live split
`/health/live` = process is up. `/health/ready` = downstream
dependencies (storage, cache) are reachable. Use both at the LB.

## 7. Add an integration test
Spin up two service instances; have one call the other; verify the
end-to-end contract.

## 8. Add a "bulk" endpoint
Accept N items in one request. Use `gunicorn` with `gthread` workers
to handle concurrency; benchmark the improvement.
'''


def main(modules: list[str]) -> None:
    root = Path(__file__).resolve().parent.parent
    out = root / "exercises"
    out.mkdir(parents=True, exist_ok=True)
    for m in modules:
        title = m.split("_", 1)[1].replace("_", " ").title() if "_" in m else m
        # nicer titles
        title_map = {
            "twitter": "Twitter / X",
            "typeahead": "Typeahead / Search Suggest",
            "instagram": "Instagram",
            "yt_or_netflix": "YouTube / Netflix",
            "kv_store": "Key-Value Store",
            "rate_limiter": "Rate Limiter",
            "distributed_lru": "Distributed LRU Cache",
            "dropbox": "Dropbox",
            "s3_storage": "S3 Object Storage",
            "ticketmaster": "Ticketmaster",
            "hotel_booking": "Hotel Booking",
            "parking_garage": "Parking Garage",
            "metrics_logging": "Metrics & Logging Service",
            "apm": "Application Performance Monitoring",
            "doc_processing": "Document Processing Pipeline",
            "zillow": "Zillow",
            "weather_app": "Weather App",
            "messenger": "Facebook Messenger",
            "whatsapp": "WhatsApp",
            "chess": "Chess.com",
            "slack": "Slack",
            "google_docs": "Google Docs",
            "tiktok": "TikTok",
            "twitch": "Twitch",
            "ai_support": "AI Customer Support",
            "chatgpt": "ChatGPT",
            "file_uploader": "AI File Uploader",
            "llm_batching": "LLM Query Batching",
            "claude_code": "Claude Code",
            "voice_ai": "Real-Time Voice AI",
            "reddit_homepage": "Reddit Homepage",
            "url_shortener": "URL Shortener",
            "message_queue": "Distributed Message Queue",
            "webhook_delivery": "Webhook Delivery",
            "uber_eats": "Uber Eats",
            "web_crawler": "Web Crawler",
            "job_scheduler": "Job Scheduler",
            "user_data_export": "User Data Export",
            "newsfeed": "Newsfeed",
        }
        # strip the leading number prefix
        short = m.split("_", 1)[1] if "_" in m else m
        long_title = title_map.get(short, title)
        path = out / f"{m}_exercises.md"
        if path.exists():
            continue
        path.write_text(TEMPLATE.format(title=long_title, short_title=long_title))
        print(f"wrote {path}")


if __name__ == "__main__":
    modules = sys.argv[1:] or [
        "04_twitter", "05_newsfeed", "06_yt_or_netflix",
        "07_message_queue", "08_webhook_delivery", "09_uber_eats",
        "10_web_crawler", "11_job_scheduler", "12_user_data_export",
        "13_kv_store", "14_rate_limiter", "15_distributed_lru",
        "16_dropbox", "17_s3_storage",
        "18_ticketmaster", "19_hotel_booking", "20_parking_garage",
        "21_metrics_logging", "22_apm", "23_doc_processing",
        "24_zillow", "25_weather_app",
        "26_messenger", "27_whatsapp", "28_chess", "29_slack", "30_google_docs",
        "31_tiktok", "32_twitch",
        "33_ai_support", "34_chatgpt", "35_file_uploader",
        "36_llm_batching", "37_claude_code", "38_voice_ai",
        "39_reddit_homepage",
    ]
    main(modules)
