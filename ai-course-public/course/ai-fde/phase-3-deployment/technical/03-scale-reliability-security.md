# Lesson T3 — Scale, reliability, and security failure handling

> **The 3-loop cadence from T2 only works if the service stays up.** 45 minutes. Hands-on: trip a circuit breaker, drain a rate limiter, and watch the redactor strip an email from a log line.

By the end of this lesson you can explain the **3 failure modes of LLM services** (silent quality drops, latency spikes, cost spikes), wire a circuit breaker / rate limiter / PII redactor around a `/draft` call, and read the `GET /circuit/state` endpoint to know whether the system is healthy. The artifact that survives: the runbook (C3) + the security policy ("never log a customer email") + the on-call rotation that knows what to do at 2am when OpenAI is down.

The PacificFreight scenario: it's week 5 of the pilot. Mei sends 150 emails/day. At 14:23 on a Tuesday, OpenAI's API goes down for 11 minutes. The drafter hangs. Mei is blocked. Sarah (ops manager) asks "why didn't it just say 'down for maintenance'?" **That's the moment you need a circuit breaker.** And the next week, an intern pastes a 10,000-row customer CSV into the email body by mistake. The LLM gets a wall of PII. **That's the moment you need the redactor.** And on Friday, Mei complains "the drafter is sluggish today" — turns out she has 8 tabs open and is hitting the rate limit. **That's the moment you need a visible rate-limit response.**

---

## 🎯 Outcome

You produce one artifact (the code already exists; the lesson is the **why**):

- `service/circuit.py` — `CircuitBreaker` (closed / half_open / open with 3 trip signals), `TokenBucketRateLimiter` (per-user), `Redactor` (regex for emails / phones / passports), `TTLCache` (LRU+TTL for fallback), and the `make_tiered_fallback` 3-tier (cache → cheaper LLM → stub) wiring.
- `GET /circuit/state` — the endpoint Daniel hits when the drafter feels slow. Returns current state, recent transitions, fallback tier, and the rolling-window call counts.
- `GET /metrics` — Prometheus text exposition; the CS team's Grafana dashboard plots `pf_circuit_state{downstream="openai"}` as a single-stat panel.
- A 5-question "FDE has left" test (in `consulting/06-on-call-rotation.md`) the next FDE can answer in 30 seconds.

When you finish, you can answer in 60 seconds: "what happens when OpenAI is down for 10 minutes?" and "what's the worst-case cost if a user pastes 10,000 rows into the email body?"

## 🧠 Mindset

LLM services have **3 failure modes that don't exist in regular web services**, and each needs a different primitive:

| Failure mode | What it looks like | What catches it | What it does NOT catch |
|---|---|---|---|
| **Silent quality drop** | OpenAI ships a model update. The drafter starts hallucinating. No 5xx. Latency is fine. | The **offline eval** (Phase 2 T2). | Metrics (everything is 200 OK). Rate limiter (rate is normal). |
| **Latency spike** | OpenAI's P99 jumps from 2s to 12s. The drafter feels broken. | The **circuit breaker's `latency_p99_ms` trip signal**. The **online metric** `pf_draft_latency_seconds` histogram. | The offline eval (it can't run during an outage — it's stuck in the same latency tail). |
| **Cost spike** | Mei pastes a 10K-row CSV. Token usage spikes to $5. Or someone runs a tight loop and burns $20 in 10 minutes. | The **circuit breaker's `cost_per_min_usd` trip signal**. The **rate limiter's per-user cap**. The **redactor** (smaller body = fewer tokens). | The offline eval (it sees the result, not the bill). The latency histogram (cost ≠ latency). |

The trap:

