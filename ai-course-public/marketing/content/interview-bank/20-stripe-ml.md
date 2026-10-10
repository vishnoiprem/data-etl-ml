# 20. Stripe (ML Platform)

- **Role:** ML Engineer (Radar / Fraud)
- **Tech stack:** Python, Ruby, Scala, Spark, Kafka, ML infrastructure
- **Comp band:** $200K-$1.2M+ (L1-L5, flat titles)
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **HackerRank OA (60 min)** | Sequential 3-part question, implementation-heavy | 1 week | ~50% advance |
| 2. **Recruiter screen (30 min)** | Background, team fit (Radar / ML Platform) | 1 week | ~50% advance |
| 3. **Technical screen (60 min)** | Live coding, practical scenario | 1-2 weeks | ~40% advance |
| 4. **Virtual onsite (5 rounds in 1-2 days)** | Coding → Bug Squash → Integration → System Design → Behavioral | 1-2 days | ~30% advance |
| 5. **Hiring committee + offer** | Packet → committee vote | 1-2 weeks | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an ML engineer with 5 years in fraud detection — most recently at [X] where I shipped a real-time fraud model that processed 10K payments/sec with <100ms latency. Relevant: a feature store for payment events that handled 1B features/day. I'm targeting Stripe Radar because the payments-fraud domain is the most consequential ML problem in 2026.
**Tip:** Stripe grades domain depth; bring payments or fraud specifics.

### Q1.2: "Why Stripe?"
**Answer:** I want to work on Radar because the platform-enabling thesis is the most important bet in fintech 2026. The 1 thing I'd test: whether Radar can scale to 100M payments/day with <50ms p99 latency while keeping the false-positive rate below 0.1%. The 1 thing I disagree with: Radar should adopt a transformer-based architecture instead of gradient-boosted trees.
**Tip:** Specific product + specific bet + specific test + specific disagreement.

## Stage 2: Technical screen (60 min)

### Q2.1: "Implement a state machine for a payment flow with retries"
**Answer:**
```python
class PaymentStateMachine:
    CREATED, AUTHORIZED, CAPTURED, FAILED, REFUNDED = "created","authorized","captured","failed","refunded"
    TRANSITIONS = {
        CREATED: {AUTHORIZED, FAILED},
        AUTHORIZED: {CAPTURED, FAILED, REFUNDED},
        CAPTURED: {REFUNDED},
        FAILED: set(),
        REFUNDED: set(),
    }
    def transition(self, current, target):
        if target not in self.TRANSITIONS[current]:
            raise InvalidTransition(current, target)
        return target
```
Stripe graders want idempotency baked in: each transition writes a `transition_id` (UUID) that's checked before applying.
**Tip:** Idempotency keys are non-negotiable in payments.

## Stage 3: Virtual onsite (5 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "LRU cache with TTL, thread-safe"
**Answer:** `OrderedDict` for LRU + expiry timestamp; on `get`, check TTL, evict if expired. Thread-safety: `threading.Lock` per cache; sharded locks for concurrency. Stripe caches everything; TTL is the freshness SLA.

### Q3.1.2: "Rate limiter: token bucket, distributed"
**Answer:**
```python
class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate, self.capacity, self.tokens, self.ts = rate, capacity, capacity, time.monotonic()
        self.lock = Lock()
    def allow(self, n=1):
        with self.lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.ts) * self.rate)
            self.ts = now
            if self.tokens >= n:
                self.tokens -= n
                return True
            return False
```
Distributed: Redis-backed with Lua script for atomicity; sliding window via sorted set.

### Round 3.2: Bug Squash (45-60 min, the signature round)

### Q3.2.1: "Find and fix the bug in this unfamiliar codebase"
**Answer:** Follow the trace. Run the failing test, read the stack trace to the named function, read the function + 2 callers. The wrong answer: try to understand the whole codebase. The right answer: "I see the function uses a default timeout of 0, but 0 means 'no timeout' in this library, so the request hangs. Fix: change the default to 3000ms." Verify by re-running the test.
**Tip:** Follow the trace, hypothesize, verify. Process matters more than the answer.

### Round 3.3: Integration (45-60 min, open-book)

### Q3.3.1: "Add a new endpoint to this Stripe-style service"
**Answer:** Match the codebase's patterns: error handling (every error has a code, message, type, HTTP status), logging (structured JSON with a request_id), idempotency (`Idempotency-Key` header required for all POSTs), tests (pytest with the existing fixtures), docstring (the existing style).
**Tip:** Match the patterns, not the function. The grader is grading idiomatic Stripe code.

