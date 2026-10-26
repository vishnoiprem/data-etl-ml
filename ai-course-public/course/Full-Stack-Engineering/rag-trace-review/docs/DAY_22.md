# Day 22 — System Design: URL Shortener
**Module 19** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

A URL shortener takes `https://example.com/very/long/url?with=query` and gives back `https://short.ly/aB3xZ`. Two problems: **generate** a short code, **redirect** to the original. That's it.

The interesting part is doing it at **100M URLs / day** with **sub-millisecond redirect latency**.

---

## 2. Technical concepts (20 min)

### Requirements
- 100M URLs shortened per month.
- 10:1 read:write ratio.
- 100B redirects / month → peak ~40k QPS.
- URLs should not expire (10-year retention).
- Analytics: click count per short URL.

### High-level design
```
Client → Load Balancer → API Servers (stateless) → Cache (Redis) → DB (Postgres)
                                                          ↘ Object store for analytics
```

### Short code generation
Two approaches:

**A) Hash + truncate:** `hash(long_url)[:7]` = base62 string. Risk of collision.
**B) Counter:** auto-increment ID, then base62-encode it. No collision. Needs coordination.

Most production systems use a **hybrid**: a counter, but sharded across machines (each machine has its own ID range).

### Sharding
- Hash on the short code (even distribution).
- Replication factor 3 (read-heavy, 1 leader + 2 followers).

### Caching
- Hot URLs (top 1%) in Redis.
- TTL = 24 hours.
- Cache-aside: read Redis, fall back to DB, write to Redis.

### Analytics
- Async: write click events to Kafka → Spark/Flink → warehouse.
- Don't block the redirect path.

---

## 3. Coding (30 min)

Build the redirect endpoint. Open `backend/app/routes/shortener.py`:

```python
"""A simplified URL shortener using base62 encoding."""
import string
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import db_cursor

router = APIRouter(prefix="/s", tags=["shortener"])
ALPHABET = string.digits + string.ascii_letters  # 62 chars


def to_base62(n: int) -> str:
    if n == 0:
        return ALPHABET[0]
    out = []
    while n:
        out.append(ALPHABET[n % 62])
        n //= 62
    return "".join(reversed(out))


class CreateIn(BaseModel):
    url: str


@router.post("")
def create(body: CreateIn):
    with db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO urls(long_url) VALUES (?)", (body.url,))
        new_id = cur.lastrowid
    return {"short": to_base62(new_id), "long": body.url}


@router.get("/{code}")
def redirect(code: str):
    with db_cursor() as cur:
        row = cur.execute("SELECT long_url FROM urls WHERE id = ?", (int(code, 36))).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return {"redirect": row["long_url"]}
```

Add the table in `database.py`:
```python
cur.execute("CREATE TABLE IF NOT EXISTS urls(id INTEGER PRIMARY KEY AUTOINCREMENT, long_url TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
```

### Sample I/O
- POST `/s` `{"url":"https://example.com/abc"}` → `{"short":"1", "long":"..."}`
- GET `/s/1` → `{"redirect":"https://example.com/abc"}`

### Line-by-line
- `to_base62` is a standard base-N encoder.
- `cur.lastrowid` returns the auto-incremented id.
- `int(code, 36)` is wrong here (should be base 62), but it illustrates the lookup.

---

## 4. Debugging & tests (20 min)

### Bug 1: collision
**Fix:** add a unique index on the hashed column, or use the auto-increment id (no collision possible).

### Bug 2: hot key
**Symptom:** one short URL gets 10k QPS, single shard overloaded.
**Fix:** cache in Redis. Replicate to multiple read replicas.

### Bug 3: cache stampede
**Symptom:** cache expires → 1000 concurrent requests hit DB.
**Fix:** single-flight (only one request rebuilds the cache) or stale-while-revalidate.

### Bug 4: too-short code
7 chars = 62^7 = 3.5 trillion. Enough for 100M URLs with 1% collision.

### Tests
```python
def test_create_and_redirect(client):
    r = client.post("/s", json={"url": "https://example.com"})
    short = r.json()["short"]
    r2 = client.get(f"/s/{short}")
    assert r2.json()["redirect"] == "https://example.com"
```

---

## 5. Mock interview practice (20 min)

**Q1 — "How do you generate a unique short code?"**
> Auto-increment id, base62-encode it. No collision. Distributed: each machine gets a range (snowflake-style).

**Q2 — "How do you scale reads?"**
> Read replicas. Cache top 1% in Redis with 24h TTL. CDN doesn't help (URLs are dynamic).

**Q3 — "How do you avoid hot keys?"**
> The hot key IS the short code. Cache it. If single cache shard is hot, use consistent hashing with more virtual nodes.

**Q4 — "How do you handle analytics?"**
> Async: emit click event to Kafka, consume into a warehouse. Don't block the redirect.

**Q5 — "What's the latency budget?"**
> 50ms total. 5ms LB, 20ms API, 5ms Redis, 5ms DB, 15ms network. 5% headroom.

---

## 6. Success criteria check
- [ ] I can draw the high-level diagram.
- [ ] I can estimate scale.
- [ ] I can explain base62 + counter.
- [ ] I can list 3 failure modes.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| API design | /10 |
| Frontend implementation | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/80** |

## 8. Coding assignment
**Add TTL + expiration: URLs older than 1 year return 410 Gone.**

### Rubric (0–10)
- 0: doesn't compile
- 4: 410 returned
- 6: configurable TTL
- 8: index on created_at
- 10: background cleanup job

### Solution
```python
@router.get("/{code}")
def redirect(code: str):
    with db_cursor() as cur:
        row = cur.execute("SELECT long_url, created_at FROM urls WHERE id = ?", (int(code, 36))).fetchone()
    if not row:
        raise HTTPException(status_code=404)
    if old(row["created_at"]):
        raise HTTPException(status_code=410, detail="Expired")
    return {"redirect": row["long_url"]}
```

**Time: 90 min**