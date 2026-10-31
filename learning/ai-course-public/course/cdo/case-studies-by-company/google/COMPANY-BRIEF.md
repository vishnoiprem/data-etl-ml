# Google (Alphabet) — Interview Signal Brief

> **Use this as the anchor** for the 8 case studies in this folder. Every case study uses the unit economics, BU names, data/AI moves, and loop dynamics from this brief. Read it first.

## 1. Real unit economics (FY2024, Alphabet 10-K)

| Metric | Value | Source |
|---|---|---|
| Total revenue | $350.0B (+14% YoY) | Alphabet Q4'24 release |
| Operating income | $112.4B (~32% margin) | Alphabet Q4'24 release |
| Headcount | 183,323 (Dec 31, 2024) | Alphabet 10-K |
| Capex | $52.5B (FY24, "majority AI infra") | Q4'24 release |
| 2025 capex guide | ~$75B (raised) | Fortune Feb 2026 |
| Google Services Q4'24 | $84.1B (+10% YoY) | Q4'24 release |
| Google Cloud Q4'24 | $11.96B (+30% YoY, "led by GCP") | Q4'24 release |
| YouTube ads Q4'24 | $10.47B | Q4'24 release |

## 2. Org structure (what matters for a Head-of-Data candidate)

- **BUs:** Google Services (Search, Ads, YouTube, Android, Chrome, Pixel, Subs), Google Cloud (GCP, Workspace, Vertex AI, BigQuery), Google DeepMind (Gemini, research), Other Bets (Waymo, Verily, Wing, Intrinsic).
- **Knowledge & Information** (Search + Ads): Prabhakar Raghavan → Pichai.
- **Google Cloud:** Thomas Kurian (CEO), Amin Vahdat (CTO AI Infra), Karthik Narain (CPO).
- **Google DeepMind:** Demis Hassabis (CEO), Jeff Dean (Chief Scientist).
- **No formal enterprise CDO.** Data leadership is distributed: Raghavan (Search data), DeepMind (model data), Cloud Data/Analytics under Kurian. Interview framing: federated, not single CDO mandate.

## 3. Real data/AI moves (last 12 months)

- **Gemini cadence:** 1.0 (Dec 2023) → 1.5 (Feb 2024) → 2.0 (Dec 2024) → 2.5 Pro/Flash (2025).
- **BigQuery + Vertex AI** sold as unified "data-to-AI." BigQuery ML + Gemini in BigQuery = Cloud Next 2025 marquee pitch.
- **AI Overviews** serving billions of queries (Q4'24 call). Performance Max + AI-driven Search ads cited as revenue accelerators.
- **$75B 2025 capex** explicitly AI infra. "AI demand outstripping supply" (Fortune).

## 4. Director / Head-of-Data loop

- **Rounds:** 5-7. Recruiter → Hiring Manager → 2-3 technical/system design → cross-functional → **Bar Raiser** → exec/comp.
- **Bar Raiser = trained, neutral, structural veto.** Scores (a) role-relevant leadership behaviors, (b) "would this person raise the average of the team 12 months in?"
- **Values:** Googleyness, humility, role-related knowledge, general cognitive ability, leadership. (Legacy reWork — site de-emphasized.)
- **Common Director themes (publicly reported):** "Design a metrics platform for YouTube creators," "How would you reduce training data cost 10x for Gemini-class models," "Build a feature store serving Search and Ads," "Migrate Ads reporting from internal Borg-system to BigQuery."

## 5. What trips non-Google candidates

- **Scale expectation.** Petabyte→exabyte. Borg, Colossus, Spanner. Frameworks designed at "billion users, trillion events." Show you've operated one order-of-magnitude below, then articulate the jump.
- **10² (10x) thinking.** Pichai's stated framing — incremental wins are below bar. Anchor every answer on order-of-magnitude leverage.
- **No-surprises culture / data-rigour.** State the metric, the source, the confidence interval, the counterfactual. Off-the-cuff opinions penalized.
- **Two-way door / one-way door** framing. Show you can classify reversibility.

## 6. The 8 case-study prompts (in this folder)

| # | Title | Mapping |
|---|---|---|
| CS-01 | The 3-min pitch to the Knowledge & Information SVP | Original CS-01 (CISO pitch), retargeted to Google's K&I org |
| CS-02 | 3-year Head-of-Data strategy across Search, Cloud, DeepMind | Original CS-02, retargeted to Alphabet's federated model |
| CS-03 | $50M Cloud Data & AI budget allocation | Original CS-03, scaled to Google's Cloud segment economics |
| CS-04 | Designing the BigQuery + Vertex AI unified data plane for Ads + Search | Original CS-04 (10M platform), retargeted to GCP at Google scale |
| CS-05 | A bad Gemini eval result goes public during quarterly earnings | Original CS-05 (margin incident), retargeted to a model-failure scenario |
| CS-06 | Transforming a 200-person federated data org into a unified platform team | Original CS-06, retargeted to Google's federated data org |
| CS-07 | The 3-C conflict: Pichai wants 10x AI, the CFO wants capex discipline, Kurian wants Cloud margin | Original CS-07, with the Alphabet-specific cast |
| CS-08 | Should Waymo's data business be spun out? Defend the recommendation to Sundar | Original CS-08 (ambiguous), retargeted to Alphabet's "Other Bets" |

---

**Last updated:** 2026-10-16 · **Source:** Compiled from research brief; all numeric claims cite the original 10-K / 10-Q / public press.