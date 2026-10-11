# 32. Lyft (ML / Pricing / AV)

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual. Color: company brand color as accent. Headline on image: "LYFT / AI PRICING / 2026".

> **TL;DR:** Lyft's loop is **driver-first** by mission — the signature lens is the ethics of pricing, and the prime-time PR crisis is a real cultural scar. The signature stack is **H3 + Flyte + switchback experiments**, and the winning candidate talks about supply-side empathy before reaching for the model.

```
Recruiter (55%) → Phone (45%) → Onsite (35%) → Tech Panel (60%) → Offer
```

- **Role:** ML Engineer / Applied Scientist (Pricing, Marketplace, AV/Level 5)
- **Tech stack:** Python, PyTorch, TensorFlow, Scala, Spark, Kafka, Flyte (Lyft's orchestrator), H3 geospatial
- **Comp band:** $250K-$650K total comp (L4-L6) | RSUs 4-year, 1-year cliff; senior crosses $850K+
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Org match (Pricing/Marketplace/AV), comp | 1 week | ~55% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML | 1-2 weeks | ~45% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML, behavior | 1-2 days | ~35% advance |
| 4. **Hiring committee (Tech Panel)** | Cross-org panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

Lyft's loop is the most mission-driven of the marketplace companies. Ethics and driver empathy aren't bonus points — they're a primary signal. If your pricing design doesn't reach for fairness caps, you've already lost the round.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Lyft for ML?"
**Answer:** "Lyft's marketplace is the cleanest two-sided system in ride-sharing — drivers and riders with rich telemetry. The ML team owns pricing, ETA, dispatch, and the AV stack at Level 5. I want to ship ML that affects millions of weekly rides, with a smaller team and more ownership than I'd get at Uber."
**Tip:** Reference *Lyft Pricing*, *ETA*, *Level 5 (AV)* — these are distinct teams.

### Q1.2: "Tell me about a pricing or marketplace model you shipped"
**Answer:** STAR with focus on *causal impact*, *supply-side response*, and *experimentation*. Lyft is experiments-driven.
**Tip:** Show you understand that pricing changes affect supply and demand in feedback loops.

## Stage 2: Technical phone screens (90 min)

The phone screens look standard, but the ML round always pivots to *supply-side impact* and *ethical constraints*. If you reach for switchback experiments unprompted, you've already cleared the Lyft bar.

### Q2.1: Coding: "Design a URL shortener"
**Answer:** Hash (MD5/SHA) → base62 → 7-char code; store in DB with index; optional caching layer.
**Tip:** System-design-in-coding-format questions. Sometimes a classic LeetCode medium.

### Q2.2: ML: "Design Lyft's prime-time pricing algorithm"
**Answer:** (1) Inputs — supply (drivers online by H3 cell, geo-fenced), demand (riders requesting), ETA, driver acceptance prob; (2) Objective — match rate + driver earnings; (3) Constraints — fairness, regulatory caps, ethical ride affordability; (4) Model — gradient boosting with controlled experiments; (5) Two-sided — must keep rider conversion and driver acceptance both healthy; (6) Switchback experiments to measure causal impact; (7) Online at 30ms.
**Tip:** Lyft's prime-time PR crisis is well-known — they want to know you think about *ethics* of pricing.

## Stage 3: Onsite (4 rounds)

The onsite is dense and ethics-flavored. Every pricing question is a chance to show driver empathy, and the experimentation-platform system design is Lyft's signature.

### Round 3.1: Coding (60 min, 2 questions)
- Q: Search in rotated sorted array. O(log N) modified binary search.
- Q: Word break. DP, O(N·L).
- Optional 3rd: Distributed systems question on idempotency or exactly-once.

### Round 3.2: System design (60 min)
- Q: Design Lyft's ETA model. Streaming features, geospatial indexing (H3), gradient boosting with map-matching, sub-1s inference, and A/B with offline metrics.
- Q: Design Lyft's experimentation platform. Bucket assignment (deterministic hashing), switchback design, interleaving, variance reduction (CUPED), and a dashboard.

### Round 3.3: ML deep-dive (60 min)
- Q: How would you improve Lyft's driver-rider matching? Bipartite matching under constraints, RL for long-term marketplace health, and driver-acceptance prediction.
- Q: How would you build an AV perception model for Level 5? Multi-camera 3D detection, transformer-based BEV, and eval on the Lyft perception dataset.

### Round 3.4: Behavioral (60 min)
- Q: Tell me about a time you navigated a sensitive product decision. Lyft's "ethics of pricing" is a real topic.
- Q: A time you shipped a model that made a hard trade-off.
- Q: Disagreement with a stakeholder.

## Stage 4: Hiring committee
A panel of senior engineers reviews. They look for: (1) ML bar for the level, (2) marketplace / two-sided thinking, (3) ethics and customer empathy (Lyft's "driver-first" mission), (4) Lyft values (Make it Happen, Be Yourself, Uplift Others, Customer Obsession). Vote is "Strong Hire / Hire / No Hire / Strong No Hire."

## Stage 5: Offer
Cash + RSUs. Lyft is competitive but below FAANG top-of-band (post-IPO reset). Negotiation is moderate. Team match after loop. SF HQ is the main hub.

## Tips for the Lyft loop
- Reference *Lyft Pricing*, *ETA*, *Level 5 (AV)*, *Flyte (orchestrator)* — open source tools.
- For ML rounds, emphasize *two-sided dynamics* and *ethical pricing*.
- For system design, geospatial indexing (H3) and real-time streaming are common.
- Lyft is *driver-first* — show you care about supply side too.
- Switchback experiments are Lyft's gold standard — be ready.
- For behavioral, ethics stories score well — Lyft's culture is mission-driven.
- Reference Lyft's published ML papers if you've read them.

## Real candidate report
> "Loop for Lyft Pricing. 4 rounds in 1 day. The system design was the experimentation platform with switchback designs and they pushed on variance reduction. The ML deep-dive was prime-time pricing and I had to discuss fairness constraints and ethical caps. Behavioral was 'uplift others' flavored. Offer at L5, ~$520K total, 5 weeks." — Blind, 2025-10

## Sources
- [Lyft Careers](https://www.lyft.com/careers)
- [Levels.fyi Lyft salaries](https://www.levels.fyi/companies/lyft/salaries)
- [Lyft Engineering blog](https://eng.lyft.com/)
- [Lyft ML papers](https://www.lyft.com/level5/publications)
- [Flyte GitHub](https://github.com/lyft/flyte)

---

## The 1 thing to remember

At Lyft, "driver-first" is a primary signal — name Flyte, name H3, and reach for fairness caps and switchback experiments before you reach for the model, because ethics of pricing is the cultural scar and the test.