1. **The "circuit breaker is safety" trap.** A circuit breaker is **observability**, not safety. It tells you the LLM is degraded; it doesn't *prevent* the degradation. The 3-tier fallback is what keeps the drafter responsive during the outage. **The breaker just routes around the failure.**
2. **The "rate limiter is anti-abuse" trap.** The rate limiter is **cost control**, not anti-abuse. Mei hitting 8 tabs in 30 seconds is not abuse — it's normal usage that the original 1-call-per-3-seconds budget didn't anticipate. The rate limiter's job is to keep total cost under Daniel's $5/month ceiling.
3. **The "redactor is compliance theater" trap.** The redactor is **token-cost control**, not just compliance. Customer emails are 20+ characters each; a 10K-row paste = 200K characters of PII = a $2 prompt. Redacting before the LLM call cuts the token bill AND the privacy risk in one move.

> **FDE rule:** ship a circuit breaker, a rate limiter, AND a redactor. They are not three separate features — they are **one defense** in depth, each catching what the others miss. The cost-and-quality graph for an LLM service is not flat; the failure modes are correlated (a slow LLM is often an expensive one, and an expensive one often hallucinates more).

## 🛠️ Practice — the 3 failure modes

### Failure mode 1: latency spike → circuit breaker trips

The circuit breaker has 3 trip signals, evaluated every call against a rolling 60s window:

```python
@dataclass
class CircuitBreakerConfig:
    failure_threshold: float = 0.20       # trip if failure_rate >= 20% over the window
    latency_p99_ms_threshold: float = 4000.0  # trip if observed p99 latency > 4s
    cost_per_min_usd_threshold: float = 5.0   # trip if rolling 60s cost > $5
    window_seconds: float = 60.0
    cooldown_seconds: float = 30.0
    min_calls_in_window: int = 5          # don't trip on < 5 calls
```

The state machine is the standard 3-state CLOSED → OPEN → HALF_OPEN → CLOSED:

```
   ┌────────┐  threshold breach   ┌──────┐  cooldown elapsed  ┌────────────┐
   │ CLOSED │ ──────────────────▶ │ OPEN │ ─────────────────▶ │ HALF_OPEN  │
   └────────┘                     └──────┘                    └────────────┘
       ▲                             ▲                              │
       │ half_open_success           │ half_open_failure            │ trial call
       └─────────────────────────────┴──────────────────────────────┘
```

**Why the breaker is observability, not safety:** the breaker doesn't *fix* the LLM. It routes the next call to the 3-tier fallback. If the fallback also fails, the call returns the stub ("[unavailable] The drafter is temporarily down"). The breaker's job is to keep the user from waiting 12s for a hung HTTP call.

**The `min_calls_in_window=5` knob is critical.** Without it, the first failed call (1 of 1 = 100% failure rate) trips the breaker. With it, you need 5 calls in the window before the failure rate is even considered. This is the lesson of "don't make decisions on 1 data point."

### Failure mode 2: cost spike → rate limiter caps the damage

The token bucket is per-user:

```python
rl = TokenBucketRateLimiter(capacity=20, refill_rate=0.33)  # 20 burst, 1 token / 3s
if not rl.try_acquire(user_key):
    return {"outcome": "rate_limited", "draft": "[rate limit] Try again in 30s."}
```

**The math:** Mei sends 150 emails/day = ~10/hour = 1 every 6 minutes on average. A capacity of 20 + refill of 1 per 3s = 20 tokens burst, then 20 per minute. She'll never hit the limit. But if she opens 8 tabs and triggers 20 drafts in 30 seconds, she gets capped and the drafter returns `[rate limit]`. **The cost ceiling is preserved; the user experience is "try again in a moment" instead of "Daniel's $5 bill is now $50."**

**The Phase 4 caveat (explicit in the lesson):** the bucket is in-process. With multiple workers (gunicorn with 4 workers), each worker has its own bucket. Mei's effective limit is 4× the configured value. The fix is Redis with a Lua script for atomic token decrement. The lesson calls this out; the code does not implement it.

### Failure mode 3: PII leakage → redactor strips before the LLM call

The redactor runs on the email body BEFORE the LLM call:

```python
class Redactor:
    EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}")
    PHONE_RE = re.compile(r"\+?\d[\d\s\-\(\)]{7,}\d")
    PASSPORT_RE = re.compile(r"\b[A-Z]\d{7}\b")
    def redact(self, text: str) -> str:
        text, n = self.EMAIL_RE.subn("[REDACTED:email]", text); ...
```

