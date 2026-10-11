# 31. Uber (ML Platform / Michelangelo / Dynamic Pricing)

- **Role:** ML Engineer (Michelangelo, Pricing, Eats Ranking, Autonomous)
- **Tech stack:** Python, PyTorch, TensorFlow, Go, Java, Spark, Kafka, Michelangelo (Uber's internal ML platform), H3 geospatial
- **Comp band:** $250K-$700K (L4-L6); senior crosses $900K+; RSUs vest 4-year
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Org match (Michelangelo/Pricing/Eats/ATG), comp | 1 week | ~50% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML, behavior | 1-2 days | ~30% advance |
| 4. **Hiring committee (Tech Panel)** | Cross-org panel review | 1-2 weeks | ~55% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Uber for ML?"
**Answer:** "Three reasons. First, Michelangelo is the most battle-tested ML platform at scale — it powers Uber Eats, Rides, and Driver incentives. Second, the marketplace ML challenges (dynamic pricing, ETA, dispatch) are some of the most interesting in industry. Third, I want to work on the geospatial stack (H3) which is open source."
**Tip:** Reference *Michelangelo*, *H3*, *Pyro* (Uber's probabilistic programming language), *Deck.gl*.

### Q1.2: "Describe a marketplace ML project you've shipped"
**Answer:** STAR with focus on *two-sided dynamics*, *supply-demand balance*, and *causal impact*. Uber problems are inherently two-sided.
**Tip:** Show you understand marketplace feedback loops — pricing affects supply which affects pricing.

## Stage 2: Technical phone screens (90 min)

### Q2.1: Coding: "Design a rate limiter"
**Answer:** Token bucket (deque with timestamps) or sliding window counter.
```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, limit, window):
        self.limit, self.window = limit, window
        self.events = deque()
    def allow(self):
        now = time.time()
        while self.events and self.events[0] < now - self.window:
            self.events.popleft()
        if len(self.events) < self.limit:
            self.events.append(now); return True
        return False
```
**Tip:** Distributed-systems questions are common — rate limiting, leader election, idempotency.

### Q2.2: ML: "Design Uber's dynamic pricing model"
**Answer:** (1) Inputs — supply (drivers online by H3 hex), demand (riders, destination), ETA, traffic, events (concerts, weather); (2) Model — gradient boosting on tabular features + neural for embeddings; (3) Two-sided: must model impact on driver acceptance + rider conversion; (4) Causal uplift on supply, not just predictive; (5) Constraints — fairness caps, regulatory; (6) Online at 50ms; (7) A/B with switchback design (since users see prices).
**Tip:** Uber ML is *two-sided*. Show you think about supply *and* demand.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min, 2 questions)
- Q: Implement a thread-safe LRU cache (concurrency).
- Q: Find K-th largest in array. Quickselect, O(N) avg.
- Optional 3rd: Graph problem, e.g., "Cheapest flight within K stops."

### Round 3.2: System design (60 min)
- Q: Design Michelangelo's feature store. Online (Cassandra) + offline (Hive/Spark), point-in-time joins, freshness SLOs, and multi-tenant.
- Q: Design a real-time ETA model. Streaming features, geospatial indexing (H3), gradient boosting with map-matching, and sub-second inference.

### Round 3.3: ML deep-dive (60 min)
- Q: How would you improve Uber Eats restaurant ranking? Multi-objective (clicks, orders, GMV, retention), position bias, diversity, and cold start for new restaurants.
- Q: How would you build a dispatch model for Uber Rides? Bipartite matching under constraints (driver location, ETA), and reinforcement learning to optimize long-term marketplace health.

### Round 3.4: Behavioral (60 min)
- Q: Tell me about a time you dealt with conflicting metrics. Two-sided markets have this constantly.
- Q: A time you shipped imperfect work to learn. Uber values "build and iterate."
- Q: Disagreement with a PM on a marketplace change.

## Stage 4: Hiring committee
A panel of senior engineers + PM reviews. They look for: (1) ML bar for the level, (2) marketplace / systems thinking, (3) Uber values (Customer Obsession, Curiosity, Boldness, Inclusion, Integrity), (4) impact at scale. Vote is "Strong Hire / Hire / No Hire / Strong No Hire."

## Stage 5: Offer
Cash + RSUs. Uber is competitive with FAANG. Negotiation is real. Team match after loop. San Francisco HQ is the main hub; some roles in NYC, Seattle, Toronto.

## Tips for the Uber loop
- Reference *Michelangelo*, *H3*, *Pyro*, *Deck.gl* by name — they're all open source.
- For ML rounds, emphasize *two-sided dynamics* and *causal inference*.
- For system design, geospatial indexing (H3) and real-time streaming are common.
- Uber culture is "we build and iterate" — show shipping speed.
- Switchback experiments are Uber's hallmark — be ready to discuss.
- For behavioral, customer obsession is real — both rider and driver.
- Quantify scale: "millions of trips/day", "10K QPS on pricing", "p99 < 100ms."

## Real candidate report
> "Loop for Michelangelo ML Platform. 4 rounds in 1 day. Coding was 2 mediums (LRU + K-th largest). System design was the Michelangelo feature store with point-in-time joins. ML deep-dive was dynamic pricing and they pushed me on causal vs predictive and supply-side fairness. Behavioral was customer-obsession flavored. Offer at L5, ~$580K total, 5 weeks." — r/MachineLearning, 2025-09

## Sources
- [Uber Careers](https://www.uber.com/careers/)
- [Levels.fyi Uber salaries](https://www.levels.fyi/companies/uber/salaries)
- [Uber Engineering blog](https://www.uber.com/blog/engineering/)
- [Michelangelo paper](https://eng.uber.com/scaling-michelangelo/)
- [H3 GitHub](https://github.com/uber/h3)
