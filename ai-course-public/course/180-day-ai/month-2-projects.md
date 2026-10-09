# Month 2: AI + REST APIs — 30 Days of Hands-On Projects
### Theme: "Build an AI that can call any API"

**Data system:** REST APIs + Webhooks (GitHub, Stripe, Slack, Notion, Linear, OpenWeather)
**Tools:** Python 3.10+, OpenAI/Anthropic API, httpx, FastAPI, ngrok, Redis (caching)
**Setup time:** 30 min (one time)
**Time per project:** 30-90 min
**Total time:** ~25 hours over 30 days

---

## Setup (do this once, before Day 31)

```bash
mkdir ai-daily && cd ai-daily
python -m venv venv && source venv/bin/activate
pip install openai httpx fastapi uvicorn redis python-dotenv pydantic
echo "OPENAI_API_KEY=sk-..." > .env
echo "GITHUB_TOKEN=ghp_..." >> .env
echo "STRIPE_KEY=sk_test_..." >> .env
echo "SLACK_BOT_TOKEN=xoxb-..." >> .env
echo "NOTION_TOKEN=secret_..." >> .env
echo "OPENWEATHER_KEY=..." >> .env
```

Create a shared `clients.py`:

```python
# clients.py
import os
from openai import OpenAI
import httpx

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def http_client(timeout: float = 30.0) -> httpx.Client:
    return httpx.Client(timeout=timeout, headers={"User-Agent": "ai-daily/1.0"})
```

---

## Day 31: Function-Calling Weather Agent (30 min)

**Project:** Build an LLM agent that uses OpenAI function calling to fetch real weather from OpenWeather.

```python
# day31_weather_agent.py
import json
from openai import OpenAI
import httpx
import os

client = OpenAI()

WEATHER_FUNCTIONS = [
    {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Tokyo'"},
                "units": {"type": "string", "enum": ["metric", "imperial"], "default": "metric"}
            },
            "required": ["city"]
        }
    }
]

def get_weather(city: str, units: str = "metric") -> dict:
    key = os.environ["OPENWEATHER_KEY"]
    r = httpx.get(
        f"http://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": key, "units": units},
        timeout=10.0,
    )
    r.raise_for_status()
    return r.json()

def ask(question: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}],
        functions=WEATHER_FUNCTIONS,
        function_call="auto",
    )
    msg = resp.choices[0].message
    if msg.function_call:
        args = json.loads(msg.function_call.arguments)
        weather = get_weather(**args)
        follow = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": question},
                msg,
                {"role": "function", "name": "get_weather", "content": json.dumps(weather)},
            ],
        )
        return follow.choices[0].message.content
    return msg.content

print(ask("What's the weather in Tokyo right now? Should I bring an umbrella?"))
```

**Stretch:** Add forecast function, multi-city comparison, unit auto-detection.
**Architect note:** Function calling is a contract with the model — schema quality drives reliability. Always include descriptions and enums.

---

## Day 32: GitHub PR Summarizer (30 min)

```python
# day32_github_pr.py
import os
from openai import OpenAI
import httpx

client = OpenAI()
GH_TOKEN = os.environ["GITHUB_TOKEN"]

def list_prs(repo: str, state: str = "open") -> list[dict]:
    r = httpx.get(
        f"https://api.github.com/repos/{repo}/pulls",
        params={"state": state, "per_page": 20},
        headers={"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"},
    )
    r.raise_for_status()
    return r.json()

def summarize_pr(pr: dict) -> str:
    diff = httpx.get(
        pr["diff_url"], headers={"Authorization": f"Bearer {GH_TOKEN}"}
    ).text[:6000]
    prompt = f"""Summarize this PR for a busy tech lead.
Title: {pr['title']}
Author: {pr['user']['login']}
Files changed: {pr['changed_files']}, +{pr['additions']} -{pr['deletions']}

Diff (truncated):
{diff}

Format:
- One-line summary
- What changed (bullets)
- Risk areas
- Suggested reviewers"""

    return client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content

if __name__ == "__main__":
    for pr in list_prs("anthropics/anthropic-sdk-python")[:3]:
        print(f"\n=== {pr['title']} ===")
        print(summarize_pr(pr))
```

**Stretch:** Add review-comment summarization, post summary as PR comment via API, label suggestions.
**Architect note:** GitHub's secondary rate limits (abuse-detection) will block you if you poll. Use conditional requests with `ETag`/`If-None-Match`.

---

## Day 33: Slack Message Classifier + Router (45 min)

