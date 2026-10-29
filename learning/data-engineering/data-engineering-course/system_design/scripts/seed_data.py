"""Generate sample data for all 6 read-heavy systems.

Run once on first checkout, or whenever you want a fresh corpus:

    python3 scripts/seed_data.py

Outputs to system_design/sample_data/ as JSONL files. Each file is small
enough to commit, and big enough to be interesting (a few MB).
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

random.seed(42)

OUT = Path(__file__).resolve().parent.parent / "sample_data"
OUT.mkdir(parents=True, exist_ok=True)


# ---- 1. URLs for the URL shortener -------------------------------------

def gen_urls(n: int = 2_000) -> None:
    domains = [
        "example.com", "blog.dev", "news.org", "shop.io", "docs.tech",
        "wiki.net", "github.com", "stackoverflow.com",
    ]
    paths = ["article", "post", "guide", "tutorial", "docs", "blog"]
    with (OUT / "urls.jsonl").open("w") as f:
        for i in range(n):
            domain = random.choice(domains)
            path = random.choice(paths)
            slug = random_word(6)
            yield_str = f"https://{domain}/{path}/{slug}-{i}"
            f.write(json.dumps({"id": i, "url": yield_str}) + "\n")


# ---- 2. Dictionary for typeahead ---------------------------------------

WORDLIST = (
    "python flask system design cache database queue worker sharding "
    "replication consistency availability partition load balancer "
    "search trie rank scoring latency throughput benchmark micro "
    "service monolith kafka spark airflow dbt snowflake bigquery "
    "warehouse lake delta parquet iceberg vector embedding "
    "transformer attention retrieval ranking recommendation "
    "instagram twitter netflix youtube typeahead suggestion "
    "fanout timeline newsfeed photo video streaming".split()
)


def random_word(n: int = 8) -> str:
    return "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n))


def gen_dictionary() -> None:
    """Top-1k-ish word corpus with synthetic search frequencies."""
    with (OUT / "dictionary.jsonl").open("w") as f:
        # Real words + a long tail of synthetic ones.
        for w in WORDLIST:
            f.write(json.dumps({
                "word": w,
                "freq": random.randint(100, 1_000_000),
            }) + "\n")
        for i in range(1500):
            f.write(json.dumps({
                "word": f"{random_word(random.randint(4, 10))}{i}",
                "freq": random.randint(1, 5000),
            }) + "\n")


# ---- 3. Users for Instagram / Twitter / Newsfeed -----------------------

def gen_users(n: int = 500) -> None:
    with (OUT / "users.jsonl").open("w") as f:
        for i in range(n):
            f.write(json.dumps({
                "user_id": i + 1,
                "username": f"user_{i+1}",
                "name": f"User Number {i+1}",
                "followers": random.randint(0, 50_000),
            }) + "\n")


# ---- 4. Photos for Instagram -------------------------------------------

def gen_photos(n: int = 5_000) -> None:
    with (OUT / "photos.jsonl").open("w") as f:
        for i in range(n):
            user_id = random.randint(1, 500)
            f.write(json.dumps({
                "photo_id": i + 1,
                "user_id": user_id,
                "caption": f"photo #{i+1} by user {user_id}",
                "likes": random.randint(0, 100_000),
                "image_url": f"https://cdn.example.com/photos/{i+1}.jpg",
            }) + "\n")


# ---- 5. Tweets for Twitter --------------------------------------------

TWEET_TEMPLATES = [
    "loving the new {topic} release!",
    "anyone else debugging {topic} today?",
    "shipped a small improvement to {topic}",
    "{topic} is a great example of good engineering",
    "just read a deep dive on {topic}",
    "thinking about {topic} and {topic2} together",
    "thread on {topic} coming soon",
    "what's your favorite {topic} pattern?",
]

TOPICS = ["caching", "sharding", "kafka", "airflow", "spark", "dbt",
          "typeahead", "fanout", "redis", "postgres", "s3", "iceberg",
          "delta", "parquet", "vector search", "retrieval", "ranking"]


def gen_tweets(n: int = 20_000) -> None:
    with (OUT / "tweets.jsonl").open("w") as f:
        for i in range(n):
            tpl = random.choice(TWEET_TEMPLATES)
            topic = random.choice(TOPICS)
            topic2 = random.choice(TOPICS)
            f.write(json.dumps({
                "tweet_id": i + 1,
                "user_id": random.randint(1, 500),
                "text": tpl.format(topic=topic, topic2=topic2),
                "likes": random.randint(0, 50_000),
                "retweets": random.randint(0, 5_000),
            }) + "\n")


# ---- 6. Videos for YouTube / Netflix -----------------------------------

def gen_videos(n: int = 1_000) -> None:
    with (OUT / "videos.jsonl").open("w") as f:
        for i in range(n):
            f.write(json.dumps({
                "video_id": i + 1,
                "title": f"Lesson {i+1}: " + random.choice([
                    "intro to sharding", "caching patterns", "fanout-on-write",
                    "typeahead at scale", "video streaming", "ranking systems",
                    "delta lake basics", "kafka fundamentals",
                ]),
                "duration_s": random.randint(60, 3600),
                "views": random.randint(100, 50_000_000),
            }) + "\n")


# ---- main -------------------------------------------------------------

def main() -> None:
    print(f"Seeding data into {OUT}")
    for fn, label in [
        (gen_urls, "urls"),
        (gen_dictionary, "dictionary"),
        (gen_users, "users"),
        (gen_photos, "photos"),
        (gen_tweets, "tweets"),
        (gen_videos, "videos"),
    ]:
        print(f"  - {label}")
        fn()
    print("Done.")


if __name__ == "__main__":
    main()