### Round 3.4: System design (payments-themed, 60 min)

### Q3.4.1: "Design Stripe's payment processing pipeline"
**Answer:** Client → API gateway (auth, idempotency check) → Payment Service (state machine) → Fraud Check (Radar, <100ms) → Bank integration (Stripe-managed adapters for Visa/MC/ACH) → Ledger (double-entry, append-only) → Webhook delivery (durable queue, exponential backoff, dead-letter). Idempotency keys: 24h TTL, corner case (same key, different body) returns 422.
**Tip:** Idempotency + webhooks + ledger is the payments-domain trio.

### Q3.4.2: "Design Radar: real-time fraud detection at 10K payments/sec"
**Answer:** Feature store (online, <5ms lookup), model server (gradient-boosted trees, <20ms inference), fallback rule engine (deny-list, velocity checks). Online learning: shadow mode for 24h before promotion. Eval: precision-recall on a labeled holdout, A/B on 1% of traffic.
**Tip:** Real-time + payments means latency budget is sacred.

### Round 3.5: Behavioral (45 min, Stripe values)

### Q3.5.1: "Tell me about a time you debugged a production incident"
**Answer:** A 1% drop in Radar approvals. Root cause: a feature pipeline silently failed, using stale features for 4 hours. Fix: feature pipeline monitoring + on-call runbook. Lesson: silent failures need proactive testing.
**Tip:** Root cause + fix + lesson.

### Q3.5.2: "Stripe values 'optimistic thoroughness' — a time you went deep on a problem"
**Answer:** I noticed a 0.3% increase in false positives during a holiday spike. I dug into the feature distributions and found a data drift in the device fingerprint feature. Fix: added drift detection to the feature pipeline. Saved an estimated $2M/year in false-positive chargebacks.

## Stage 4: Hiring committee

The committee weighs Bug Squash + payments domain depth + Stripe values. They look for: (1) idiomatic Stripe code (error handling, logging, idempotency), (2) payments-domain fluency (idempotency, webhooks, ledger), (3) "would I trust this person with the Radar codebase?" 1-2 week turnaround is normal.

## Stage 5: Offer

Stripe uses flat titles: L1-L3 are SWE, L4+ is Staff. The L4+ bar is Senior Staff elsewhere. Comp negotiates: base + RSU + sign-on. The play: anchor with a competing offer (Square, Adyen, Plaid). 4-year vest, 1-year cliff.

## Tips for the Stripe ML loop

- **Bug Squash is the signature round.** Follow the trace, hypothesize, verify.
- **Idempotency is non-negotiable.** 24h TTL, corner case for key reuse.
- **Webhooks are at-least-once.** Exponential backoff + jitter, dead-letter, per-account ordering.
- **Integration round is open-book.** Match the patterns, not the function.
- **Payments domain depth.** Idempotency, webhooks, ledger, rate limiting.
- **Flat titles.** L4+ is Staff, not Senior.
- **Pace is breakneck.** Intense information density, no downtime.

## Real candidate report

> *"The entire process moves at a breakneck pace with intense information density, leaving zero room for downtime. As a company that 'only cares about doing the right thing,' Stripe holds a high bar on the 'gaps' — the trade-offs you consider but don't take. The interviewer wants to see you articulate the trade-offs even when you don't have time to implement them."*
> — [Medium — Stripe 2026 New Grad Round 1 VO: In-Depth Interview Guide](https://medium.com/@programhelp/stripe-2026-new-grad-round-1-vo-in-depth-interview-guide-0618ba9be92c)

## Sources

- [InterviewCoder — Stripe Software Engineer Interview: Process & Prep (2026)](https://www.interviewcoder.co/blog/stripe-software-engineer-interview)
- [Dataford — Stripe Software Engineer Interview Questions & Guide 2026](https://dataford.io/interview-guides/stripe/software-engineer)
- [Medium — Stripe 2026 New Grad Round 1 VO: In-Depth Interview Guide](https://medium.com/@programhelp/stripe-2026-new-grad-round-1-vo-in-depth-interview-guide-0618ba9be92c)
- [Datavidhya — Stripe Data Engineer Interview Questions & Process (2026)](https://datavidhya.com/blog/stripe-data-engineering-interview-guide/)
- [Levels.fyi — Stripe compensation](https://www.levels.fyi/companies/stripe/salaries/software-engineer)
- [Stripe Engineering Blog](https://stripe.com/blog/engineering)