```python
# day33_slack_classifier.py
import os
import json
from openai import OpenAI
import httpx

client = OpenAI()
SLACK = os.environ["SLACK_BOT_TOKEN"]

CATEGORIES = ["bug", "feature_request", "question", "praise", "spam", "urgent"]

def fetch_messages(channel: str, limit: int = 30) -> list[dict]:
    r = httpx.get(
        "https://slack.com/api/conversations.history",
        params={"channel": channel, "limit": limit},
        headers={"Authorization": f"Bearer {SLACK}"},
    )
    r.raise_for_status()
    return r.json()["messages"]

def classify(text: str) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Classify into one of: {CATEGORIES}. Return JSON: {{\"category\": \"...\", \"confidence\": 0.0-1.0, \"reason\": \"...\"}}"},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)

def route(message: dict, classification: dict):
    """Forward urgent/bug messages to an on-call channel."""
    if classification["category"] in ("urgent", "bug"):
        httpx.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {SLACK}"},
            json={
                "channel": "#ai-triage",
                "text": f"[{classification['category'].upper()}] {message['text']}\n> {classification['reason']}",
            },
        )

if __name__ == "__main__":
    for msg in fetch_messages("C12345"):
        if msg.get("text"):
            c = classify(msg["text"])
            print(f"{c['category']:8s} ({c['confidence']:.2f}) {msg['text'][:60]}")
            route(msg, c)
```

**Stretch:** Per-channel classifier fine-tuning, auto-thread reply, sentiment trend over time.
**Architect note:** Slack tokens scope permissions narrowly. Use a `chat:write` bot token, never a user token, for production bots.

---

## Day 34: Stripe Payment Analytics (45 min)

```python
# day34_stripe_analytics.py
import os
import json
from openai import OpenAI
import httpx

client = OpenAI()
STRIPE = os.environ["STRIPE_KEY"]

def list_charges(limit: int = 100) -> list[dict]:
    r = httpx.get(
        "https://api.stripe.com/v1/charges",
        params={"limit": limit},
        headers={"Authorization": f"Bearer {STRIPE}"},
    )
    r.raise_for_status()
    return r.json()["data"]

def list_subscriptions() -> list[dict]:
    r = httpx.get(
        "https://api.stripe.com/v1/subscriptions",
        params={"limit": 100, "status": "all"},
        headers={"Authorization": f"Bearer {STRIPE}"},
    )
    r.raise_for_status()
    return r.json()["data"]

def analyze() -> str:
    charges = list_charges()
    subs = list_subscriptions()
    summary = {
        "total_revenue_cents": sum(c["amount"] for c in charges if c["paid"]),
        "failed_count": sum(1 for c in charges if c["status"] == "failed"),
        "active_subs": sum(1 for s in subs if s["status"] == "active"),
        "mrr_cents": sum(s["plan"]["amount"] for s in subs if s["status"] == "active"),
        "top_customers": sorted(
            [{"email": c["billing_details"]["email"], "amount": c["amount"]} for c in charges],
            key=lambda x: -x["amount"],
        )[:5],
    }
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a finance analyst. Given Stripe data, identify risks, growth opportunities, and write a 1-paragraph executive summary."},
            {"role": "user", "content": json.dumps(summary, indent=2)},
        ],
    ).choices[0].message.content

print(analyze())
```

**Stretch:** MRR-by-plan breakdown, churn prediction, refund-fraud scoring.
**Architect note:** Stripe's list endpoints paginate — use `has_more` + `starting_after` for >100 records. Cache the result; this endpoint is rate-limited.

---

## Day 35: Notion Page Q&A (45 min)

```python
# day35_notion_qa.py
import os
import json
from openai import OpenAI
import httpx

client = OpenAI()
NOTION = os.environ["NOTION_TOKEN"]

def search_pages(query: str) -> list[dict]:
    r = httpx.post(
        "https://api.notion.com/v1/search",
        headers={
            "Authorization": f"Bearer {NOTION}",
            "Notion-Version": "2022-06-28",
        },
        json={"query": query, "filter": {"property": "object", "value": "page"}},
    )
    r.raise_for_status()
    return r.json()["results"]

def get_page_text(page_id: str) -> str:
    r = httpx.get(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers={"Authorization": f"Bearer {NOTION}", "Notion-Version": "2022-06-28"},
    )
    r.raise_for_status()
    parts = []
    for b in r.json()["results"]:
        t = b.get(b["type"], {}).get("rich_text", [])
        parts.append("".join(x["plain_text"] for x in t))
    return "\n".join(parts)

def ask(question: str) -> str:
    candidates = search_pages(question)[:5]
    context_parts = []
    for p in candidates:
        title = p["properties"].get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
        body = get_page_text(p["id"])[:2000]
        context_parts.append(f"### {title}\n{body}")
    context = "\n\n".join(context_parts)
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Answer the user's question using only these Notion pages. Cite the title.\n\n{context}"},
            {"role": "user", "content": question},
        ],
    ).choices[0].message.content

print(ask("What is our Q3 OKR?"))
```

**Stretch:** Recursive sub-page traversal, block-type-specific handling, sync to a vector index.
**Architect note:** Notion block fetches paginate and the rate limit is ~3 req/s. Use a queue worker for bulk imports.

---

## Day 36: Linear Issue Triager (45 min)

