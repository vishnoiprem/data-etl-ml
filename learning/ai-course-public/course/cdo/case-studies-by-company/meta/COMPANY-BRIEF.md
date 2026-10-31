# Meta — Interview Signal Brief

> **Use this as the anchor** for the 8 case studies in this folder. Every case uses the unit economics, BU names, data/AI moves, and loop dynamics below.

## 1. Real unit economics (Q3 2025 + FY2025)

| Metric | Value | Source |
|---|---|---|
| Q3 2025 revenue | $51.24B (+26% YoY) | Q3 2025 PR |
| FY2024 revenue | $164.5B | Q4 2024 PR |
| FY2025 revenue | $200.97B (+22% YoY) | Q4 2025 PR |
| Ad revenue FY2025 | $196.18B | Q4 2025 PR |
| Q3 2025 op margin | 40% (Family of Apps $24.97B; Reality Labs –$4.43B) | Q3 2025 PR |
| Q3 2025 capex | $19.37B | Q3 2025 PR |
| FY2025 capex guide | $70-72B (raised from $66-72B) | Q3 2025 PR |
| 2026 capex growth | "notably larger" than 2025 | Q3 2025 PR |
| Headcount (Sep 2025) | 78,450 (+8% YoY) | Q3 2025 PR |
| DAP (Sep 2025) | 3.54B (Family of Apps) | Q3 2025 PR |
| 2026 RIF | ~8,000 jobs (~10%) + 6,000 reqs closed (May 2026) | NYT Apr 2026; Reuters |

## 2. Org structure (what matters for Director of Data)

- **Chief Data Officer (NEW):** **Alex Schultz** — named Meta's *first* CDO in **July 2026** (moved from CMO). Mandate: "global AI analytics." 19-year Meta vet.
- **Chief AI Officer:** **Alexandr Wang** (joined June 2025 from Scale AI). Leads **Meta Superintelligence Labs (MSL)**, formed June 30, 2025.
- **BUs:** Family of Apps (Facebook, Instagram, Messenger, WhatsApp, Threads) + Reality Labs + MSL.
- **2025 leadership churn:** Wang (CAIO), Shengjia Zhao (chief AI scientist), Schultz (CDO); Naomi Gleit elevated to "Head of Product."

## 3. Real data/AI moves (last 12 months)

- **Llama 4** released April 2025; cadence slower than Llama 3.
- **Andromeda** (ad retrieval) + **GEM** (Generative Ads Recommendation Model, ranking) — both live in production by Q2 2025.
- **Meta AI** in WhatsApp/IG/FB/Messenger; WhatsApp highest engagement outside US.
- **$70-72B 2025 capex** for AI infra.

## 4. Director (IC6 / M6) loop

- ~6-8 weeks, 5-7 rounds virtual:
  1. Recruiter screen (30 min)
  2. Technical screen: SQL + coding (60 min)
  3. **Data modeling** (60 min) — schema design, ERDs, scale-out
  4. **Architecture / system design** (60 min) — Director-only; pipelines at petabyte scale
  5. **ML system design** (60 min) — feature stores, ranking, online/offline, experimentation
  6. **Product sense / analytics** (60 min) — metric design, A/B, causal
  7. **Leadership & behavioral** (60 min) — ownership, cross-org, "10x" stories
  8. **Hiring manager + skip-level**
- **Values tested:** Move Fast, Be Bold, Be Open, Focus on Long-Term Impact, Build Awesome Things.
- **Common prompts:** "Design a metrics platform for IG Reels," "Design an experimentation system for ad ranking," "Reduce p99 latency of Home Feed ranking by 30%."

## 5. What trips non-Meta candidates

- **Scale shock:** Family DAP 3.54B. Designs that "work" at 100M users die here.
- **Ship bias:** "What did you *build* and *ship*?" not "what did you analyze?"
- **Opinionated:** Pick a side in design debates; defend with data. "It depends" reads as weak.
- **10x framing:** Every Director answer should imply 10x scale or step-function.
- **Cross-org:** Data orgs at Meta are embedded in product pods; expect "influence without authority" stories.

## 6. The 8 case-study prompts (in this folder)

| # | Title | Mapping |
|---|---|---|
| CS-01 | The 3-min pitch to Alex Schultz on the new CDO mandate | Original CS-01, retargeted to Meta's first-ever CDO |
| CS-02 | 3-year Director of Data strategy across Family of Apps + Reality Labs + MSL | Original CS-02, scaled to Meta's federated product orgs |
| CS-03 | $30M Director-of-Data budget across FB / IG / WhatsApp / Threads | Original CS-03, scaled to Meta's BU economics |
| CS-04 | Designing the Home Feed ranking data plane at 3.54B DAP | Original CS-04 (10M platform), retargeted to Meta scale |
| CS-05 | A bad Llama 4 eval result goes public during a developer event | Original CS-05 (margin incident), retargeted to model-failure |
| CS-06 | Transforming a 500-person embedded data org into a CDO-mandated platform team | Original CS-06, scaled to Meta's embedded analytics org |
| CS-07 | The 3-C conflict: Zuckerberg wants superintelligence, the CFO wants cost discipline, Schultz wants data org | Original CS-07, with Meta cast |
| CS-08 | Should Meta's Reality Labs data be spun out? Defend to Mark | Original CS-08 (ambiguous), retargeted to Reality Labs |

---

**Last updated:** 2026-10-16.