**The wire-up** in `_draft_pipeline`:

```python
# In service/app.py::_draft_pipeline:
redacted_body = _REDACTOR.redact(req.email)
n_redactions = _REDACTOR.stats()["emails"] + ...
_USAGE_LOG.log(
    request_id=request_id, ...,
    n_redactions=n_redactions,  # count only, never the redacted text
)
```

**The dual-purpose win:** the redactor cuts the token bill (a 10K-row CSV with 200K chars of emails = a $2 prompt without redaction; with redaction = ~$0.20) AND keeps customer PII out of the OpenAI request. **One regex line, two problems solved.**

**The log line says "n_redactions=12", not "the redacted text is john@…, jane@…".** The next FDE can verify redaction worked by counting, never by reading. **This is the security boundary.**

### The 3-tier fallback (cache → cheaper LLM → stub)

When the breaker trips, calls don't go to the LLM. They go to `make_tiered_fallback`:

```python
def make_tiered_fallback(cache, cheaper_fn):
    def fallback(*args, **kwargs):
        cache_key = str(args[0]) if args else "default"
        cached = cache.get(cache_key)
        if cached is not None:
            return {**cached, "circuit_state": "open", "fallback_tier": "cache"}
        if cheaper_fn is not None:
            try:
                result = cheaper_fn(*args, **kwargs)
                cache.set(cache_key, result)
                return {**result, "circuit_state": "open", "fallback_tier": "cheaper"}
            except Exception:
                pass
        return stub_fallback(*args, **kwargs)  # "[unavailable]"
    return fallback
```

The 3 tiers:

1. **Cache** — if we drafted a similar email in the last 10 min, return the cached response. Mei sends "your shipment is held at customs" ~20 times/day; the cache hits most of them.
2. **Cheaper LLM** — fall back to `gpt-4o-mini` (or the equivalent in whatever provider). 10× cheaper, slightly worse quality, but Mei can still reply.
3. **Stub** — `[unavailable] The drafter is temporarily down. Please reply manually.` Better than a hung HTTP call. Mei sees the message, sends a 2-line manual reply, moves on.

**The cache is the unsung hero.** Of the 150 emails/day Mei sends, ~40 are near-duplicates ("where is my shipment?"). The cache absorbs them when the breaker is open, so the drafter still *feels* responsive during a 10-min outage. Without the cache, every call falls to Tier 2 or 3 and Mei notices the quality drop.

### The `GET /circuit/state` endpoint

Daniel's on-call debugging tool:

```bash
$ curl http://localhost:8000/circuit/state
{
  "name": "openai",
  "state": "open",
  "state_code": 2,
  "n_calls": 142,
  "n_trips": 1,
  "window_n": 7,
  "window_failures": 6,
  "window_cost_usd": 0.0035,
  "recent_transitions": [
    {"ts": 1728000000, "from": "closed", "to": "open", "reason": "threshold_breach"},
    {"ts": 1728000030, "from": "open", "to": "half_open", "reason": "cooldown_elapsed"}
  ]
}
```

Three things Daniel looks for in 10 seconds:

1. **`state`** — is the breaker open? If yes, why (look at `recent_transitions[0].reason`).
2. **`window_failures / window_n`** — what's the failure rate? If it's 6/7 = 86%, the LLM is genuinely down. If it's 1/7 = 14%, it's noise and the breaker tripped on latency or cost.
3. **`window_cost_usd`** — is this a cost spike? If yes, check if someone is running a loop.

### The wrap order in `_draft_pipeline`

The 4 primitives are stacked in this order. The order matters:

```python
# 1. Redact (cheapest; always run)
safe = _REDACTOR.redact(req.email)
# 2. Rate limit (cheap; protects cost)
if not _RATE_LIMITER.try_acquire(user_key):
    return {"outcome": "rate_limited", ...}
# 3. Circuit breaker (routes around outages)
result = _LLM_BREAKER.call(_service_draft_fn, safe, request_id=...)
# 4. Telemetry (emits the metric + the log line)
telemetry_mod.REGISTRY.counter("pf_drafts_total", labels={"outcome": outcome}).inc()
telemetry_mod.REGISTRY.histogram("pf_draft_latency_seconds", ...).observe(latency_ms/1000.0)
_USAGE_LOG.log(...)
```