```python
# day36_linear_triager.py
import os
import json
from openai import OpenAI
import httpx

client = OpenAI()
LINEAR = os.environ["LINEAR_API_KEY"]

def gql(query: str, variables: dict = None) -> dict:
    r = httpx.post(
        "https://api.linear.app/graphql",
        headers={"Authorization": LINEAR, "Content-Type": "application/json"},
        json={"query": query, "variables": variables or {}},
    )
    r.raise_for_status()
    return r.json()["data"]

def fetch_issues(team: str = "ENG") -> list[dict]:
    return gql(f"""
        query {{ issues(filter: {{ team: {{ key: {{ eq: "{team}" }} }}, state: {{ type: {{ eq: "unstarted" }} }} }}, first: 25) {{
            nodes {{ id title description priority labels {{ nodes {{ name }} }} }}
        }} }}
    """)["issues"]["nodes"]

def triage(issue: dict) -> dict:
    return json.loads(client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """You are a senior engineering manager. Triage this Linear issue.
Return JSON: {"priority": 0-4, "labels": [...], "estimate_days": N, "assignee_suggestion": "frontend|backend|devops|data", "reasoning": "..."}"""},
            {"role": "user", "content": f"Title: {issue['title']}\nDescription: {issue.get('description', '')[:1500]}"},
        ],
        response_format={"type": "json_object"},
    ).choices[0].message.content)

if __name__ == "__main__":
    for issue in fetch_issues():
        result = triage(issue)
        print(f"[P{result['priority']}] {issue['title'][:60]} → {result['assignee_suggestion']}")
```

**Stretch:** Auto-apply labels via mutation, comment the reasoning on the issue, weekly triage digest.
**Architect note:** Linear's GraphQL schema is excellent but their rate limit is generous (~1500 req/hour). Batch with `first: 50`.

---

## Day 37: WEEKEND — Multi-API Personal Dashboard (3 hours)

Combine Days 31-36 into a FastAPI + Streamlit app:
- One page = one data source (Weather, GitHub, Stripe, Slack, Notion, Linear)
- Auth via OAuth so each user connects their own accounts
- Auto-refresh every 5 min
- Deploy to Railway; share the URL

**Architect note:** A unified dashboard across many APIs is a "data integration hub" — the harder problems are auth-state management and per-user token isolation, not the LLM call itself.

---

## Day 38: Async API Client (45 min)

```python
# day38_async_client.py
import asyncio
import httpx
import os
import time

API = "https://jsonplaceholder.typicode.com"

async def fetch(client: httpx.AsyncClient, path: str) -> dict:
    r = await client.get(f"{API}/{path}")
    r.raise_for_status()
    return r.json()

async def main():
    async with httpx.AsyncClient(timeout=10) as client:
        # Sequential
        start = time.time()
        for i in range(10):
            await fetch(client, f"posts/{i+1}")
        seq = time.time() - start

        # Concurrent
        start = time.time()
        await asyncio.gather(*[fetch(client, f"posts/{i+1}") for i in range(10)])
        conc = time.time() - start

        print(f"Sequential: {seq:.2f}s, Concurrent: {conc:.2f}s, speedup: {seq/conc:.1f}x")

asyncio.run(main())
```

**Stretch:** Per-host connection pool tuning, semaphore-based concurrency limit.
**Architect note:** httpx's `Limits(max_connections=100)` caps concurrency — without it, async turns into "thundering herd against the API."

---

## Day 39: Parallel API Calls with gather (45 min)

```python
# day39_parallel_gather.py
import asyncio
import httpx
from openai import OpenAI
import os

client = OpenAI()
GH = os.environ["GITHUB_TOKEN"]

async def get_repo(client: httpx.AsyncClient, repo: str) -> dict:
    r = await client.get(
        f"https://api.github.com/repos/{repo}",
        headers={"Authorization": f"Bearer {GH}"},
    )
    r.raise_for_status()
    return r.json()

async def main():
    repos = ["python/cpython", "anthropics/anthropic-sdk-python", "openai/openai-python",
             "microsoft/vscode", "torvalds/linux"]
    async with httpx.AsyncClient(timeout=15) as c:
        results = await asyncio.gather(*[get_repo(c, r) for r in repos],
                                       return_exceptions=True)
    for repo, data in zip(repos, results):
        if isinstance(data, Exception):
            print(f"  ❌ {repo}: {data}")
        else:
            print(f"  ⭐ {data['stargazers_count']:>7,}  {repo}")

asyncio.run(main())
```

**Stretch:** `return_exceptions=True` + retry, `asyncio.TaskGroup` (3.11+), backpressure with `asyncio.Semaphore`.
**Architect note:** `gather` without `return_exceptions=True` will short-circuit the whole batch on a single failure. Always pass it for production.

---

## Day 40: Retry with Exponential Backoff (45 min)

