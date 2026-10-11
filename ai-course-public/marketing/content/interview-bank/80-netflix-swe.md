# 80. Netflix (Streaming SWE)

- **Role:** Senior Software Engineer (Streaming / Cloud / Personalization platform)
- **Tech stack:** Java, Kotlin, Python, Scala, Cassandra, Kafka, Flink, AWS, React, Spinnaker
- **Comp band:** $300K-$900K total comp (L5-L7: Senior → Staff) | Base + RSUs (public)
- **Cumulative pass rate:** ~2-3% (high bar)

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + an Open Connect CDN map with adaptive bitrate (ABR) ladder inset and a Kafka → Flink → Cassandra event pipeline. Color: Netflix red (#E50914). Headline: "Netflix / Streaming SWE / 2026".

> **TL;DR:** Netflix hires senior engineers with high judgment — "freedom and responsibility" isn't a poster, it's the actual bar. The signature round is the system design for the video streaming pipeline: ingest, transcode, Open Connect CDN, ABR. The winning candidate has a specific Netflix area of interest and can defend a high-judgment behavioral answer.

```
Recruiter → Phone (coding) → Onsite (4-5 rounds) → Hiring committee → Offer
```

The coding → system design → judgment progression is the spine. Skip the culture memo and you don't pass the behavioral.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, fit | 30 min | ~50% |
| 2. Technical phone | Coding + system design lite | 60 min | ~40% |
| 3. Onsite (4-5 rounds) | Coding (2), system design, behavioral, hiring manager | 4-5 hrs | ~30% |
| 4. Hiring committee | Panel review | 1-2 wks | ~60% |
| 5. Offer | Comp negotiation | 1 wk | — |

## Stage 1: Recruiter screen

The screen rewards culture-fit fluency. Reference the "Freedom and Responsibility" memo and have a specific Netflix area of interest.

### Q1.1: "Why Netflix?"
**Answer:** "Netflix is the only company streaming at true internet scale — 250M+ users, about 15% of global bandwidth, and a culture that prizes senior judgment over process. I want to work somewhere with high ownership and real consequences."
**Tip:** Reference the "Freedom and Responsibility" culture memo and the tech blog.

### Q1.2: "What about streaming interests you?"
**Answer:** "The combination of real-time delivery at scale, recommendation/ML systems, and the chaos engineering culture is unique. I want to work on the most-watched video pipeline in the world."
**Tip:** Have a specific area of interest (Open Connect CDN, personalization, payment, etc.).

## Stage 2: Technical phone screen

The phone is a thread-safe rate limiter and a video-recommendation feed design. They expect production-scale thinking.

### Q2.1: Implement a thread-safe rate limiter.
**Answer:** Token bucket with atomic counter; per-IP/per-user key. Discuss distributed variants with Redis.
**Tip:** They use this in production.

### Q2.2: How would you design a video recommendation feed?
**Answer:** Candidate generation (ALS, two-tower, embeddings) → ranking (deep model with hundreds of features) → re-ranking (diversity, freshness, business rules) → A/B test. Cite Netflix's published research.
**Tip:** This is the ML/SWE crossover; they expect depth.

## Stage 3: Onsite

Five rounds: merge-k-sorted-lists, top-K-frequent-items, video streaming pipeline, real-time event pipeline for 1B events/day, and a high-judgment behavioral.

### Round 3.1: Coding
**Q:** Merge k sorted lists.
**Answer:** Heap-based; O(N log k).

### Round 3.2: Coding
**Q:** Design a function to find the top K frequent items in a stream.
**Answer:** Counter + min-heap of size K, O(n log k); or Count-Min Sketch + heap for true streaming.

### Round 3.3: System design
**Q:** Design Netflix's video streaming pipeline.
**Answer:** Ingest → transcode (multi-bitrate ladder) → CDN (Open Connect) → client player with adaptive bitrate (ABR). Discuss codec choice (AV1/HEVC), ABR algorithms, manifest, DRM, edge cache, eviction.

### Round 3.4: System design
**Q:** Design a real-time event pipeline for 1B events/day.
**Answer:** Kafka → Flink → Cassandra (key) + S3 (archive) + Druid (analytics). Discuss backpressure, exactly-once, schema evolution.

### Round 3.5: Behavioral (cultural)
**Q:** Tell me about a time you disagreed with your manager.
**Answer:** STAR: high-judgment answer. Netflix values "rare valuable" behavior.
**Tip:** They explicitly screen for high-judgment + self-awareness.

## Stage 4: Hiring committee
Panel of 4-5 staff+ engineers + senior leadership. They look for: (1) senior-level judgment, (2) Netflix culture fit (freedom + responsibility), (3) technical depth.

## Stage 5: Offer
Top of market. Base $300K-$500K, RSUs $300K-$800K+ for senior+. They negotiate hard but pay well.

## Tips for the Netflix loop

Most candidates under-prep behavioral for senior-level judgment. Netflix screens explicitly — practice "tell me about an unpopular decision."
- Read the Netflix Tech Blog — they publish deep essays.
- Study the Open Connect CDN and ABR algorithms.
- Practice behavioral answers for "high-judgment" questions.
- Memorize classic system design patterns.
- Show you've thought about what "freedom and responsibility" means.
- Be ready to discuss trade-offs, not just solutions.

## Real candidate report
> "5 rounds over 2 days. Coding was 2 mediums, system design was video streaming (ABR, CDN), and behavioral was culture-fit. They explicitly asked 'tell me about a time you had to do something unpopular.' Offer $450K base + $700K RSUs for senior." — Levels.fyi, Senior SWE, 2025

## Sources
- [Netflix careers](https://jobs.netflix.com)
- [Netflix Tech Blog](https://netflixtechblog.com)
- [Levels.fyi — Netflix](https://www.levels.fyi/companies/netflix)
- [Glassdoor — Netflix interviews](https://www.glassdoor.com/Interview/Netflix-Interview-Questions-E11891.htm)
- [Reddit r/cscareerquestions — Netflix thread](https://reddit.com/r/cscareerquestions)

---

## The 1 thing to remember

Netflix is senior judgment over process — every behavioral answer must demonstrate "rare valuable" behavior, and the system design must show trade-off fluency, not just a solution.