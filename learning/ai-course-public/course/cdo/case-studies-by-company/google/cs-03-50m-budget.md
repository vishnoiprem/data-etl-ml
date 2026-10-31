# CS-03 (Google) — $50M Cloud Data & AI budget allocation

> **Mapping:** Original CS-03 ($5M retailer budget). Scaled to Cloud segment economics.
> **Goal:** 30 minutes. Allocate $50M/year for Cloud Data & AI. Defend in front of the Cloud CFO + the Cloud CPO + Thomas Kurian.

## The brief

You are the new Head of Data for Google Cloud. The Cloud segment is +30% YoY ($11.96B in Q4'24). The Cloud CFO has approved $50M/year incremental for Data & AI. The CPO wants features. Kurian wants margin. The board wants AI.

**State of the Cloud data plane today:**
- BigQuery + Vertex AI = marquee product
- `[NEED SOURCE: Cloud Data org size — embedded analysts? Central team?]` [CONFIRM]
- `[NEED SOURCE: Cloud AI features shipped in 2024]`
- `[NEED SOURCE: BigQuery ML adoption, Gemini in BigQuery adoption]`

**Your task:** Allocate $50M. Justify every $5M. Name the ROI. Name the cuts. Measure the 12-month outcomes. Defend in 30 minutes.

## The structure (30 min)

| Section | Time | What to say |
|---|---|---|
| Diagnosis | 5 min | The state of the Cloud data plane, in Cloud's language |
| Portfolio | 10 min | The 7 funded bets, line by line |
| ROI | 5 min | Total return, payback |
| Cuts | 5 min | The 13 items cut, with reason |
| Measurement | 5 min | The 12-month outcome metrics |

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (5 min).**
- BigQuery is the data plane. Vertex AI is the AI plane. The seam is the bottleneck — most customers hit it in their first 90 days.
- `[CONFIRM: BigQuery ML adoption %, Gemini in BigQuery DAUs]`
- The diagnosis: the Cloud data plane is technically best-in-class; the customer experience at the seam is the ceiling on growth.

**Portfolio (10 min):**

| $M | Bet | Owner | ROI (12-month) |
|---|---|---|---|
| 5 | BigQuery ML + Gemini eval harness | CPO + Data | +20% ML adoption, +X% [CONFIRM] |
| 8 | Cross-cloud feature store (Cloud customers) | CPO + Data | $XM revenue, +X% attach [CONFIRM] |
| 5 | Vertex AI + BigQuery unified observability | Platform | -X% support tickets, +NPS [CONFIRM] |
| 7 | Data clean rooms for enterprise customers | CPO + Sales | $XM new logos [CONFIRM] |
| 5 | AI customer support for BigQuery + Vertex | Support | -X% handling time, +NPS [CONFIRM] |
| 10 | RAG + agent platform for Cloud customers | CPO + Data | $XM revenue, +X% attach [CONFIRM] |
| 5 | FinOps + data contracts (the foundation) | Data | Enabler for all above |
| 5 | Stop doing: `[CONFIRM: 3-5 named Cloud initiatives]` | | |
| 50 | Total | | $XM run-rate, payback [CONFIRM] |

**ROI (5 min).** Total run-rate: $XM. Payback: `[CONFIRM: 12-18 months]`. Risk-adjusted at 60%: $XM.

**Cuts (5 min).** Per Opinion 3 — the AI portfolio is 80% traditional ML, 20% GenAI. Cloud is the public face of Google's AI; the pressure is to over-invest in GenAI. Don't. The CFO will respect the discipline.

**Measurement (5 min).** Monthly: BigQuery ML adoption, Gemini in BigQuery DAUs, BigQuery support ticket trend, Net Revenue Retention on Cloud data customers. Quarterly: business case review with Kurian. Annual: portfolio review with the board.

**Q&A — be ready for:**
- "Why not all-Gemini?" — Per Opinion 3. The 80/20 bet.
- "Why is foundations $5M?" — Without it, everything else fails.
- "What if BigQuery adoption is already at ceiling?" — Then the bet shifts to Vertex AI attach; the contracts still pay back.

## Watch for when you re-listen

- **Did you name every $5M with an owner?** If not, the CFO concludes the budget is a wish list.
- **Did you name the cuts?** A budget without cuts is over-commit.
- **Did you defend the ROI with a baseline?** If you can't say "today is $X, target is $Y," you have no business case.
- **Did you end on time?** The CFO buys precision; running over signals you can't prioritize.

---

**Source:** Adapted from original CS-03 + Google case-study brief.