```python
# day40_retry_backoff.py
import httpx
import time
import random
from functools import wraps

RETRY_STATUS = {429, 500, 502, 503, 504}

def retry(max_attempts: int = 5, base: float = 0.5, max_wait: float = 30.0):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    r = fn(*args, **kwargs)
                    if r.status_code not in RETRY_STATUS:
                        return r
                    if r.status_code == 429:
                        wait = float(r.headers.get("Retry-After", base * (2 ** attempt)))
                    else:
                        wait = min(base * (2 ** attempt) + random.random() * 0.1, max_wait)
                except httpx.TransportError as e:
                    wait = min(base * (2 ** attempt) + random.random() * 0.1, max_wait)
                    r = None
                if attempt < max_attempts - 1:
                    print(f"  retry in {wait:.2f}s (attempt {attempt+1}/{max_attempts})")
                    time.sleep(wait)
            if r is not None:
                r.raise_for_status()
            raise RuntimeError("retries exhausted")
        return wrapper
    return decorator

@retry()
def fetch(url: str) -> httpx.Response:
    return httpx.get(url, timeout=10)

print(fetch("https://httpbin.org/status/500").status_code)
```

**Stretch:** Jitter strategy choice (full vs equal vs decorrelated), circuit breaker integration.
**Architect note:** Full jitter (`random(0, 2^n * base)`) is provably better than exponential without jitter at preventing thundering herd.

---

## Day 41: Rate Limit Handling (45 min)

```python
# day41_rate_limit.py
import httpx
import time

class RateLimiter:
    def __init__(self, requests_per_second: float):
        self.min_interval = 1.0 / requests_per_second
        self.last = 0.0

    def wait(self):
        delta = time.time() - self.last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self.last = time.time()

class TokenBucket:
    def __init__(self, capacity: int, refill_per_sec: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill = refill_per_sec
        self.last = time.time()

    def take(self, n: int = 1) -> bool:
        now = time.time()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.refill)
        self.last = now
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False

# Demo
limiter = RateLimiter(requests_per_second=2)
for i in range(5):
    limiter.wait()
    print(f"req {i} at {time.time():.3f}")
```

**Stretch:** Sliding window, distributed rate limit with Redis, per-API-key buckets.
**Architect note:** Client-side rate limiting is a *courtesy*, not a guarantee. Server-side rate limits still need server-respect (Retry-After headers).

---

## Day 42: Response Caching with Redis (45 min)

```bash
# Setup
docker run -d -p 6379:6379 --name redis redis:7-alpine
pip install redis
```

```python
# day42_redis_cache.py
import json
import hashlib
import os
import redis
import httpx
from functools import wraps

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
TTL = 300  # 5 min

def cache(ttl: int = TTL):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = f"{fn.__name__}:{hashlib.md5(json.dumps((args, kwargs), default=str).encode()).hexdigest()}"
            cached = r.get(key)
            if cached:
                return json.loads(cached)
            result = fn(*args, **kwargs)
            r.setex(key, ttl, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator

@cache(ttl=60)
def get_user_posts(user_id: int) -> list[dict]:
    """Expensive call we want to cache."""
    r = httpx.get(f"https://jsonplaceholder.typicode.com/posts", params={"userId": user_id})
    r.raise_for_status()
    return r.json()

# First call hits API, second call hits cache
import time
start = time.time(); get_user_posts(1); print(f"cold: {time.time()-start:.3f}s")
start = time.time(); get_user_posts(1); print(f"warm: {time.time()-start:.3f}s")
```

**Stretch:** Cache invalidation patterns, stampede protection with locks, cache stampede prevention.
**Architect note:** Cache keys must include all inputs that affect output — including auth context. Cache poisoning across users is a top-3 API bug.

---

## Day 43: Circuit Breaker Pattern (45 min)

```python
# day43_circuit_breaker.py
import time
from enum import Enum
from dataclasses import dataclass, field

class State(Enum):
    CLOSED = "closed"      # normal
    OPEN = "open"          # failing — fail fast
    HALF_OPEN = "half_open"  # testing recovery

@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    state: State = State.CLOSED
    failures: int = 0
    opened_at: float = 0.0

    def call(self, fn, *args, **kwargs):
        if self.state == State.OPEN:
            if time.time() - self.opened_at > self.recovery_timeout:
                self.state = State.HALF_OPEN
            else:
                raise RuntimeError("circuit open")
        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failures = 0
        self.state = State.CLOSED

    def _on_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = State.OPEN
            self.opened_at = time.time()

# Demo
cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
def flaky(n): return 1 / n
for i in [1, 0, 0, 0, 0, 1, 1]:
    try:
        print(cb.call(flaky, i))
    except Exception as e:
        print(f"  err: {type(e).__name__}")
```

**Stretch:** Sliding-window failure detection, per-host breaker, metrics export.
**Architect note:** Circuit breakers protect *your* system, not the upstream. Pair with retries and timeouts, and always log state transitions.

---

## Day 44: WEEKEND — Resilient API Wrapper Library (3 hours)

Package Days 38-43 into a `resilient_client` library with:
- `get(url)` and `post(url, json=...)` 
- Configurable retry, backoff, rate limit, circuit breaker, cache
- 100% typed with Pydantic models
- 30+ unit tests
- Publish to TestPyPI

**Architect note:** A library that's "easy to use, hard to misuse" treats the default config as safe — never let a developer accidentally disable retries in production.

