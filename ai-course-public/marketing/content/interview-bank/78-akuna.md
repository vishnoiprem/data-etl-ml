# 78. Akuna Capital

- **Role:** Quantitative Researcher / Quant Trader / Quant SWE
- **Tech stack:** C++, Python, kdb+, low-latency systems, options pricing
- **Comp band:** $200K-$700K total comp (Quant → Senior Quant) | Base + bonus (top of market; no public equity)
- **Cumulative pass rate:** ~4-5%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + an options pricing model (Black-Scholes surface) over a C++ order book grid, with a Chicago skyline silhouette. Color: Akuna red (#D32F2F). Headline: "Akuna Capital / Quantitative Researcher & SWE / 2026".

> **TL;DR:** Akuna is a smaller options-focused shop where you'll own systems end-to-end — the bar is still high but mentorship is direct. The signature round is the onsite: a 100-prisoners puzzle, an order book in C++, and an options market-making system. The winning candidate has read Hull, can write C++ on a whiteboard, and shows collaborative instinct.

```
Recruiter → Phone (math) → Onsite (4 rounds) → Hiring committee → Offer
```

The math → C++ → options progression is the spine. Show authentic interest in a smaller shop — they prize that over brand name.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, fit | 30 min | ~50% |
| 2. Technical phone | Probability, statistics, coding | 60 min | ~35% |
| 3. Onsite (4 rounds) | Math, coding, system design, trading, behavioral | 4-5 hrs | ~30% |
| 4. Hiring committee | Cross-team review | 1-2 wks | ~60% |
| 5. Offer | Comp negotiation | 1 wk | — |

## Stage 1: Recruiter screen

The screen rewards authenticity. Have a real reason for a smaller shop, and a specific reason for working in options.

### Q1.1: "Why Akuna over bigger shops?"
**Answer:** "Akuna's options market-making franchise is top-tier, and being smaller than the megafunds means I get more direct mentorship and more scope to own systems end-to-end."
**Tip:** Show you've researched the firm — they prize authenticity over brand name.

### Q1.2: "Why options?"
**Answer:** "I like the constraint of working in a defined-vol space — the Greeks force you to think about every P&L attribution."
**Tip:** Have a real reason; they screen for the "money vs math" axis.

## Stage 2: Technical phone screen

The phone is variance derivations and a C++ binary search. Edge cases and overflow awareness are screened.

### Q2.1: 6-sided die; what's the variance of a single roll?
**Answer:** E[X^2] - E[X]^2 = 91/6 - 3.5^2 ≈ 2.917.
**Tip:** Clean; be precise.

### Q2.2: Implement binary search in C++.
**Answer:**
```cpp
int bsearch(const std::vector<int>& a, int x) {
    int l = 0, r = a.size() - 1;
    while (l <= r) {
        int m = l + (r - l) / 2;
        if (a[m] == x) return m;
        if (a[m] < x) l = m + 1; else r = m - 1;
    }
    return -1;
}
```
**Tip:** Watch for overflow; they test edge cases.

## Stage 3: Onsite

Four rounds: 100-prisoners probability, an order book in C++, an options market-making system design, and a combined trading-game + behavioral.

### Round 3.1: Probability
**Q:** 100 prisoners problem — 100 boxes, each containing a unique number 1-100. Prisoners find their own number in <50 tries. Optimal strategy: open box with their own number first, then the number they see. P(all win)?
**Answer:** (1 - 1/100 + 1/100 * 1/99 - ...) ≈ 0.3118. (Cycle decomposition: >50% if cycles ≤ 50, ~31% if uniformly random.)
**Tip:** Classic puzzle; derive the cycle logic.

### Round 3.2: Coding
**Q:** Implement an order book in C++.
**Answer:** Same as other prop shops — price-time priority, intrusive lists, pre-allocated memory.
**Tip:** They test C++ deeply.

### Round 3.3: System design
**Q:** Design an options market-making system.
**Answer:** Pricing model (BSM) → vol surface → market-making engine → risk aggregator → hedge router. Discuss latency, Greeks computation, vol skew.

### Round 3.4: Trading + behavioral
**Q:** Play a market-making game.
**Q:** Tell me about a recent project you're proud of.
**Answer:** Combine trading simulation with a STAR on a recent build.

## Stage 4: Hiring committee
Panel of senior traders + researchers. They look for: (1) options fluency, (2) C++ depth, (3) collaborative spirit.

## Stage 5: Offer
$200K-$500K base new grad; $400K-$700K+ experienced. Bonus is significant.

## Tips for the Akuna loop

Most candidates treat Akuna as a backup. Authenticity about the firm is the gate; bring a real reason for a smaller shop.
- Read Hull's options chapters.
- Practice the 100 prisoners problem and other classics.
- Memorize Black-Scholes derivations.
- Be ready to write C++ on a whiteboard.
- Show collaborative instinct — they screen for it.
- Akuna is in Chicago and Sydney; mention location fit.

## Real candidate report
> "4 rounds, all math. They asked the 100 prisoners problem, implied vol, and an order book. Akuna was less intense than Jane Street but the math bar was still high. Offer $350K base + 100% bonus for new grad." — Glassdoor, Quant Trader, 2025

## Sources
- [Akuna Capital careers](https://akunacapital.com/careers)
- [Akuna coding challenge](https://akunacapital.com/careers/coding-challenge)
- [Levels.fyi — Akuna Capital](https://www.levels.fyi/companies/akuna-capital)
- [Glassdoor — Akuna Capital](https://www.glassdoor.com/Interview/Akuna-Capital-Interview-Questions-E1355180.htm)
- [Reddit r/quant — Akuna threads](https://reddit.com/r/quant)

---

## The 1 thing to remember

Akuna's math canon is the gate — Heard on the Street, Hull for options, and 100-prisoners-style puzzle derivations are not optional, and clean C++ on a whiteboard is the differentiator that pushes offers above band.