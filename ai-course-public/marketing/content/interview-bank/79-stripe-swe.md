# 79. Stripe (Payments SWE)

- **Role:** Senior Software Engineer (Payments / Infrastructure)
- **Tech stack:** Ruby, Scala, Go, Java, Python, PostgreSQL, Redis, Kafka, distributed systems
- **Comp band:** $200K-$700K base + RSUs (public company, SF/South SF)
- **Cumulative pass rate:** ~2-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, fit | 30 min | ~50% |
| 2. Technical phone | Coding + system design lite | 60 min | ~40% |
| 3. Onsite (4-5 rounds) | Coding (2), system design, behavioral, hiring manager | 4-5 hrs | ~30% |
| 4. Hiring committee | Panel review | 1-2 wks | ~60% |
| 5. Offer | Comp negotiation | 1 wk | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Stripe?"
**Answer:** "Stripe moves hundreds of billions of dollars a year, and the scale + reliability bar is the most interesting engineering problem in payments. I want to work on the primitive that the internet's commerce runs on."
**Tip:** Show you've used Stripe (as a developer ideally). Mention specific products (Radar, Connect, Issuing) by name.

### Q1.2: "Why payments?"
**Answer:** "I like the strict correctness bar — a bug doesn't just slow users down, it loses money. The combination of correctness + scale + financial domain is the sweet spot for me."
**Tip:** Have a specific reason.

## Stage 2: Technical phone screen

### Q2.1: Implement an LRU cache.
**Answer:** See Writer's answer — OrderedDict O(1).
**Tip:** Standard; they want clean code + edge cases.

### Q2.2: Design a URL shortener.
**Answer:** Hash → base62; or counter + base62. Discuss collision handling, caching, rate limiting, read/write split.
**Tip:** They expect scaling discussion (1B URLs, 10K QPS).

## Stage 3: Onsite

### Round 3.1: Coding
**Q:** Implement a payment processing function with idempotency.
**Answer:** Use an idempotency key in a unique-keyed DB table; on retry, return the cached response. Discuss at-most-once delivery, partial failures, distributed transactions.
**Tip:** This is core to Stripe.

### Round 3.2: Coding
**Q:** Serialize/deserialize a binary tree.
**Answer:** Pre-order traversal, mark nulls; reconstruct recursively. Discuss iterative variant.
**Tip:** Standard; they want clean code.

### Round 3.3: System design
**Q:** Design Stripe's payment processing pipeline.
**Answer:** API gateway → fraud check (Radar ML) → bank network adapter (Visa/MC rails) → ledger write → webhook delivery. Discuss idempotency, exactly-once semantics, 2PC vs Saga, reconciliation, dispute flow.

### Round 3.4: System design (infra)
**Q:** Design a webhook delivery system.
**Answer:** Persistent queue with retry/backoff, signed payloads, exponential backoff with jitter, dead-letter queue, ordering guarantees, replay endpoint.
**Tip:** Stripe's webhooks are a real product.

### Round 3.5: Behavioral
**Q:** Tell me about a time you had to balance correctness with shipping speed.
**Answer:** STAR with metrics.

## Stage 4: Hiring committee
Panel of 4 staff+ engineers + a hiring manager. They look for: (1) strong coding, (2) systems thinking, (3) taste for correctness, (4) Stripe values (rigor, customer focus).

## Stage 5: Offer
Public company RSUs vest over 4 years (25% year 1, then quarterly). Base is top-of-market. They negotiate aggressively for senior+.

## Tips for the Stripe loop
- Read the Stripe blog (especially the engineering posts on payments).
- Practice payment correctness patterns (idempotency, 2PC, eventual consistency).
- Be ready to discuss real-world payment edge cases.
- Show you've built something on the Stripe API.
- Memorize classic system design (URL shortener, rate limiter, web crawler).
- They value "rigor" — be precise in your answers.

## Real candidate report
> "5 rounds in one day, all technical. Coding was 2 mediums, system design was the payment pipeline (idempotency keys, webhooks, ledger). Behavioral was values-based. Offer $400K base + $500K RSUs for senior. Stripe is the best payments engineering interview I've done." — Levels.fyi, Senior SWE, 2025

## Sources
- [Stripe careers](https://stripe.com/jobs)
- [Stripe engineering blog](https://stripe.com/blog/engineering)
- [Levels.fyi — Stripe](https://www.levels.fyi/companies/stripe)
- [Glassdoor — Stripe interviews](https://www.glassdoor.com/Interview/Stripe-Interview-Questions-E671932.htm)
- [Reddit r/cscareerquestions — Stripe thread](https://reddit.com/r/cscareerquestions)