---

## Day 45: Webhook Receiver with FastAPI (45 min)

```python
# day45_webhook_receiver.py
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import os
import json

app = FastAPI()
SECRET = os.environ.get("WEBHOOK_SECRET", "dev-secret")

# In-memory event log (use Redis/Postgres in prod)
EVENTS: list[dict] = []

@app.post("/webhook")
async def receive(request: Request):
    body = await request.body()
    sig = request.headers.get("x-signature", "")
    expected = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=401, detail="bad signature")

    event = json.loads(body)
    EVENTS.append({"type": event.get("type"), "received_at": request.headers.get("date", "")})
    return {"ok": True}

@app.get("/events")
def list_events(limit: int = 20):
    return EVENTS[-limit:]

# Run: uvicorn day45_webhook_receiver:app --reload --port 8000
```

**Stretch:** Persistent event log, dead-letter for malformed events, HMAC helper for senders.
**Architect note:** Always verify signatures *before* parsing JSON. A 401 on bad signature is your first line of defense against spoofed events.

---

## Day 46: Stripe Webhook → AI Categorization (45 min)

```python
# day46_stripe_webhook.py
from fastapi import FastAPI, Request, HTTPException
from openai import OpenAI
import os, stripe, json

client = OpenAI()
app = FastAPI()
stripe.api_key = os.environ["STRIPE_KEY"]
WEBHOOK_SECRET = os.environ["STRIPE_WEBHOOK_SECRET"]

@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="bad sig")

    if event["type"] == "charge.succeeded":
        charge = event["data"]["object"]
        category = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content":
                f"Categorize this Stripe charge: {charge.get('description', '')} "
                f"amount=${charge['amount']/100}. Reply with one of: "
                f"subscription|one_time|refund|dispute|other"}],
        ).choices[0].message.content.strip()
        # Save to your DB
        print(f"charge {charge['id']} → {category}")
    return {"ok": True}
```

**Stretch:** Auto-refund suspicious charges, retry-failed-events endpoint, post-charge analytics.
**Architect note:** Stripe sends the same event multiple times if you 5xx. Make your handler *idempotent* — check `event["id"]` against a seen-events set.

---

## Day 47: GitHub Webhook → AI Code Review (60 min)

```python
# day47_github_webhook.py
from fastapi import FastAPI, Request, HTTPException
import httpx, os
from openai import OpenAI

client = OpenAI()
app = FastAPI()
GH = os.environ["GITHUB_TOKEN"]

@app.post("/github/webhook")
async def gh_webhook(request: Request):
    event = request.headers.get("x-github-event")
    payload = await request.json()
    if event != "pull_request" or payload["action"] not in ("opened", "synchronize"):
        return {"ok": True}

    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    diff = httpx.get(
        pr["diff_url"], headers={"Authorization": f"Bearer {GH}"}
    ).text[:8000]

    review = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content":
            f"Review this PR diff for {repo} PR #{pr['number']} ({pr['title']}).\n"
            f"Identify: bugs, security issues, missing tests, style problems. "
            f"Be specific (file/line if possible). Format as a GitHub comment.\n\n{diff}"}],
    ).choices[0].message.content

    httpx.post(
        f"https://api.github.com/repos/{repo}/issues/{pr['number']}/comments",
        headers={"Authorization": f"Bearer {GH}"},
        json={"body": f"## AI Code Review\n\n{review}"},
    )
    return {"ok": True}
```

**Stretch:** Comment-on-line via review API, severity-tagged findings, exclude bot authors.
**Architect note:** GitHub webhook secret = HMAC of payload. Without verification, anyone can POST and have you review nonexistent PRs (and burn API budget).

---

## Day 48: Slack Webhook → AI Moderation (45 min)

```python
# day48_slack_moderation.py
from fastapi import FastAPI, Request
from openai import OpenAI
import os, httpx

client = OpenAI()
app = FastAPI()
SLACK = os.environ["SLACK_BOT_TOKEN"]

@app.post("/slack/events")
async def slack_events(request: Request):
    body = await request.json()
    if body.get("type") == "url_verification":
        return {"challenge": body["challenge"]}
    if body.get("type") != "event_callback":
        return {"ok": True}
    event = body["event"]
    if event.get("type") != "message" or event.get("subtype") or "text" not in event:
        return {"ok": True}

    text = event["text"]
    verdict = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content":
            f"Moderate this Slack message. Reply JSON with keys: "
            f"action (allow|warn|delete), reason (string), confidence (0-1).\n\n{text}"}],
        response_format={"type": "json_object"},
    ).choices[0].message.content
    import json
    v = json.loads(verdict)
    if v["action"] == "delete":
        httpx.post("https://slack.com/api/chat.delete",
            headers={"Authorization": f"Bearer {SLACK}"},
            params={"channel": event["channel"], "ts": event["ts"]})
    return {"ok": True}
```

