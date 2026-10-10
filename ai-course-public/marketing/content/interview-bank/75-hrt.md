# 75. Hudson River Trading (HRT)

- **Role:** Quantitative Researcher / Quant SWE / Algorithm Engineer
- **Tech stack:** C++ (heavily!), Python, Rust, kdb+, FPGA, low-latency systems
- **Comp band:** $300K-$1M+ base + bonus (no public equity; partnership-style)
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, fit | 30 min | ~50% |
| 2. Technical phone | Probability, statistics, coding | 60 min | ~30% |
| 3. Onsite (4-5 rounds) | Math, coding (often C++), system design, ML, behavioral | 5-6 hrs | ~25% |
| 4. Hiring committee | Cross-team review | 1-2 wks | ~60% |
| 5. Offer | Comp negotiation | 1 wk | — |

## Stage 1: Recruiter screen

### Q1.1: "Why HRT?"
**Answer:** "HRT is the only trading firm that builds its own silicon and writes the lowest-latency C++ in the industry. I want to work where the research and the engineering are both world-class."
**Tip:** Reference HRT's "Technical Reflections" blog and their FPGA work.

### Q1.2: "Why low-latency systems?"
**Answer:** "I love the combination of math and systems — to shave microseconds, you need both a good model and a great kernel. That's the rare intersection HRT sits at."
**Tip:** Show genuine excitement for systems work.

## Stage 2: Technical phone screen

### Q2.1: You draw 5 cards from a deck. P(royal flush)?
**Answer:** 4 / C(52,5) = 4 / 2,598,960 ≈ 1.54e-6.
**Tip:** Combinatorics; be precise.

### Q2.2: Implement a thread-safe queue in C++.
**Answer:**
```cpp
template<typename T>
class TSQueue {
    std::queue<T> q; std::mutex m;
public:
    void push(T v) { std::lock_guard<std::mutex> g(m); q.push(std::move(v)); }
    bool try_pop(T& v) { std::lock_guard<std::mutex> g(m); if (q.empty()) return false; v = std::move(q.front()); q.pop(); return true; }
};
```
**Tip:** They want C++ fluency; mention lock-free variants (moodycamel queue).

## Stage 3: Onsite

### Round 3.1: Probability
**Q:** A stock is at $100, vol 20% annual, r = 5%. Value a 1-year ATM call.
**Answer:** Use Black-Scholes: C = S*N(d1) - K*e^(-rT)*N(d2), with d1 = (ln(S/K) + (r+σ^2/2)T)/(σ√T), d2 = d1 - σ√T. With S=K=100, T=1, r=0.05, σ=0.2: d1 ≈ 0.35, d2 ≈ 0.15; N(0.35) ≈ 0.6368, N(0.15) ≈ 0.5596; C ≈ 10.45.
**Tip:** Walk through the derivation; they'll ask.

### Round 3.2: Coding
**Q:** Implement a low-latency order book in C++.
**Answer:** Use price-time priority with intrusive lists, pre-allocated memory pool, lock-free reads with per-thread caches, atomic operations. Discuss micro-benchmarking, false sharing, cache alignment.
**Tip:** This is the core HRT system; show depth.

### Round 3.3: System design
**Q:** Design a market data feed handler processing 10M msgs/sec.
**Answer:** Kernel-bypass (DPDK/Solarflare) → fixed-size ring buffer → SIMD parsing → L3 cache-friendly order book → publish via shared memory. Discuss packet loss, sequence gaps, jitter buffers.

### Round 3.4: ML/math
**Q:** Derive the Kalman filter update step.
**Answer:** Predict: x̂⁻ = F x̂, P⁻ = FP F^T + Q. Update: K = P⁻ H^T (H P⁻ H^T + R)^{-1}, x̂ = x̂⁻ + K(z - H x̂⁻), P = (I - KH) P⁻.
**Tip:** They use Kalman for various signal models.

### Round 3.5: Behavioral
**Q:** Tell me about a time you optimized a system by 10x.
**Answer:** STAR with metrics — show technical depth.

## Stage 4: Hiring committee
Panel of senior quants + engineers. They look for: (1) C++/systems depth, (2) math rigor, (3) taste for performance.

## Stage 5: Offer
$300K-$700K base new grad; $500K-$1M+ experienced. Signing $100K-$400K. They pay top of market; little counter-room.

## Tips for the HRT loop
- Practice C++ at the level of "Effective Modern C++."
- Read the HRT blog — they publish deep technical essays.
- Memorize options pricing + Kalman filter derivations.
- Practice lock-free data structures on paper.
- Be ready to discuss kernel-bypass networking.
- Show you can ship performance-critical code.

## Real candidate report
> "4 rounds in one day, all math and C++. They asked me to implement a low-latency order book, derive Black-Scholes, and explain false sharing. Their bar is the bar. Got the offer 2 weeks later, $450K base + $300K sign-on for a senior SWE." — Levels.fyi, Algorithm Engineer, 2025

## Sources
- [HRT careers](https://www.hudsonrivertrading.com/careers)
- [HRT Technical Reflections](https://www.hudsonrivertrading.com/hrtview)
- [Levels.fyi — HRT](https://www.levels.fyi/companies/hudson-river-trading)
- [Glassdoor — HRT](https://www.glassdoor.com/Interview/Hudson-River-Trading-Interview-Questions-E403132.htm)
- [Reddit r/quant — HRT threads](https://reddit.com/r/quant)