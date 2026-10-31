# CS-02 (Google) — 3-year Head-of-Data strategy across Search, Cloud, DeepMind

> **Mapping:** Original CS-02 (3-year retailer strategy). Retargeted to Alphabet's federated model.
> **Goal:** 30 minutes. Defend a 3-year data + AI strategy to Prabhakar (K&I), Thomas Kurian (Cloud), and Demis Hassabis (DeepMind).

## The brief

You are the new Head of Data for a federated Alphabet. The 3 leaders can't agree on a single CDO mandate — and you're pitching across all 3. Defend the 3-year plan.

**State of the company today:**
- 3 separate data planes: K&I (Search/Ads/YouTube), Cloud (GCP/BigQuery/Vertex), DeepMind (training data, evaluation)
- `[NEED SOURCE: scale of each plane — events/day, queries/day, training tokens]`
- AI Overviews in production. Performance Max in production. Gemini 2.5 in production. Bedrock-style managed models in production.
- $75B 2025 capex, "majority AI infra." The CFO wants ROI.

**Your task:** Build a 3-year strategy. Year by year. Defend in 30 minutes to the 3 leaders. They will challenge every choice.

## The structure (30 min)

| Section | Time | What to say |
|---|---|---|
| Diagnosis | 5 min | The state of the 3 data planes, in each leader's language |
| Strategy | 5 min | The 3-year theme, year by year |
| Roadmap | 5 min | Year 1 in detail, years 2-3 directional |
| Investment | 5 min | Capex / opex split, what you stop doing |
| 90-day plan | 5 min | What you do in the first 90 days |
| Q&A | 5 min | Defend every choice |

## The scoring rubric (per the original CS-02)

| Competency | Weight | What "great" looks like |
|---|---|---|
| Strategic and business thinking | 25% | Each leader nods at the diagnosis in their language |
| Leadership and executive influence | 20% | All 3 leaders sign off |
| Technical judgment and architecture | 20% | The 3 data planes have a story; the AI mandate has a path |
| Commercial and financial understanding | 15% | The capex is named; the ROI is named; the "stop doing" is named |
| Communication and structure | 10% | 30 minutes, no overrun |
| Ownership and measurable impact | 10% | Year 1 has 3-5 measurable outcomes |

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (5 min).**
- K&I: data plane fragmented across `[N]` internal systems [CONFIRM]. The cost is duplication; the opportunity cost is AI velocity.
- Cloud: BigQuery + Vertex AI is the public face, but the internal data plane for Cloud's own analytics is `[CONFIRM: separate, older]`.
- DeepMind: training data is best-in-class; evaluation data is the bottleneck. The 18-month "almost AI" pattern is `[CONFIRM: how many near-misses]`.
- The diagnosis is not "we need AI." The diagnosis is "we need the data plane that makes AI investable across all 3 planes."

**Strategy (5 min).**
- **Year 1: Foundations.** One platform, federated ownership. Contracts on top 5 cross-plane source systems. Semantic layer MVP. 1 cross-plane AI in production (suggest: AI Overviews eval harness, or Ads + Search shared feature store).
- **Year 2: Scale.** All 3 planes on the platform. 5 cross-plane AI in production. `[CONFIRM: what 5 — AI Overviews expansion, Performance Max optimization, Gemini serving infra, Cloud AI workloads, YouTube creator analytics]`.
- **Year 3: Differentiation.** Externalized data products for Cloud customers. Agentic AI in production. The data plane becomes a Cloud revenue line.

**Roadmap (5 min).** Y1 in detail. Y2-Y3 directional. Per Day 9 shape.

**Investment (5 min).**
- Capex: $XM/year incremental (over the $75B base) [CONFIRM]
- Opex: 200-person federated team
- Stop doing: `[CONFIRM: 3-5 named internal systems / projects]`

**90-day plan (5 min).**
- Days 1-30: 1:1 with each leader, federated stakeholder map
- Days 31-60: contracts on top 3 cross-plane sources; semantic layer MVP
- Days 61-90: 1 cross-plane AI in production with named revenue impact

**Q&A — be ready for:**
- "Why federated and not a single team?" — Per Opinion 1.
- "Why is K&I data the Y1 priority?" — Gemini 2.5, AI Overviews, Performance Max. The K&I plane drives the revenue.
- "What if Kurian wants this under Cloud?" — Joint ownership. The data plane is shared; Cloud owns the public-facing product layer.

## Watch for when you re-listen

- **Did you name each leader's data plane in their language?** If you said "the data platform" you lost Prabhakar. If you said "BigQuery" you lost Demis.
- **Did you name the stop-doing list?** A 3-year plan without cuts is a wish.
- **Did you defend the federated shape?** Per Opinion 1, federation is the Y3 destination; hub-and-spoke is Y1.
- **Did you end on time?** If you run over, the leaders conclude you can't prioritize.

---

**Source:** Adapted from original CS-02 + Google case-study brief.