**Stretch:** Profanity filter regex pre-check, escalation DM to admins, transparency report.
**Architect note:** Slack requires a 3-second response — async-acknowledge pattern (return 200 immediately, process in background) is mandatory at scale.

---

## Day 49: ngrok for Local Webhooks (30 min)

```bash
# Install
brew install ngrok
ngrok config add-authtoken <your-token>

# Run your local server
uvicorn day45_webhook_receiver:app --port 8000

# In another terminal
ngrok http 8000
# → https://abc123.ngrok.app
```

```python
# day49_ngrok_helper.py
# Print your ngrok URL for use in webhook configs
import httpx
import os

def ngrok_url() -> str:
    r = httpx.get("http://localhost:4040/api/tunnels")
    r.raise_for_status()
    return r.json()["tunnels"][0]["public_url"]

if __name__ == "__main__":
    print(f"Subscribe webhooks to: {ngrok_url()}/webhook")
```

**Stretch:** Multi-tunnel setup, custom subdomain, ngrok + ngrok-edge for production-like TLS.
**Architect note:** ngrok free tier URL changes every restart. For repeatable testing, use a paid plan or a public reverse proxy like `bore.pub`.

---

## Day 50: Webhook Signature Verification (45 min)

```python
# day50_signature_verify.py
import hmac
import hashlib
import time
from typing import Callable

class SignatureVerifier:
    """Generic HMAC-SHA256 signature verification with timestamp window."""

    def __init__(self, secret: str, tolerance_sec: int = 300):
        self.secret = secret.encode()
        self.tolerance = tolerance_sec

    def verify(self, payload: bytes, signature: str, timestamp: str | None = None) -> bool:
        # Replay protection
        if timestamp and abs(time.time() - int(timestamp)) > self.tolerance:
            return False
        # Standard: "sha256=<hex>"
        if signature.startswith("sha256="):
            signature = signature[7:]
        # Stripe-style: "t=<ts>,v1=<hex>"
        if timestamp and "v1=" in signature and "t=" in signature:
            parts = dict(p.split("=", 1) for p in signature.split(","))
            signature = parts["v1"]
            signed_payload = f"{parts['t']}.".encode() + payload
        else:
            signed_payload = payload
        expected = hmac.new(self.secret, signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

# Test
v = SignatureVerifier(secret="my-secret")
sig = hmac.new(b"my-secret", b"hello", hashlib.sha256).hexdigest()
print(v.verify(b"hello", sig))  # True
print(v.verify(b"hello", sig, str(int(time.time()))))  # True
print(v.verify(b"tampered", sig))  # False
```

**Stretch:** Per-source signature schemes (Stripe vs GitHub vs Slack), test vectors.
**Architect note:** `hmac.compare_digest` is constant-time — never use `==` to compare signatures (timing attacks).

---

## Day 51: WEEKEND — Event-Driven AI System (3 hours)

Build a small system that:
- Receives Stripe webhooks → categorizes charge → posts to Slack
- Receives GitHub webhooks → AI code review → posts comment
- Receives Slack messages → moderation → auto-action
- All three share a `webhook_log` table
- FastAPI + SQLite + ngrok
- Deploy with Docker to Fly.io

**Architect note:** A "smart webhook router" pattern: each event has a transformer (parse) and a handler (AI action). This is the same shape as AWS EventBridge + Lambda targets.

---

## Day 52: OAuth 2.0 Flow with GitHub (60 min)

```python
# day52_oauth_github.py
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import httpx, os
import secrets

app = FastAPI()
CLIENT_ID = os.environ["GITHUB_OAUTH_CLIENT_ID"]
CLIENT_SECRET = os.environ["GITHUB_OAUTH_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:8000/auth/callback"

# In-memory store for state -> user (use Redis in prod)
STATES: dict[str, str] = {}

@app.get("/auth/login")
def login():
    state = secrets.token_urlsafe(16)
    STATES[state] = ""
    url = (f"https://github.com/login/oauth/authorize"
           f"?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&state={state}&scope=repo,user")
    return RedirectResponse(url)

@app.get("/auth/callback")
async def callback(request: Request):
    code = request.query_params["code"]
    state = request.query_params["state"]
    if state not in STATES:
        return {"error": "bad state"}
    r = httpx.post("https://github.com/login/oauth/access_token",
        data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code},
        headers={"Accept": "application/json"})
    token = r.json()["access_token"]
    user = httpx.get("https://api.github.com/user",
        headers={"Authorization": f"Bearer {token}"}).json()
    return {"login": user["login"], "token_preview": token[:8] + "..."}
```

**Stretch:** Refresh token flow, scope upgrade request, PKCE for public clients.
**Architect note:** Always validate `state` (CSRF protection) and use `code_verifier` (PKCE) for SPAs — without these, OAuth is exploitable.

---

## Day 53: Token Refresh Handling (45 min)

