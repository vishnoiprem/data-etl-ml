# 33. Airbnb (ML / Search & Discovery)

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual. Color: company brand color as accent. Headline on image: "AIRBNB / AI SEARCH / 2026".

> **TL;DR:** Airbnb's loop is **search-heavy** and mission-driven — the trinity is long-tail handling, cold-start, and offline/online metric alignment. The signature lens is **"belong anywhere"** — every behavioral answer gets reframed through craft and host empathy. The winning candidate reads the Airbnb Tech Blog before the loop and quotes it back.

```
Recruiter (50%) → Phone (35%) → Onsite (30%) → Tech Panel (55%) → Offer
```

- **Role:** ML Engineer / Applied Scientist (Search Ranking, Recommendations, Trust, LLM)
- **Tech stack:** Python, PyTorch, Java, Kotlin, Scala, Spark, Kafka, Druid, MySQL, Elasticsearch, ML infra
- **Comp band:** $300K-$850K total comp (L4-L6) | RSUs 4-year, 1-year cliff; senior crosses $1M+
- **Cumulative pass rate:** ~1-2%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Org match (Search/Trust/Payments), comp | 1 week | ~50% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML | 1-2 weeks | ~35% advance |
| 3. **Onsite (4-5 rounds)** | Coding, system design, ML, behavior, cross-fn | 1-2 days | ~30% advance |
| 4. **Hiring committee (Tech Panel)** | Cross-org panel review | 1-2 weeks | ~55% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

Airbnb's loop is the most "bar-raising" of the marketplace companies — the panel is famously calibrated, and "no hire" is the default when signal is mixed. Read the tech blog before your loop; it's the cheapest competitive advantage you can buy.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Airbnb for ML?"
**Answer:** "Airbnb's search ranking is one of the most challenging in industry — long-tail listings, seasonal demand, two-sided trust, and the most-shared user review system on the web. The published research on the listing embedding and ranking models is what I've studied for years. I want to ship search that helps guests find places that genuinely fit them."
**Tip:** Reference specific Airbnb research posts — listing embeddings, TRIPS, host-side ML — they're publicly loved.

### Q1.2: "Tell me about a search or ranking model you shipped"
**Answer:** STAR with focus on *long-tail item handling*, *position bias*, and *offline/online metric alignment*.
**Tip:** Airbnb ML is *search-heavy*. Show you understand ranking.

## Stage 2: Technical phone screens (90 min)

The phone screens are where Airbnb quietly tests for *search depth* — multi-objective ranking, position bias, and the two-sided host/guest dynamic. If you don't name specific Airbnb research posts (TRIPS, listing embeddings), you're behind.

### Q2.1: Coding: "Implement a trie with insert/search/startsWith"
**Answer:** Node-based with 26 children. O(L) per operation.
**Tip:** Some roles use Java or Kotlin. Confirm with recruiter.

### Q2.2: ML: "Design Airbnb's search ranking model"
**Answer:** (1) Query understanding — natural-language query parsing, location disambiguation; (2) Retrieval — Elasticsearch lexical + dense bi-encoder (listing embeddings); (3) Ranking — LightGBM with cross features + neural ranker; (4) Features — query-listing cross, host quality, guest historical, seasonality, price elasticity; (5) Multi-objective — NDCG, booking prob, host acceptance; (6) Position bias debiasing; (7) A/B on bookings.
**Tip:** Airbnb has published extensively — reference specific models.

## Stage 3: Onsite (4-5 rounds)

The onsite is dense and design-conscious. Five rounds means a dedicated cross-functional slot — that's your chance to show partnership with PM and design, which is a real signal at Airbnb.

### Round 3.1: Coding (60 min, 2 questions)
- Q: LRU cache. O(1) get/put.
- Q: Find median from data stream. Two heaps.
- Optional 3rd: Graph/tree problem.

### Round 3.2: System design (60 min)
- Q: Design Airbnb's listings embeddings pipeline. Trip-level aggregation, multi-tower with listing + trip context, batch + streaming updates, and serving via ANN (ScaNN/FAISS).
- Q: Design Airbnb's experimentation platform. Bucket assignment, interleaving (AIR), variance reduction (CUPED), switchback, A/A testing, and dashboards.

### Round 3.3: ML deep-dive (60 min)
- Q: How would you handle cold-start for new Airbnb listings? Content-based (photos via CLIP, descriptions via LLM embeddings), host prior, exploration via geometric uplift, and popularity priors.
- Q: How would you improve the host acceptance rate model? Two-sided acceptance, decline reasons (price, calendar), feature importance, and propensity modeling.

### Round 3.4: Cross-functional (45 min)
- Q: Tell me about a time you worked with PM and design on a model-driven product. Airbnb is design-conscious.
- Q: A time you changed the product based on data insights.

### Round 3.5: Behavioral (45 min)
- Q: Tell me about a time you lived Airbnb's value of "belong anywhere." Mission-driven culture.
- Q: A time you dealt with ambiguity. Startup-feel within Airbnb.
- Q: Disagreement with a peer on a model design.

## Stage 4: Hiring committee
A panel of senior engineers + scientists reviews. They look for: (1) ML bar for the level, (2) Airbnb values (Champion the Mission, Be a Host, Embrace the Adventure, Be a Cereal Entrepreneur), (3) cross-functional collaboration, (4) craft and quality. Vote is "Strong Hire / Hire / No Hire / Strong No Hire." Airbnb is known for high bar.

## Stage 5: Offer
Cash + RSUs (heavily RSU-weighted). Airbnb is *top-of-market* — competitive with Meta/Google for senior+. Negotiation is real. Team match after loop. SF HQ is main hub.

## Tips for the Airbnb loop
- Read the Airbnb Tech Blog & research posts before your interview — reference them by name.
- For ML rounds, emphasize *long-tail handling* and *cold-start* — they're pain points.
- For system design, search + embeddings + experimentation are the trifecta.
- For behavioral, mission-driven stories score well — "belong anywhere."
- Cross-functional collaboration matters — show you can partner with PM, design, data.
- For senior+, show *tech leadership* — Airbnb values "entrepreneurship" within teams.
- Quantify scale: "8M listings", "1B reviews", "100M+ guests".

## Real candidate report
> "Loop for Search Ranking. 5 rounds in 2 days. The ML deep-dive was on listing embeddings and they wanted me to discuss trip-context windows and update latency trade-offs. The system design was the embeddings pipeline + serving. Behavioral was 'be a host' flavored. Offer at L5, ~$640K total, 4 weeks." — Blind, 2025-11

## Sources
- [Airbnb Careers](https://careers.airbnb.com/)
- [Levels.fyi Airbnb salaries](https://www.levels.fyi/companies/airbnb/salaries)
- [Airbnb Tech Blog](https://medium.com/airbnb-engineering)
- [Airbnb Research](https://research.airbnb.com/)
- [r/MachineLearning Airbnb thread](https://www.reddit.com/r/MachineLearning/)

---

## The 1 thing to remember

At Airbnb, read the tech blog before the loop and quote it back — name listing embeddings, TRIPS, and "be a host," because the panel is calibrated to the Airbnb voice and a generic ML answer sinks you.
