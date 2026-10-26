"""Generate 10,000 synthetic RAG traces."""
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from app.database import db_cursor, init_db  # noqa: E402

PROMPT_VERSIONS = ["v1.0", "v1.1", "v1.2", "v2.0"]
QUERIES = [
    "What is RAG?",
    "How does retrieval augmented generation work?",
    "Explain vector databases.",
    "What is the difference between fine-tuning and RAG?",
    "How do embeddings work?",
    "Best practices for prompt engineering.",
    "What is cosine similarity?",
    "How to evaluate retrieval quality?",
    "What is chunking strategy?",
    "Explain hybrid search.",
]
SOURCES = ["wiki.md", "docs.pdf", "blog.md", "faq.md", "manual.pdf"]


def main(n: int = 10_000) -> None:
    random.seed(42)
    init_db()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows: list[tuple] = []
    feedbacks: list[tuple] = []
    for i in range(n):
        ts = (base + timedelta(minutes=random.randint(0, 60 * 24 * 30))).isoformat()
        pv = random.choice(PROMPT_VERSIONS)
        q = random.choice(QUERIES)
        chunks = [
            {"chunk_id": f"c{j}", "text": f"chunk {j} of {q}", "score": round(random.random(), 3)}
            for j in range(random.randint(2, 5))
        ]
        citations = [
            {"chunk_id": c["chunk_id"], "source": random.choice(SOURCES), "score": c["score"]}
            for c in chunks
        ]
        latency = random.randint(50, 4500)
        tokens = random.randint(100, 4000)
        status = random.choices(["ok", "error"], weights=[0.95, 0.05])[0]
        rows.append(
            (
                f"trace_{i:06d}",
                ts,
                pv,
                q,
                f"Prompt template {pv}: {{query}}",
                json.dumps(chunks),
                f"Model answer for: {q}",
                json.dumps(citations),
                tokens,
                latency,
                status,
                None,
            )
        )
        if random.random() < 0.3:
            rating = random.choice(["up", "down"])
            feedbacks.append(
                (f"trace_{i:06d}", rating, None, ts)
            )

    with db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM feedback")
        cur.execute("DELETE FROM traces")
        cur.executemany(
            """
            INSERT INTO traces(trace_id, created_at, prompt_version, user_query, prompt,
                               retrieved_chunks, model_response, citations,
                               token_usage, latency_ms, status, feedback)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            rows,
        )
        cur.executemany(
            "INSERT INTO feedback(trace_id, rating, note, created_at) VALUES (?,?,?,?)",
            feedbacks,
        )
    print(f"Inserted {n} traces and {len(feedbacks)} feedback rows.")


if __name__ == "__main__":
    main()