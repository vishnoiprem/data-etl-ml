# 81. Airbnb (Marketplace SWE)

- **Role:** Senior Software Engineer (Marketplace)
- **Tech stack:** Java, Kotlin, Ruby, TypeScript, React, MySQL, Kafka, Spark, Airflow, Kubernetes, TensorFlow
- **Comp band:** $200K-$650K total comp (L4-L6); IC6 staff $700K-$1.2M total comp (Levels.fyi 2026) | RSUs 4-year, 1-year cliff
- **Cumulative pass rate:** ~1.5-2.5%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual (a marketplace search ranking layer — listings, hosts, and a two-tower embedder). Color: Airbnb Rausch (#FF5A5F). Headline: "Airbnb / AI Senior SWE / 2026".

> **TL;DR:** Airbnb's loop is values-heavy and marketplace-specific — the system design round almost always touches two-sided dynamics, and the behavioral round pulls from the original culture deck. The winning candidate frames every answer around host vs guest, talks cold-start fluently, and ships clean, readable code over clever LeetCode.

```
┌──────────────────────────────────────────────────────────────────┐
│                       AIRBNB HIRING FUNNEL                       │
├──────────────────────────────────────────────────────────────────┤
│  Apply ──► Recruiter (50%) ──► Phone Screen (35%) ──► Onsite     │
│                                                                  │
│  Onsite ──► Coding ×2 / Design / Values ──► Calibration Committee │
│          (30%)                                  (60%, level vote) │
│                                                                  │
│  Committee ──► Offer (1 band per level) ──► Team match (90 days) │
└──────────────────────────────────────────────────────────────────┘
```

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, comp, location | 30 min | ~50% advance |
| 2. **Technical phone screen** | 1 coding round, 1 system design chat | 1-2 weeks | ~35% advance |
| 3. **Onsite (4 rounds)** | 2 coding, 1 system design, 1 behavioral | 1 day | ~30% advance |
| 4. **Hiring committee** | Cross-functional panel + cross-location reviewers | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp, level, team match | 1 week | — |

Airbnb's loop is unique: it uses a "values-based" behavioral round grounded in their 12-year-old culture deck, and the coding bar is more about clarity and customer obsession than LeetCode trickery. Expect marketplace-specific design (search ranking, pricing, two-sided dynamics).

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your most impactful marketplace project"
**Answer:** "I built a host-side dynamic pricing model at [Company] using a two-tower neural net trained on 18 months of booking data. We increased host revenue 7% and surfaced 'smart pricing' suggestions in 200ms. The interesting tradeoff was between model accuracy and explainability — hosts rejected black-box suggestions, so we added SHAP-based reasoning that drove 22% suggestion acceptance."
**Tip:** Airbnb is obsessed with "belong anywhere" — frame your work in terms of trust between two parties.

### Q1.2: "Why Airbnb over a pure-tech company like Stripe?"
**Answer:** "I want to work on a two-sided marketplace where ML directly mediates supply and demand. Stripe optimizes payments; Airbnb optimizes whether a family in Kyoto gets discovered by a traveler in Berlin. That's a more interesting ML problem. The 2026 AI Trip ideas launch tells me leadership is serious about ML product, not just ads."
**Tip:** Show you've used the AI trip planner and read Airbnb's 2026 launches.

### Q1.3: "What's your location / remote preference?"
**Answer:** Be direct. SF, NYC, and remote-considered states (CA, NY, WA, TX, MA) are safest. Airbnb moved to "Live and Work Anywhere" with quarterly travel stipends.

Recruiter screens are the easiest filter to pass — they're checking comp fit, location, and your motivation. If you clear this, the real test begins: the phone screen is where Airbnb confirms you can write production code and reason about a marketplace at scale.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Find the k-th smallest element in a BST"
**Answer:**
```python
def kth_smallest(root, k):
    stack = []
    cur = root
    while cur or stack:
        while cur:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        k -= 1
        if k == 0:
            return cur.val
        cur = cur.right
```
**Tip:** Airbnb's phone screen is moderate LeetCode (E-M). Don't optimize prematurely — they want readable code.

### Q2.2: ML — "How would you detect a bad listing before it goes live?"
**Answer:** "Two-stage: (1) Lightweight model on listing metadata + text embeddings (CLIP image, sentence-transformer description) to score risk in <100ms. (2) For high-risk listings, send to human review queue with the model's top suspicious signals (price outlier vs neighborhood, image stock-photo detector, host history features). Train on labeled data from past takedowns; use precision at top-k since reviewer capacity is the constraint."
**Tip:** Mention reviewer capacity / cost-per-flag. Airbnb is cost-conscious.

### Q2.3: System design chat — "Design a notification system for hosts"
**Answer:** "Kafka topic per event type (booking, inquiry, review), a fan-out service writes to a per-user feed (Cassandra), and a delivery orchestrator picks channel (push, email, SMS) based on user prefs and quiet hours. Batching: collapse multiple bookings in a 5-min window into a digest. A/B test ranking of notifications by a small gradient-boosted model trained on downstream host engagement."
**Tip:** They love event-driven architectures and ML ranking layered on top.

## Stage 3: Onsite (4 rounds, 1 day)

### Round 3.1: Coding
**Q3.1.1:** "Implement a thread-safe LRU cache." Standard pattern, use `OrderedDict` or doubly-linked list + hashmap.
**Q3.1.2:** "Given a stream of search queries, return top-k at any time." Use a min-heap of size k or count-min sketch + heap.
**Q3.1.3:** "Serialize/deserialize a binary tree." Airbnb's classic phone-screen question (sourced from their public blog 2018, still asked).

### Round 3.2: System design
**Q3.2.1:** "Design Airbnb's search ranking pipeline." Discuss query understanding, listing retrieval (Elasticsearch + embedding ANN), two-tower ranker, business rules, online learning from bookings.
**Q3.2.2:** "Design a marketplace for experiences." Cover two-sided onboarding, supply quality, demand generation, payments splits, fraud, and review systems.

### Round 3.3: ML deep-dive
**Q3.3.1:** "Walk me through a recsys you've built end-to-end." Data pipeline → features → model → serving → eval. Be ready to discuss offline metrics (NDCG, MAP) and online (bookings per search, host revenue).
**Q3.3.2:** "How do you handle cold start for new listings?" Hybrid content-collaborative, meta-learning, exploration bands, host-driven seeding via boosted listings.

### Round 3.4: Behavioral
**Q3.4.1:** "Tell me about a time you disagreed with your manager." STAR — show you advocated with data, accepted the decision, executed well.
**Q3.4.2:** "Describe a project where you had to ship under uncertainty." STAR — show iteration, customer feedback loops.
**Q3.4.3:** "How do you embody 'belong anywhere' in your work?" Specific story connecting technical work to human impact.

The onsite is the day of truth. Four rounds, two codings, one design, one values — and the design round almost always pulls from search ranking, pricing, or two-sided onboarding. Treat each round as its own interview: the committee will see your packet as a whole and re-weight rounds that wobble.

## Stage 4: Hiring committee
Airbnb's committee (the "Calibration Committee") is a 4-6 person cross-functional panel that reviews your packet, including all interviewer scores, a "value fit" assessment, and 1-2 cross-location peer reviewers. They vote on level (L4/L5/L6) independently of the hiring manager. The bar is high for L6 (staff) — they expect system design that influences org-wide direction.

## Stage 5: Offer
Airbnb has a single comp band per level; negotiation is limited. RSUs vest over 4 years (1-year cliff, then quarterly). Team match happens after offer — you can swap teams within your first 90 days if the first one doesn't fit. Sign-on bonus is rare but relocation is generous.

## Tips for the Airbnb loop
1. **Read "Don't F*ck Up the Culture" and the original culture deck** — values questions are real.
2. **Know marketplace dynamics cold** — two-sided network effects, cold start, supply/demand balance.
3. **Talk about host and guest experience separately** — they're two different customers.
4. **Coding is clean-code focused** — not LeetCode-hard. Variable names matter.
5. **Mention a time you improved a metric by 5%+** — Airbnb is metric-obsessed.
6. **Be candid about AI** — they've shipped multiple LLM features, show you've used them.
7. **Prepare a 90-second "trip you took as a guest" story** — interviewers love it.

## Real candidate report
> "Onsite had 4 rounds in one day. The system design round was on search ranking and they kept pushing me on offline-to-online metric alignment — I had to be precise about NDCG vs bookings/session. The behavioral round was the hardest, three 30-min STAR questions on conflict, ambiguity, and a time I was wrong. They gave me an L5 offer at $420K base + $600K RSU over 4 years. Negotiation room was tiny." — Glassdoor, L5 SWE offer 2025

## Sources
- [Airbnb Engineering Blog](https://airbnb.io/)
- [Airbnb Culture Deck (2014, still referenced)](https://drive.google.com/file/d/0B7s_JyB3CLfuTmhPdmctV1FnNG8/view)
- [Levels.fyi Airbnb](https://www.levels.fyi/companies/airbnb)
- [Glassdoor Airbnb interviews](https://www.glassdoor.com/Interview/Airbnb-Interview-Questions-E391850.htm)
- [LeetCode Airbnb tagged questions](https://leetcode.com/company/airbnb/)

---

## The 1 thing to remember

Airbnb's hiring rewards the candidate who frames every answer around two-sided trust — host and guest are different customers, and the L6 bar goes to engineers who design for the system, not just the model.