```python
# day53_token_refresh.py
import httpx
import time
from dataclasses import dataclass, field

@dataclass
class TokenStore:
    access_token: str = ""
    refresh_token: str = ""
    expires_at: float = 0.0
    client_id: str = ""
    client_secret: str = ""

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at - 30  # 30s buffer

    def get_valid(self) -> str:
        if self.is_expired() and self.refresh_token:
            self._refresh()
        return self.access_token

    def _refresh(self):
        r = httpx.post("https://oauth2.googleapis.com/token", data={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        })
        r.raise_for_status()
        data = r.json()
        self.access_token = data["access_token"]
        self.expires_at = time.time() + data["expires_in"]
        if "refresh_token" in data:
            self.refresh_token = data["refresh_token"]

# Demo
store = TokenStore(
    access_token="old", refresh_token="rt_123",
    expires_at=0, client_id="cid", client_secret="csec",
)
print(store.get_valid())  # returns "old" but is_expired=True internally — refresh happens
```

**Stretch:** Proactive refresh (5 min before expiry), multi-account token store, encrypted at rest.
**Architect note:** Store tokens encrypted at rest (Fernet, AWS KMS). A leaked refresh token = permanent account compromise.

---

## Day 54: Per-User API Credentials (60 min)

```python
# day54_user_credentials.py
from fastapi import FastAPI, Depends, HTTPException, Header
import os
import json
from cryptography.fernet import Fernet

app = FastAPI()
ENCRYPTION_KEY = os.environ["ENCRYPTION_KEY"].encode()  # base64 32-byte
fernet = Fernet(ENCRYPTION_KEY)

# Simulated DB
USERS: dict[str, dict] = {}  # user_id -> {encrypted_creds, name}

def encrypt(plaintext: str) -> str:
    return fernet.encrypt(plaintext.encode()).decode()

def decrypt(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()

def auth(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "bad auth")
    return authorization[7:]

@app.post("/users/{user_id}/credentials")
def store_creds(user_id: str, github_token: str, stripe_key: str,
                _token: str = Depends(auth)):
    USERS[user_id] = {
        "github": encrypt(github_token),
        "stripe": encrypt(stripe_key),
    }
    return {"ok": True}

@app.get("/users/{user_id}/github-token")
def get_github(user_id: str, _token: str = Depends(auth)):
    if user_id not in USERS:
        raise HTTPException(404)
    return {"token": decrypt(USERS[user_id]["github"])[:8] + "..."}
```

**Stretch:** Per-resource scopes, audit log of every decrypt, KMS-backed encryption.
**Architect note:** Per-user credential isolation means a single user's compromised account can't touch another user's data. This is the foundation of multi-tenant SaaS security.

---

## Day 55: Multi-Tenant API Quotas (60 min)

```python
# day55_quotas.py
import time
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class Quota:
    requests_per_minute: int = 60
    requests_per_day: int = 10000
    cost_per_day_cents: int = 100  # $1/day in API spend cap

@dataclass
class TenantUsage:
    minute_count: int = 0
    minute_reset: float = 0.0
    day_count: int = 0
    day_reset: float = 0.0
    day_cost_cents: int = 0

class QuotaEnforcer:
    def __init__(self, default: Quota):
        self.default = default
        self.usage: dict[str, TenantUsage] = defaultdict(TenantUsage)
        self.overrides: dict[str, Quota] = {}

    def check(self, tenant: str, est_cost_cents: int = 0) -> tuple[bool, str]:
        q = self.overrides.get(tenant, self.default)
        u = self.usage[tenant]
        now = time.time()

        # Roll windows
        if now > u.minute_reset:
            u.minute_count = 0
            u.minute_reset = now + 60
        if now > u.day_reset:
            u.day_count = 0
            u.day_cost_cents = 0
            u.day_reset = now + 86400

        if u.minute_count >= q.requests_per_minute:
            return False, f"minute limit {q.requests_per_minute}"
        if u.day_count >= q.requests_per_day:
            return False, f"day limit {q.requests_per_day}"
        if u.day_cost_cents + est_cost_cents > q.cost_per_day_cents:
            return False, f"cost cap ${q.cost_per_day_cents/100}"
        return True, "ok"

    def record(self, tenant: str, cost_cents: int = 0):
        u = self.usage[tenant]
        u.minute_count += 1
        u.day_count += 1
        u.day_cost_cents += cost_cents

q = QuotaEnforcer(Quota())
print(q.check("tenant_a", est_cost_cents=10))  # ('ok', 'ok')
q.record("tenant_a", cost_cents=10)
```

**Stretch:** Tiered plans (free/pro/enterprise), burst capacity with token bucket, per-endpoint quotas.
**Architect note:** The single most expensive day in your SaaS will be a runaway loop. Cost caps save companies from bankruptcy.

---

## Day 56: Audit Log Every API Call (45 min)

