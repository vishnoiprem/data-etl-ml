# 77. Optiver

- **Role:** Quantitative Trader / Quantitative Researcher / Quant SWE
- **Tech stack:** C++ (primary), Python, kdb+, low-latency systems, options pricing
- **Comp band:** $250K-$800K total comp (Quant → Senior Quant → Trader-track) | Base + bonus (top of market; no public equity)
- **Cumulative pass rate:** ~3-4%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + an options vol surface (SVI fit) with delta-1 hedge arrows on the underlying. Color: Optiver blue (#003366). Headline: "Optiver / Quantitative Trader & Researcher / 2026".

> **TL;DR:** Optiver is the most disciplined options market maker in the world — vol surface, Greeks, and delta-1 hedging are the daily craft. The signature round is the onsite: Black-Scholes derivations, implied vol via Newton-Raphson, and a delta-1 system design. The winning candidate can talk about vol surface arbitrage and show they read Hull cover to cover.

```
Recruiter → Phone (math) → Onsite (4-5 rounds) → Hiring committee → Offer
```

The math → C++ → options-progression is the spine. Skip Hull and you don't pass the screen; skip the team-oriented vibe and you don't get the offer.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, fit | 30 min | ~50% |
| 2. Technical phone | Probability, statistics, coding | 60 min | ~35% |
| 3. Onsite (4-5 rounds) | Math, coding, system design, trading, behavioral | 5-6 hrs | ~30% |
| 4. Hiring committee | Cross-team review | 1-2 wks | ~60% |
| 5. Offer | Comp negotiation | 1 wk | — |

## Stage 1: Recruiter screen

The screen rewards options depth. Reference the Optiver Trading Academy and the delta-1 blog series.

### Q1.1: "Why Optiver?"
**Answer:** "Optiver is the most disciplined options market maker I know of. The combo of quant research and engineering rigor in options is unmatched, and I want to learn the vol and delta-1 business from people who've been doing it for a decade."
**Tip:** Reference Optiver's published research (their delta-1 blog series is a good start).

### Q1.2: "Why options over equities?"
**Answer:** "Options are the cleanest expression of market opinion — implied vol, skew, term structure are all rich signal sources. I prefer markets where the math is deep and the alpha is durable."
**Tip:** Show you've thought about what makes options trading unique.

## Stage 2: Technical phone screen

The phone tests Black-Scholes fluency and asks for an implied-vol Newton-Raphson implementation. Walk through d1, d2, and vega.

### Q2.1: A stock is at $100, vol 30%, r = 4%. Value a 6-month ATM straddle.
**Answer:** Black-Scholes: C = S·N(d1) − K·e^(−rT)·N(d2). With T=0.5, σ=0.3: d1 ≈ 0.2003, d2 ≈ −0.0118; C ≈ P ≈ 9.39, straddle ≈ 18.78.
**Tip:** They test Black-Scholes fluency hard. Walk through d1, d2, then the call and put.

### Q2.2: Implement a function to compute the implied vol from a market price (Newton-Raphson).
**Answer:**
```python
def implied_vol(price, S, K, T, r):
    sigma = 0.3
    for _ in range(100):
        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)
        c = S*norm.cdf(d1) - K*math.exp(-r*T)*norm.cdf(d2)
        vega = S*norm.pdf(d1)*math.sqrt(T)
        if vega == 0: break
        sigma -= (c - price) / vega
    return sigma
```
**Tip:** Newton-Raphson; they want closed-form vega.

## Stage 3: Onsite

Five rounds: symmetry-trick probability, a low-latency order book in C++, a delta-1 system design, a hedging deep-dive, and a behavioral that probes decisions under uncertainty.

### Round 3.1: Probability
**Q:** Two iid normal(0, σ^2) variables. P(first > second | first > 0)?
**Answer:** By symmetry P(first > second) = 0.5; P(first > second and first > 0) = P(first > max(second, 0)) = ? Better: condition on first = x > 0: P(second < x) = Φ(x/σ). Integrate: ∫_0^∞ (2φ(x/σ)/σ) Φ(x/σ) dx = 3/4. So answer is 3/4.
**Tip:** Symmetry tricks; they go fast.

### Round 3.2: Coding
**Q:** Implement a low-latency order book with O(log n) insertions.
**Answer:** Use a sorted array per side with binary search, or skip list. Discuss cache-friendliness.
**Tip:** O(log n) is the bar; O(1) for top-of-book.

### Round 3.3: System design
**Q:** Design a delta-1 options market-making system.
**Answer:** Vol surface fit (SVI) → delta-1 hedge calculation → rebalancing scheduler → risk limits → market-making engine with skewing. Discuss gamma scalping, vol-of-vol, vega exposure.

### Round 3.4: Trading deep-dive
**Q:** How do you think about hedging a short straddle?
**Answer:** Delta hedge by trading underlying; gamma scalping to capture realized vs implied; vega hedge with longer-dated options; theta management with calendar spreads. Cite empirical results.
**Tip:** They want product intuition, not just math.

### Round 3.5: Behavioral
**Q:** Tell me about a time you made a decision under uncertainty.
**Answer:** STAR: process + outcome.

## Stage 4: Hiring committee
Panel of senior traders + researchers. They look for: (1) options intuition, (2) C++ depth, (3) collaborative spirit (Optiver is famously team-oriented).

## Stage 5: Offer
$250K-$500K base new grad; $500K-$800K+ experienced. Bonus is significant (often 50-100% of base). They pay top of market; little negotiation room.

## Tips for the Optiver loop

Most candidates over-index on equity vol and under-index on options Greeks in production. Optiver is options-first — show Greeks fluency.
- Read Optiver's "Trading Academy" articles.
- Memorize Black-Scholes, BSM, implied vol, Greeks.
- Practice C++ at a production level.
- Read Hull cover to cover.
- Be ready to discuss vol surface arbitrage.
- They prize teamwork; don't be a solo hero.

## Real candidate report
> "5 rounds, all math. They asked me to implement implied vol via Newton-Raphson, derive Black-Scholes, and design a delta-1 hedging system. They also had a trading round. Process was 3 weeks, offer $400K base + 100% bonus target." — Glassdoor, Quantitative Trader, 2025

## Sources
- [Optiver careers](https://optiver.com/working-at-optiver)
- [Optiver Trading Academy](https://optiver.com/insights/trading-academy)
- [Levels.fyi — Optiver](https://www.levels.fyi/companies/optiver)
- [Glassdoor — Optiver](https://www.glassdoor.com/Interview/Optiver-Interview-Questions-E1161490.htm)
- [Reddit r/quant — Optiver threads](https://reddit.com/r/quant)

---

## The 1 thing to remember

Optiver's math canon is the gate — Heard on the Street, Hull for options and Greeks, and clean vol-surface derivations are not optional, and an end-to-end delta-1 hedging design is the differentiator that pushes offers above band.