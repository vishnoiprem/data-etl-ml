# 73. Jane Street

- **Role:** Quant Trader / Quant Researcher / Quant SWE
- **Tech stack:** OCaml (primary!), Python, C++, kdb+, React, distributed systems
- **Comp band:** $300K-$1.2M base + bonus (no public equity; "partner" track)
- **Cumulative pass rate:** ~1-2% (one of the hardest)

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, fit | 30 min | ~40% |
| 2. Probability phone | 25 probability puzzles | 60 min | ~20% |
| 3. Trading phone | Market making simulation | 60 min | ~40% |
| 4. Onsite (4-5 rounds) | Math, coding, trading, system design, behavioral | 5-6 hrs | ~30% |
| 5. Hiring committee | Panel review | 1-2 wks | ~60% |
| 6. Offer | Comp, signing | 1 wk | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Jane Street?"
**Answer:** "JS is the best trading firm in the world at the things I'm best at — collaborative research, honest culture, real markets. I want to work at a place that has the brainpower to do statistical arbitrage in 50 markets simultaneously."
**Tip:** Reference JS's open-source contributions (Core, Incremental, owl) and the culture docs.

### Q1.2: "Why OCaml?"
**Answer:** "Type safety prevents whole classes of trading bugs; pattern matching is perfect for parsing market data; the speed is C-like. I learned it specifically because JS uses it."
**Tip:** If you say "I want to learn OCaml," it's a red flag. They want functional fluency.

## Stage 2: Probability phone (25 puzzles in 60 min)

### Q2.1: You roll a fair die 3 times. What's the probability of at least one 6?
**Answer:** 1 - (5/6)^3 = 91/216 ≈ 0.421.
**Tip:** Jane Street's probability phone is 25 questions in 60 min — speed matters.

### Q2.2: A box has 3 red and 2 blue balls. You draw 2 without replacement. P(both red)?
**Answer:** C(3,2)/C(5,2) = 3/10 = 0.3.
**Tip:** Combinatorics basics; they escalate fast.

## Stage 3: Trading phone

### Q3.1: Play a market-making game. Quote bid/ask, manage inventory, react to fills.
**Answer:** Quote tight when inventory is 0; skew to dump inventory; never take the other side's loss; use volatility estimate to widen/tighten; track P&L per trade.
**Tip:** They want to see that you think about edge, not just quoting.

## Stage 4: Onsite

### Round 4.1: Probability/statistics
**Q:** Derive the bias of the sample variance estimator.
**Answer:** E[S^2] = σ^2 * (n-1)/n, so sample variance underestimates. Bessel's correction (divide by n-1) gives unbiased estimator.
**Tip:** They want derivations, not just definitions.

### Round 4.2: Coding (often OCaml)
**Q:** Implement a function to find the longest palindromic substring.
**Answer:** Expand-around-center O(n^2) in OCaml. Show pattern matching.
**Tip:** They sometimes allow Python but OCaml signals seriousness.

### Round 4.3: Trading deep-dive
**Q:** How do you think about adverse selection in market making?
**Answer:** Wider spreads for toxic flow, inventory skewing, short-term alpha signals to detect informed traders, information-ratio optimization, cite Avellaneda-Stoikov.

### Round 4.4: System design
**Q:** Design a market-making system for 1,000 instruments.
**Answer:** Per-instrument pricing model + cross-instrument risk aggregator + unified position management + automated hedging. Discuss latency, data integrity, kill switches.

### Round 4.5: Behavioral
**Q:** Tell me about a time you had to update a belief.
**Answer:** STAR: intellectual humility, specific update, what triggered it.

## Stage 5: Hiring committee
Panel of senior traders + researchers. They look for: (1) intellectual honesty, (2) collaborative spirit (Jane Street famously prizes teamwork), (3) genuine curiosity about markets.

## Stage 6: Offer
Top of market; $400K-$1.2M base + $200K-$500K sign-on for new grads; partnership track after ~2 years.

## Tips for the Jane Street loop
- Practice 25 probability questions in 60 min — speed drill.
- Read Avellaneda-Stoikov market making paper.
- Memorize the bias/MSE derivations for common estimators.
- Build something non-trivial in OCaml.
- Read Jane Street's Tech blog (they publish great trading essays).
- Be honest; they screen for overconfidence.

## Real candidate report
> "The probability phone is brutal — 25 questions in 60 min, escalating in difficulty. I prepped for 6 weeks with Heard on the Street. Onsite had 5 rounds, all math. The culture fit round was the hardest — they want intellectual humility, not alpha-bragging. Got the offer 2 weeks later, $500K base + $300K sign-on." — Levels.fyi, Quantitative Trader, 2025

## Sources
- [Jane Street careers](https://www.janestreet.com/join-jane-street)
- [Jane Street Tech blog](https://blog.janestreet.com)
- [Levels.fyi — Jane Street](https://www.levels.fyi/companies/jane-street)
- [Glassdoor — Jane Street](https://www.glassdoor.com/Interview/Jane-Street-Interview-Questions-E275940.htm)
- [Reddit r/quant — Jane Street threads](https://reddit.com/r/quant)