```python
# day56_audit_log.py
import json
import time
from dataclasses import dataclass, asdict
from typing import Any
import logging

logging.basicConfig(filename="audit.log", level=logging.INFO)

@dataclass
class AuditEvent:
    tenant: str
    user: str
    method: str
    url: str
    status: int
    duration_ms: float
    request_id: str
    timestamp: float
    extra: dict[str, Any] = None

def audit(method: str, url: str):
    def decorator(fn):
        def wrapper(tenant: str, user: str, *args, **kwargs):
            req_id = f"{time.time_ns()}"
            start = time.time()
            try:
                result = fn(*args, **kwargs)
                status = 200
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = (time.time() - start) * 1000
                event = AuditEvent(
                    tenant=tenant, user=user, method=method, url=url,
                    status=status, duration_ms=duration, request_id=req_id,
                    timestamp=time.time(),
                )
                logging.info(json.dumps(asdict(event)))
        return wrapper
    return decorator

@audit("GET", "/v1/charges")
def list_charges(tenant: str, user: str):
    return [{"id": "ch_1", "amount": 1000}]

list_charges(tenant="t1", user="alice")
print(open("audit.log").read())
```

**Stretch:** Ship to Loki/CloudWatch, searchable in 30s, structured fields.
**Architect note:** Without per-request audit logs, you can't answer "what did user X do yesterday?" — and that's the question you get asked in every incident.

---

## Day 57: Anomaly Detection on API Usage (60 min)

```python
# day57_anomaly.py
import json
import statistics
from collections import defaultdict
from datetime import datetime, timedelta

# Load last 30 days of audit log
USAGE: dict[str, list[tuple[datetime, int]]] = defaultdict(list)
# ... populate from real audit log ...

def detect(tenant: str, lookback_days: int = 30) -> dict:
    series = USAGE.get(tenant, [])[-lookback_days:]
    if len(series) < 7:
        return {"anomaly": False, "reason": "insufficient data"}
    counts = [c for _, c in series]
    mean = statistics.mean(counts)
    stdev = statistics.stdev(counts) or 1
    today = counts[-1]
    z = (today - mean) / stdev
    return {
        "tenant": tenant,
        "today": today,
        "mean": round(mean, 1),
        "z_score": round(z, 2),
        "anomaly": abs(z) > 3,
        "direction": "spike" if z > 0 else "drop",
    }

# Demo
sample = [(datetime(2026, 1, 1) + timedelta(days=i), 100 + (i % 7) * 5) for i in range(30)]
USAGE["tenant_a"] = sample
USAGE["tenant_a"][-1] = (datetime(2026, 1, 30), 1000)  # spike
print(detect("tenant_a"))
```

**Stretch:** Per-tenant model (each tenant has its own baseline), alert via PagerDuty, root-cause hints.
**Architect note:** Per-tenant anomaly detection beats global models because usage patterns differ wildly (a "B2B spike" looks like a "consumer B2C drop").

---

## Day 58: WEEKEND — OAuth Dashboard (3 hours)

Build a multi-user dashboard where each user OAuths into GitHub + Stripe + Linear. Show:
- GitHub: open PRs, review requests, recent activity
- Stripe: MRR, recent charges, failed payments
- Linear: assigned issues, team velocity

Each user sees only their data. Encrypt tokens at rest. Deploy to Fly.io.

**Architect note:** This is "integration hub" SaaS territory — every additional OAuth provider is +20% value to users.

---

## Day 59: Polish + Tests (60 min)

Take any project from Days 31-58 and:
- Add pytest suite (mock httpx, fixture-based)
- Add `pydantic` models for all API responses
- Add structured logging
- Add `tenacity` retry decorator
- Add rate-limit middleware
- Type-check with `mypy --strict`
- 80%+ test coverage

**Architect note:** A project without tests is a prototype, not a product. Tests are how you get promoted to senior.

---

## Day 60: MONTH PROJECT — "Ops Agent" (6 hours)

**Goal:** Build an AI that manages your SaaS stack via natural language.

**Spec:**
- Chat interface (Streamlit)
- LLM agent with function-calling for: Linear, Slack, GitHub, Notion, Stripe
- Persistent conversation memory (SQLite/Postgres)
- Per-user OAuth credentials
- Audit log of every tool call
- Rate limit + cost cap per user

**Example queries:**
- "Show me all open P0 Linear issues"
- "Find the related Slack threads and summarize them"
- "Post a status update to #eng-leads"
- "Open a PR that fixes the top issue"

**Deploy:** Streamlit Cloud or Fly.io. Share publicly. Apply to Y Combinator.

**Architect note:** This is a "real" SaaS MVP. The hard parts are 1) tool-call reliability, 2) auth, 3) cost control — and the LLM is the easy part.

---

## Month 2 Summary

**Built:** 30 projects · 1 multi-API dashboard · 1 OAuth flow · 1 event-driven AI system
**Time:** ~30 hours over 30 days
**Cost:** ~$10 in API fees (more if you deploy the month project)

**Key skills learned:**
- Function calling & tool use
- Async API clients (httpx)
- Resilience patterns (retry, backoff, circuit breaker, cache)
- Webhook receivers + signature verification
- OAuth 2.0 + per-user credentials
- Quotas, audit logs, anomaly detection

**Next:** Month 3 — AI + Documents & Search. 30 more projects on MongoDB, Elasticsearch, OCR, and PDF parsing.
