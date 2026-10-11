# 34. DoorDash (ML / Logistics / Ads)

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual. Color: company brand color as accent. Headline on image: "DOORDASH / AI LOGISTICS / 2026".

> **TL;DR:** DoorDash's loop runs on **operational pressure** — every model has to ship in a 30-minute delivery window with real-time re-dispatch. The signature lens is **two-sided constraints** (dasher supply + consumer demand + restaurant load), and the winning candidate reaches for Hungarian matching and switchback experiments by reflex.

```
Recruiter (50%) → Phone (40%) → Onsite (30%) → Tech Panel (55%) → Offer
```

- **Role:** ML Engineer / Applied Scientist (Logistics, Ads Ranking, Search, Discovery)
- **Tech stack:** Python, PyTorch, TensorFlow, Scala, Kafka, Spark, Flink, Cassandra, Elasticsearch, Kinesis
- **Comp band:** $250K-$700K total comp (L3-L5) | RSUs 4-year, 1-year cliff + cash; senior crosses $900K+
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Org match (Logistics/Ads/Search), comp | 1 week | ~50% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML, behavior | 1-2 days | ~30% advance |
| 4. **Hiring committee (Tech Panel)** | Cross-org panel review | 1-2 weeks | ~55% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

DoorDash's loop is built for ops-aware engineers — the panel wants to see that you can ship a model that survives contact with the real world. "We win together" is the cultural operating system; show you've partnered with ops teams before.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why DoorDash for ML?"
**Answer:** "DoorDash's logistics is one of the most operationally complex ML systems in industry — real-time dispatch, batching, dasher assignment, all under 30 minutes. The Ads business (~$1B revenue) is a search-ranking-like problem at scale. I want to work on the marketplace math that powers millions of deliveries daily."
**Tip:** Reference *Dispatch*, *Dasher Assignment*, *Ads Ranking*, *Search*, *Caviar* — distinct teams.

### Q1.2: "Tell me about a logistics or marketplace project you shipped"
**Answer:** STAR with focus on *real-time decisions*, *two-sided constraints*, and *operational metrics*.
**Tip:** Show you understand marketplace dynamics under constraints.

## Stage 2: Technical phone screens (90 min)

The phone screens lean distributed-systems + real-time — if your solution doesn't reach for streaming and assignment optimization, you're missing the DoorDash frame. The ML round always returns to operational constraints.

### Q2.1: Coding: "Design a task scheduler"
**Answer:** Min-heap of (time, task_id) → peek for next. Thread-safe with locks.
```python
import heapq
import threading
import time

class Scheduler:
    def __init__(self):
        self.q, self.lock = [], threading.Lock()
    def schedule(self, t, task):
        with self.lock:
            heapq.heappush(self.q, (t, task))
    def run(self):
        while True:
            time.sleep(0.01)
            now = time.time()
            with self.lock:
                if self.q and self.q[0][0] <= now:
                    _, t = heapq.heappop(self.q)
                    t()
```
**Tip:** Real-time + scheduling questions are common. Distributed-systems flavored.

### Q2.2: ML: "Design DoorDash's dispatch model"
**Answer:** (1) Inputs — orders (location, prep time, items), dashers (location, vehicle, ratings), restaurants (capacity, prep time); (2) Objective — minimize ETA + maximize dasher utilization; (3) Constraints — vehicle type, dasher capacity, restaurant load; (4) Model — gradient boosting + assignment optimization (Hungarian); (5) Real-time re-dispatch; (6) Eval on delivered-on-time + dasher earnings; (7) A/B with switchback.
**Tip:** DoorDash logistics = real-time optimization + ML. Show both skills.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min, 2 questions)
- Q: Top K most frequent elements. Counter + heap.
- Q: Two sum / Three sum / Four sum. Hash map and DP variants.
- Optional 3rd: Graph problem, BFS/DFS in a 2D grid.

### Round 3.2: System design (60 min)
- Q: Design DoorDash's real-time dispatch system. Streaming features, location updates via Kafka, assignment service, optimized matching, and fallback ranking.
- Q: Design DoorDash Ads ranking. Sponsored listings in search, auction pricing, relevance model, CTR/CVR prediction, and A/B on incremental orders.

### Round 3.3: ML deep-dive (60 min)
- Q: How would you improve DoorDash's restaurant recommendation? Multi-objective (clicks, orders, repeat rate), personalization, cold start for new merchants, and dine-in vs delivery context.
- Q: How would you forecast demand at the 30-minute horizon for dasher supply? Time series model (DeepAR/TFT), event features (weather, sports), stochastic gradient boosting, and calibration.

### Round 3.4: Behavioral (60 min)
- Q: Tell me about a time you shipped something under operational pressure.
- Q: A time you worked with operations on a deploy.
- Q: Disagreement with a PM on a marketplace change.

## Stage 4: Hiring committee
A panel of senior engineers reviews. They look for: (1) ML bar for the level, (2) marketplace / logistics thinking, (3) DoorDash values (We Serve, We Win Together, Customer Obsession, Operate with Urgency, Solve for the Customer, Bias for Action), (4) impact at scale. Vote is "Strong Hire / Hire / No Hire / Strong No Hire."

## Stage 5: Offer
Cash + RSUs. DoorDash is competitive — FAANG-tier for senior+. Negotiation is real. Team match after loop. SF HQ is main hub; some roles in NYC, Toronto.

## Tips for the DoorDash loop
- Reference *Dispatch*, *Dasher Assignment*, *Ads Ranking*, *Caviar*, *DoorDash Drive* — distinct products.
- For ML rounds, emphasize *real-time decisions* and *operational constraints*.
- For system design, streaming + assignment optimization is the trifecta.
- DoorDash is *operations-driven* — show you can partner with ops teams.
- For behavioral, "we win together" stories score well — DoorDash is collaborative.
- Quantify scale: "millions of orders/day", "300K+ dashers", "30-min delivery".
- Reference DoorDash's published engineering blogs (interview series, etc.).

## Real candidate report
> "Loop for Logistics ML. 4 rounds in 1 day. The ML deep-dive was on real-time dispatch and they wanted me to discuss Hungarian matching + dynamic re-dispatch on cancellation. The system design was the streaming pipeline behind dispatch. Behavioral was 'bias for action' flavored. Offer at L4, ~$520K total, 5 weeks." — Blind, 2025-09

## Sources
- [DoorDash Careers](https://careersatdoordash.com/)
- [Levels.fyi DoorDash salaries](https://www.levels.fyi/companies/doordash/salaries)
- [DoorDash Engineering blog](https://doordash.engineering/)
- [DoorDash ML papers](https://doordash.engineering/tag/machine-learning/)
- [r/MachineLearning DoorDash thread](https://www.reddit.com/r/MachineLearning/)
