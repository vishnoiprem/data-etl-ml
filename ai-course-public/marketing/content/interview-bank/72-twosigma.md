# 72. Two Sigma

- **Role:** Quantitative Researcher / Quant SWE
- **Tech stack:** Python, C++, kdb+, Q, PyTorch, distributed systems, Spark, Slurm
- **Comp band:** $300K-$1M+ base + bonus (no public equity; "partner" comp)
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, motivation | 30 min | ~40% |
| 2. Technical phone | Probability, statistics, coding | 90 min | ~30% |
| 3. Onsite (4-5 rounds) | Math, coding, system design, ML, behavioral | 5-6 hrs | ~25% |
| 4. Hiring committee | Panel review | 1-2 wks | ~50% |
| 5. Offer | Comp, signing | 1 wk | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Two Sigma?"
**Answer:** "Two Sigma blends fundamental research with engineering. They ship ML to production at scale, and the partnership model means quants have skin in the game. I want to work where scientific rigor meets real P&L, not where I have to defend an engagement metric."
**Tip:** Reference specific Two Sigma research papers. They publish a lot, and interviewers check.

### Q1.2: "Why quant vs FAANG?"
**Answer:** "I'd rather bet my career on a feedback loop where P&L is the metric than on a proxy metric like engagement. The honesty of the scoreboard attracts me, and at FAANG I'd never know if my work actually mattered."
**Tip:** Have a real reason. They screen for the "money-driven" anti-pattern — don't oversell greed.

## Stage 2: Technical phone screen

### Q2.1: A fair coin is flipped 10 times; what's the probability of exactly 6 heads?
**Answer:** C(10,6) / 2^10 = 210/1024 ≈ 0.205.
**Tip:** They want clean combinatorial reasoning.

### Q2.2: Estimate the expected number of trailing zeros in 100! without computing it.
**Answer:** Floor(100/5) + floor(100/25) + floor(100/125) = 20 + 4 + 0 = 24.
**Tip:** Standard interview question; they care about problem decomposition.

## Stage 3: Onsite

### Round 3.1: Probability/statistics
**Q:** You have a Markov chain with transition matrix P. What's the stationary distribution? When does it exist?
**Answer:** πP = π; exists if chain is irreducible and aperiodic; unique up to scaling. Cite Perron-Frobenius.
**Tip:** This is canonical Two Sigma quant material.

### Round 3.2: Coding
**Q:** Implement a function to sample from a discrete distribution.
**Answer:**
```python
import random, bisect
def sample(weights):
    cum = []; s = 0
    for w in weights:
        s += w; cum.append(s)
    r = random.random() * s
    return bisect.bisect_left(cum, r)
```
**Tip:** Inverse-CDF sampling is the standard answer (O(log n) per sample). Mention the alias method for O(1) sampling after O(n) build — Two Sigma knows both.

### Round 3.3: ML deep-dive (math-heavy)
**Q:** Derive the gradient of logistic regression with L2 regularization.
**Answer:** L = -Σ y log p + (1-y) log(1-p) + λ/2 ||w||^2. ∂L/∂w = X^T(p-y) + λw. Set to zero (no closed form); use Newton-IRLS.
**Tip:** They want clean calculus on the board.

### Round 3.4: System design
**Q:** Design a real-time market data system processing 10M msgs/sec.
**Answer:** FPGA / kernel-bypass networking → ring buffer → in-memory kdb+ → publish-subscribe. Discuss tail latency, clock sync, market data normalization.

### Round 3.5: Behavioral
**Q:** Tell me about a research project that failed.
**Answer:** STAR: own it, explain what you learned, what you'd change.

## Stage 4: Hiring committee
Panel of 4-5 senior quants + 1 partner. They look for: (1) intellectual honesty, (2) real research taste, (3) production engineering rigor.

## Stage 5: Offer
Comp is partnership-track; signing bonus $50K-$200K. Vesting is unique to each "pod." They pay top of market — never undercut.

## Tips for the Two Sigma loop
- Memorize the greenbook (Heard on the Street) probability questions.
- Practice options pricing derivations (Black-Scholes, Greeks).
- Read Hull's "Options, Futures, and Other Derivatives" cover to cover.
- Be ready to derive every ML formula.
- Show research taste — name a paper you love and explain why.
- Don't oversell alpha; be honest about the bar.

## Real candidate report
> "5 rounds over 2 days, all math. They asked me to derive the CAPM, implement a discrete sampler, and design a real-time tick system. Onsite lunch with two partners was a soft interview too. Offer was $400K base + $300K sign-on. Whole process was 4 weeks." — Levels.fyi, Quant Researcher, 2025

## Sources
- [Two Sigma careers](https://www.twosigma.com/careers)
- [Levels.fyi — Two Sigma](https://www.levels.fyi/companies/two-sigma)
- [Glassdoor — Two Sigma](https://www.glassdoor.com/Interview/Two-Sigma-Interview-Questions-E859428.htm)
- [Heard on the Street — quant interview prep](https://www.amazon.com/Heard-Street-Quantitative-Interview/dp/0987122930)
- [Reddit r/quant — Two Sigma threads](https://reddit.com/r/quant)