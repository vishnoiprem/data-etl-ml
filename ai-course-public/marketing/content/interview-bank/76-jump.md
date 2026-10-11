# 76. Jump Trading

- **Role:** Quantitative Researcher / Quant SWE / Algorithm Engineer
- **Tech stack:** C++ (primary), Python, Rust, FPGA, low-latency systems, kdb+
- **Comp band:** $300K-$900K total comp (Algo Eng → Senior Algo Eng) | Base + bonus (top of market; no public equity)
- **Cumulative pass rate:** ~2-3%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + a cross-exchange state machine with normalized protocol adapters, latency-arb arrows, and a crypto order book inset. Color: Jump indigo (#1A237E). Headline: "Jump Trading / Quantitative Researcher & SWE / 2026".

> **TL;DR:** Jump runs a tight research loop and moves serious size in crypto and equities — alpha drive plus C++ rigor is the bar. The signature round is the onsite: a C++ order book, an inclusion-exclusion probability puzzle, and a cross-exchange market-making design. The winning candidate has shipped systems that handle real money and can defend a measurable optimization win.

```
Recruiter → Phone (math) → Onsite (4-5 rounds) → Hiring committee → Offer
```

The math → C++ → systems progression is the spine. Skip crypto market-microstructure prep and you don't get the offer.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, fit | 30 min | ~50% |
| 2. Technical phone | Probability, statistics, coding | 60 min | ~30% |
| 3. Onsite (4-5 rounds) | Math, coding, system design, ML, behavioral | 5-6 hrs | ~25% |
| 4. Hiring committee | Cross-team review | 1-2 wks | ~60% |
| 5. Offer | Comp negotiation | 1 wk | — |

## Stage 1: Recruiter screen

The screen rewards alpha drive. Reference Jump Crypto and the prediction markets push, and bring a specific latency or throughput number.

### Q1.1: "Why Jump?"
**Answer:** "Jump runs a tight research loop and the firm already moves serious size in crypto and equities. I want to be on the team that's finding alpha across asset classes, especially as the crypto side matures past the retail phase."
**Tip:** Reference Jump Crypto and the prediction markets push. Mention a specific alpha source you've studied.

### Q1.2: "Tell me about a system you optimized."
**Answer:** STAR with a specific latency or throughput number — Jump rewards measurable wins.

## Stage 2: Technical phone screen

The phone is inclusion-exclusion combinatorics plus a C++ memory-pool implementation. They expect production-quality code.

### Q2.1: 4 dice are rolled. P(sum is 14)?
**Answer:** Count compositions of 14 into 4 parts each in [1,6]. By inclusion-exclusion: C(13,3) - 4·C(7,3) + 6·C(1,3) = 286 - 140 + 0 = 146. P = 146/1296 ≈ 0.1127.
**Tip:** They expect inclusion-exclusion when the parts are bounded, not raw stars-and-bars.

### Q2.2: Implement a memory pool in C++.
**Answer:**
```cpp
class Pool {
    char* buf; size_t sz, off;
public:
    Pool(size_t n) : buf(new char[n]), sz(n), off(0) {}
    void* alloc(size_t n) {
        n = (n + alignof(std::max_align_t) - 1) & ~(alignof(std::max_align_t) - 1);
        if (off + n > sz) return nullptr;
        void* p = buf + off; off += n; return p;
    }
};
```
**Tip:** Show alignment awareness; they care about production code.

## Stage 3: Onsite

Five rounds: geometric-distribution probability, an order book in C++, cross-exchange crypto market-making design, linear-regression derivation, and a behavioral that probes shipping under extreme time pressure.

### Round 3.1: Probability
**Q:** You sample N(0,1) until |x| > 2. Expected number of samples?
**Answer:** P(|x| > 2) = 2(1 - Φ(2)) ≈ 0.0455. Expected = 1/0.0455 ≈ 22.
**Tip:** Geometric distribution; clean.

### Round 3.2: Coding
**Q:** Implement an order book with price-time priority.
**Answer:** Per-price-level doubly-linked list of orders, intrusive pointers, pre-allocated order IDs, lock-free reads.
**Tip:** Like HRT; this is core to all prop shops.

### Round 3.3: System design
**Q:** Design a crypto market-making system across 5 exchanges.
**Answer:** Per-exchange FIX/WebSocket adapter → normalized internal protocol → cross-exchange state machine → risk aggregator → centralized order router. Discuss latency arbitrage, inventory, message sequencing.

### Round 3.4: ML/math
**Q:** Derive the closed-form for linear regression.
**Answer:** L = ||Xw - y||^2; ∂L/∂w = 2 X^T(Xw - y) = 0; w = (X^T X)^{-1} X^T y. Discuss conditioning, regularization, SVD for stability.
**Tip:** They want matrix calculus fluency.

### Round 3.5: Behavioral
**Q:** Tell me about a time you had to ship a system under extreme time pressure.
**Answer:** STAR with specific constraints.

## Stage 4: Hiring committee
Panel of senior quants + engineers. They look for: (1) C++/systems depth, (2) cross-asset intuition, (3) alpha drive.

## Stage 5: Offer
$300K-$700K base new grad; $500K-$900K+ experienced. Signing $100K-$400K.

## Tips for the Jump loop

Most candidates under-prep crypto market microstructure. Jump's crypto bet is a real differentiator — show you've studied it.
- Practice C++ at a production level.
- Read "Effective Modern C++" cover to cover.
- Memorize the linear regression + logistic regression derivations.
- Be ready to discuss crypto market microstructure.
- Show you've shipped systems that handle real money.
- They prize intellectual honesty and competitive drive.

## Real candidate report
> "5 rounds, all math and C++. They asked me to implement an order book from scratch, derive logistic regression, and design a cross-exchange system. Offer came in 10 days, $500K base + $300K sign-on." — Levels.fyi, Algorithm Engineer, 2025

## Sources
- [Jump Trading careers](https://www.jumptrading.com/careers)
- [Jump Crypto](https://www.jumpcrypto.com)
- [Levels.fyi — Jump Trading](https://www.levels.fyi/companies/jump-trading)
- [Glassdoor — Jump Trading](https://www.glassdoor.com/Interview/Jump-Trading-Interview-Questions-E449716.htm)
- [Reddit r/quant — Jump threads](https://reddit.com/r/quant)

---

## The 1 thing to remember

Jump's math canon is the gate — Heard on the Street, Hull for options, and clean linear/logistic regression derivations are not optional, and a measurable C++ optimization win is the differentiator that pushes offers above band.