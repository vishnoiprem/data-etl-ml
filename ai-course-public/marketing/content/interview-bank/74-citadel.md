# 74. Citadel

- **Role:** Quant Researcher / Quant SWE / Global Quantitative Strategies
- **Tech stack:** Python, C++, CUDA, kdb+, PyTorch, distributed systems
- **Comp band:** $300K-$1M+ total comp (Quant → Senior Quant → PM-track) | Base + bonus (top of market; no public equity)
- **Cumulative pass rate:** ~2-3%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + a stylized implied volatility surface (SVI/SSVI fit) over a price grid, with a Citadel-Securities equity order book inset. Color: Citadel blue (#003B7E). Headline: "Citadel / Quant Researcher & SWE / 2026".

> **TL;DR:** Citadel wants winners — math rigor, competitive drive, and production engineering taste, all in one. The signature round is the onsite: 5 rounds in a day, all math, including backprop derivations, options pricing system design, and Fermi estimation traps. The winning candidate can defend a bet they made and show it paid off.

```
Recruiter → Phone (math) → Onsite (4-5 rounds) → Hiring committee → Offer
```

The math → coding → systems → ML progression is the spine. Confuse Citadel with Citadel Securities in the screen and you're already starting in the hole.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, fit | 30 min | ~50% |
| 2. Technical phone | Probability, statistics, coding | 60 min | ~30% |
| 3. Onsite (4-5 rounds) | Math, coding, system design, ML, behavioral | 5-6 hrs | ~30% |
| 4. Hiring committee | Cross-team review | 1-2 wks | ~50% |
| 5. Offer | Comp negotiation | 1 wk | — |

## Stage 1: Recruiter screen

The screen rewards conviction. Know the difference between Citadel and Citadel Securities — confusing them is a soft negative.

### Q1.1: "Why Citadel?"
**Answer:** "Citadel is the most data-driven hedge fund. Citadel Securities is the largest market maker in equities and options. I want to be at the intersection of fundamental research and the cleanest data in the world, and Citadel's GQS team is where that happens."
**Tip:** Show you know the difference between Citadel (multi-strategy hedge fund) and Citadel Securities (market maker). Confusing them is a soft negative.

### Q1.2: "Why quant vs FAANG?"
**Answer:** "I'd rather compete on alpha than on resumes. The scoreboard is honest, and at FAANG I'd never know if my work actually mattered. Citadel's GQS team has the data and infra to do ML at scale, which is the rarest combination in this industry."
**Tip:** Have a real reason. Ken Griffin's culture rewards conviction.

## Stage 2: Technical phone screen

The phone is probability and Fermi estimation — Citadel is famous for ambiguity traps. Slow down and read carefully.

### Q2.1: 100 coins, 10 heads up. You flip all tails-up coins. How many heads up on average?
**Answer:** Of the 90 tails-up, each has 0.5 chance to become heads, so expected new heads = 45. Total = 10 + 45 = 55. But wait, that's the number of heads after one round; the question is about a specific moment, so answer 55.
**Tip:** Watch for misread; Citadel is famous for ambiguity traps.

### Q2.2: Estimate the volume of water in Lake Michigan.
**Answer:** ~4,900 km^3. Show your reasoning: surface area × average depth. They want the estimation process, not the exact number.
**Tip:** Fermi estimation; round-to-powers-of-10.

## Stage 3: Onsite

Five rounds in a day: rejection-sampling probability, hash-map coding, backprop derivation, options-pricing system design, and a behavioral that probes competitive conviction.

### Round 3.1: Probability
**Q:** You have a fair coin. How do you generate a uniform sample from 1 to 6?
**Answer:** Use coin flips to generate 3 bits; if value > 6, reject and retry. Expected 8/3 = 2.67 flips per sample.
**Tip:** They want rejection sampling logic + expected number of flips.

### Round 3.2: Coding
**Q:** Implement a hash map with O(1) operations.
**Answer:** Array of buckets with linked lists or open addressing; resize at load factor > 0.7. Be ready to discuss rehashing.
**Tip:** They want production-quality code.

### Round 3.3: ML deep-dive
**Q:** Derive backprop for a 2-layer net.
**Answer:** Forward: h = σ(W1 x), y = W2 h. Loss L = 0.5 (y - t)^2. ∂L/∂W2 = (y-t) h^T. ∂L/∂W1 = (W2^T (y-t) ⊙ σ'(W1 x)) x^T.
**Tip:** Clean calculus on the board.

### Round 3.4: System design
**Q:** Design a real-time options pricing system.
**Answer:** Receive market data → implied vol surface fit (SSVI/SVI) → Black-Scholes pricing → Greeks (delta, gamma, vega, theta) → publish to traders. Discuss vol surface arbitrage, calibration, latency.

### Round 3.5: Behavioral
**Q:** Tell me about a time you made a bet that paid off.
**Answer:** STAR: conviction + reasoning + outcome.

## Stage 4: Hiring committee
Panel of 4-5 senior quants + 1 PM. They look for: (1) statistical rigor, (2) competitive drive, (3) production engineering taste.

## Stage 5: Offer
$300K-$700K base for new grads, $500K-$1M+ for experienced. Signing $100K-$500K. They pay top of market and counter hard.

## Tips for the Citadel loop

Most candidates over-index on alpha-bragging and under-index on clean derivations. Citadel's culture rewards both — show, don't tell.
- Practice Heard on the Street end-to-end.
- Read Hull for options; memorize Greeks derivations.
- Be ready to derive every ML formula.
- Show you can compete — they prize winners.
- Don't undersell; they screen for confidence (without arrogance).
- Have specific examples of high-stakes decision-making.

## Real candidate report
> "5 rounds in one day, all math. They asked me to derive the Black-Scholes PDE, implement a hash map, and design an options pricing system. Ken's culture is intense — they want people who've competed and won. Offer was $500K base + $400K sign-on for a new grad PhD." — Levels.fyi, Quant Researcher, 2025

## Sources
- [Citadel careers](https://www.citadel.com/careers)
- [Citadel Securities careers](https://www.citadelsecurities.com/careers)
- [Levels.fyi — Citadel](https://www.levels.fyi/companies/citadel)
- [Glassdoor — Citadel](https://www.glassdoor.com/Interview/Citadel-Interview-Questions-E23431.htm)
- [Reddit r/quant — Citadel threads](https://reddit.com/r/quant)

---

## The 1 thing to remember

Citadel's math canon is the gate — Heard on the Street, Hull for options and Greeks, and clean ML derivations (backprop on the board) are not optional, and competitive conviction is the differentiator that pushes offers above band.