**Why this order?**

- **Redact first** — every subsequent step sees the smaller, safer body.
- **Rate limit second** — a rate-limited call should not consume an LLM token or a breaker slot. The 429-equivalent returns immediately.
- **Breaker third** — the breaker routes to fallback if needed. If the rate limiter says no, the breaker is bypassed (no point in trying when the user is over budget).
- **Telemetry always runs** — even rate-limited and fallback responses get a log line. The 3-loop cadence needs visibility into *all* outcomes, not just successes.

---

## 🏛️ FDE Lens — when the primitives lie

The 3 primitives are correct in the steady state. They lie at the edges. The FDE needs to know the 3 lies:

### Lie 1: the breaker trips on 1-of-1

Without `min_calls_in_window=5`, the first failed call (1 of 1 = 100% failure rate) trips the breaker. The system then serves the stub for 30 seconds while the LLM recovers from a single blip. **The fix is the `min_calls_in_window` knob. Set it to ≥ 5 in production. The lesson includes the knob for a reason.**

### Lie 2: the rate limiter doesn't share across workers

The token bucket is in-process. With gunicorn -w 4, Mei's effective limit is 4× the configured value. **For a single-worker VM (Daniel's current setup), this is correct.** For multi-worker, swap to Redis. The lesson explicitly notes this; the code does not implement it.

### Lie 3: the redactor misses novel PII formats

The redactor catches `email`, `phone` (international format), and `passport` (Singapore/Malaysia style). It does NOT catch:

- Credit card numbers (16 digits in 4 groups)
- Singapore NRIC (S1234567A format)
- US Social Security Numbers (123-45-6789)
- Addresses (unless they contain a number + postcode)

**The fix is to extend the regexes as the customer adds requirements.** The lesson includes the 3 most common; the FDE adds the rest based on the customer's regulatory environment. A real deployment would use Microsoft Presidio or a similar PII detection library; this lesson uses regex to keep the code self-contained.

> **FDE rule:** the 3 primitives are a **floor**, not a ceiling. The real deployment adds a battle-tested breaker library (`pybreaker`), a Redis-backed rate limiter, and a PII detection library (Presidio). This lesson is the **why and the math**; the swap-in is one `pip install` away.

## 🌙 Reflect

Write 3-5 sentences:

1. The circuit breaker has 3 trip signals. Mei asks "why not just 1 — failure rate?" What do you say? (Hint: think about the 10-min OpenAI outage that returns 200 OK with degraded responses.)
2. The rate limiter is per-user, in-process, with capacity=20 + refill 1/3s. Mei has 8 tabs open and hits the limit. **What's the worst case for Mei's daily cost if the rate limiter is removed entirely?**
3. The redactor catches email/phone/passport. A customer pastes their NRIC (S1234567A). The redactor doesn't catch it. **What's the blast radius? (How many calls before someone notices?)**
4. The `GET /circuit/state` endpoint returns `window_failures=6, window_n=7`. The breaker is OPEN. Mei is staring at "[unavailable]". **Walk through the next 30 seconds: what does Mei do, what does the breaker do, what does Daniel see?**
5. The wrap order is redact → rate-limit → breaker → telemetry. You consider swapping the order to breaker → rate-limit → redact. **What breaks?** (Hint: a tripped breaker shouldn't redact — it should return the stub fast.)

**What's next — Phase 4 / handoff.** The 3-loop cadence (T2) and the 3 failure-mode primitives (T3) are what Mei + Daniel + the next FDE need to keep the drafter improving without you in the room. The consulting track (C1 + C2 + C3) wraps that into a stakeholder map, a weekly iteration cadence, and the runbook + RACI + on-call rotation that turn "the FDE built it" into "the team runs it."
