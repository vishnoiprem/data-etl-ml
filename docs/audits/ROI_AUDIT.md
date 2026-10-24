# ROI audit — top-level projects by income potential

**Scope**: All 23 top-level directories. **Lens**: income potential ($$$) only — sell-as-service, freelance/consulting lead, content-for-credibility. **Date**: 2026-10-13.

**Scoring (1–5, where 5 = real money this quarter):**
- **$/qtr** — realistic income this quarter if the project is operated as intended
- **$/yr** — realistic income this year (12-month run-rate after one quarter of hardening)
- **Effort** — 1 = turn-the-key, 5 = rebuild the surface
- **Verdict** — one of: `KEEP`, `DEPLOY`, `HARVEST`, `POLISH-OR-PARK`, `ARCHIVE`

**Honest disclaimer**: $/qtr and $/yr are *my best guess from the codebase alone*. The real number depends on your time, your existing pipeline, and the market you're selling into. Where the signal is weak, I've said so.

---

## Tier 1 — already income-active, run them

### `leads-pipeline/` — VERDICT: `KEEP` — Score 4/5

This is the only project in the repo that's already producing billable value. It runs daily, has a working autopilot, and the lead-drop is auditable. The 2026-10-10/ batch has 27 verified leads; the cadence (6 emails + 5 DMs + 2 APAC + 5 platform = 18 touchpoints/day) is documented.

| Axis | Score | Note |
|---|---|---|
| $/qtr | **4** | $20–60K/mo gross is the user's own projection in `README.md`; 1–3 contracts/30d at $40–150/hr × bench of 6–20 |
| $/yr | **5** | If the cadence holds, 12–36 contracts/yr is plausible; the bottleneck is close-rate, not pipeline volume |
| Effort | **1** | Already running; just keep the cron green and the leads fresh |
| Risks | 3 real ones | (1) WebFetch-blocked sources (Braintrust/Arc/Lemon/Turing/Glints/JobStreet) cap the pipeline at 27/day, (2) DM-open verification on X is manual, (3) no reply/thread tracking — you don't know which templates actually close |

**30-day next step**: add a `status/` reply-tracking column (`replied?`, `replied_at`, `channel`, `meeting_booked?`) so the next 30 days answer "which template converts," not "how many went out."

---

### `realtime-stock-pipeline/trade-finder/` — VERDICT: `DEPLOY` — Score 3/5

Real product: stress-test runner + supplier verifier + 8-vendor shortlist for the SG→UK fitness-band opportunity. The pipeline is complete (find → stress-test → verify → outreach). What it lacks is a real money stream — today it's a paper-trade opportunity, not a revenue line.

| Axis | Score | Note |
|---|---|---|
| $/qtr | **2** | One sourcing deal in flight; if it closes, $X K one-shot. Not recurring. |
| $/yr | **3** | 2–4 sourced-and-sold deals/yr at 25–40% margin on a 4–8K unit order is plausible |
| Effort | **2** | The pipeline runs; what's missing is the *order*: a PO + a freight forwarder + a UK customs broker. Three outside parties, not code. |
| Risks | 4 real ones | (1) No contract with any supplier yet, (2) the 8-vendor shortlist is desk-research, not RFQ'd, (3) no UK VAT/EORI setup mentioned, (4) freight cost variance is the silent margin killer |

**30-day next step**: send the 3 outreach emails (`business-plan/02_supplier_outreach_emails.txt`) to the top 3 vendors in the shortlist, request samples + FOB quotes, and write the per-vendor cost matrix to a CSV that the financial model can consume. The first real data point (sample cost + lead time) collapses 3 of the 4 risks.

---

### `trading-bot/` — VERDICT: `KEEP` — Score 2/5 (caveat: this is paper money, not income)

| Axis | Score | Note |
|---|---|---|
| $/qtr | **1** | Paper-trading only. The README is explicit. Until it's on real money, it's a tool, not an income line. |
| $/yr | **2** | If/when promoted to live, a $5K → $6K signal-edge on a single name over a quarter is plausible. Don't bet on it. |
| Effort | **1** | The smoke test is green; just keep it |
| Risks | High | Markets can lose money. The README says so. Treat it as a research rig. |

**30-day next step**: track paper-trade win-rate over 90 days, and only consider real-money if the 90-day Sharpe on a single name is > 0.5. Until then, the ROI is "I understand my own pipeline," not dollars.

---

## Tier 2 — portfolio credibility, indirectly converts to income

These projects won't make you money directly. But they are the *proof* that closes freelance / consulting / staff-aug deals. ROI is "faster close on the next client," not "this line item in the invoice."

### `ai-engineering/` (40 leaf projects) — VERDICT: `POLISH-OR-PARK` — Score 3/5 (as a portfolio)

- **30+ numbered projects** in the `01..40` range, each at "world-class README" standard after this session's lift. 211 Python files, 53 READMEs.
- **What it can do for income**: every project here is a *demo-able artifact* for a client interview. The lattice of cross-links (now in every README's "Related directories" section) reads as "I understand the whole ML platform, not one corner."
- **Realistic conversion**: a 30-minute "show me what you've built" walk-through is a $5K–$20K staffing-aug close (one contract, one client). The repo is the artifact that makes the close possible.
- **The weak spots**: 99% of these are *toys*. None of them has paying users. That's fine for a portfolio — but if you pitch them as "a product I can deploy for you," the client will ask about uptime and you'll lose the deal.

**30-day next step**: pick the **one** project in `ai-engineering/` that you could demo cold to a non-technical client and have them say "yes, build that for us." The candidates are `20-cog-style-inference-api`, `24-vertex-style-platform`, `38-multi-tenant-inference`, and `40-ai-side-hustle`. The latter is the most directly sellable; read it, decide, and pin the repo's GitHub About to that one project.

---

### `data-engineering/` (incl. Banking-AML, keystone-iceberg, cqrs-ledger, etc.) — VERDICT: `POLISH-OR-PARK` — Score 3/5

- 58 Python files, 1 SQL, 20 READMEs. The leaf projects are real architectural patterns (event-sourced-audit, multi-tenant-isolation, ontology-data-fabric, financial-reporting-platform) — all are the kind of work banks and consultancies pay $80–150/hr for.
- **Realistic conversion**: Banking-AML specifically is *exactly* the niche you sell into with the Vietnam LLC + the AI/data profile. If a single BAA / audit / compliance client sees that subtree and the supporting READMEs, that's a $20–60K engagement.
- **The weak spots**: the AML subtree lives inside a `.claude/worktrees/` submodule (uncommitted churn visible in `git status`), and several of the leaf projects have a `data-engineering/` *inside* `data-engineering/` (the `clp_projects`, `data-engineering`, `data-enginnering-cloudvala` are likely duplicated/legacy). That's a credibility hit for a banking client who notices.

**30-day next step**: clean up the `data-engineering/` directory: (1) drop or merge the three near-duplicate inner `data-engineering*` subdirs, (2) flatten the `.claude/worktrees/` noise, (3) write a single top-level `data-engineering/README.md` that walks a bank-audit client through Banking-AML → event-sourced-audit → financial-reporting-platform in 3 links. The conversion is: client sees the curated path, books a call.

---

### `agentic-ai/` (17 leaf projects) — VERDICT: `POLISH-OR-PARK` — Score 2/5

- 35 Python files, 21 READMEs. Includes the security-warning project `5-amazon-transcribe/` (the hardcoded `AKIA...` access key in `app.py` / `Amazon_Polly.py` is documented but **still in the source** — that's a real exposure if you ever deploy it).
- **Realistic conversion**: agent projects sell to AI-curious clients, but the saturation is high. The differentiator is the *MCP + A2A + LangGraph* density in this subtree — that's research-level credibility.
- **The weak spots**: the `5-amazon-transcribe/` project needs the hardcoded keys rotated and replaced with `os.environ`/IAM-role lookup before any client sees the URL.

**30-day next step**: rotate the AWS keys in `5-amazon-transcribe/`, then re-run the smoke. The README is already world-class; the only thing between this and "demo-able" is the key rotation.

---

### `ml/` (deep-learning-specialization, GenAI-Pinnacle, multi-agent, etc.) — VERDICT: `POLISH-OR-PARK` — Score 2/5

- 143 Python files, 20 notebooks, 4 READMEs. Heavy on notebooks (course material); light on production code.
- **Realistic conversion**: a portfolio reviewer sees "this person did Andrew Ng's deep-learning specialization and can use it on real data." That's a hiring signal, not a service signal. Useful for staff roles; not for closing freelance work.

**30-day next step**: none high-priority. Pin 1–2 production-grade ML builds in the GitHub About (e.g. `ml/ai-agent/AdvancedAgenticSystem/` is now a 130-line README; that's your best ML credit). Let the rest be evidence of range.

---

### `Spark/`, `Python/`, `flink-cdc-dashboard/`, `postgres_cdc_kafka/`, `golang/` — VERDICT: `POLISH-OR-PARK` — Score 2/5 (each)

These are interview-prep + reference builds. They're credible in a system-design conversation, but they don't ship product. Keep them clean; don't expect them to make money.

**30-day next step**: nothing. The 6-step `flink-cdc-dashboard/` README is genuinely good — if you ever need a "show me CDC" demo, that's the one. The `golang/order-etl-pipeline/` is the only Go in the repo, which is a differentiator for some clients.

---

## Tier 3 — course content, tooling, and noise

These do not produce income. They are inputs to *other* things that may produce income.

### `ai-course-public/`, `pincel-ai-program/`, `ml/notebooks/` — VERDICT: `ARCHIVE` (cold)

- 6 + 0 + 20 Python files, mostly notebooks. The `pincel-ai-program/` is a "Computer Vision using PyTorch" course. `ai-course-public/` is your own course material (phase-6-interview-prep + intro-to-ai-agents companion courses).
- **Income signal**: zero directly. The *interview-prep* portion has monetization potential if you ever turn it into a paid cohort — but that's a separate product.

**30-day next step**: don't touch. These are inputs to your *own* learning, not products. Keep them; don't expect them to make money.

---

### `sam-installation/` — VERDICT: `ARCHIVE`

- Vendored AWS SAM CLI source + dist tree. Useful for a known-good install, not a product.
- **30-day next step**: nothing. If you ever need `sam`, the install script is here.

---

### `Resume/`, `Senior Delivery Consultant - Data Engineering/` — VERDICT: `POLISH-OR-PARK` (these are *you*, not projects)

- A PDF + docx resume, plus interview research for the AWS ProServe Senior Delivery Consultant role.
- **Income signal**: this is the single highest-ROI *file* in the entire repo. The ProServe role is a $150–250K base + bonus; the interview-research doc is the difference between an offer and a no.

**30-day next step**: review `Senior Delivery Consultant - Data Engineering/AWS_ProServe_SeniorDeliveryConsultant_InterviewResearch_Prem.md` against your latest resume. If anything in the resume contradicts the research doc, the resume wins; update the doc.

---

### `app/`, `aws/`, `scripts/`, `docs/`, `audit-results/`, `doc/` — VERDICT: `KEEP` (enablers, no income)

- `app/` is a SAM hello-world scaffold; the value is "known-good starting point," not income.
- `aws/` is the AWS CLI bundle + a CRA placeholder; tooling, not a product.
- `scripts/` has `run_pip_audit.sh` and `repo_stats.sh` — operational glue.
- `docs/CI_CD.md` and `docs/SECURITY_AUDIT.md` are repo-level documentation.
- `audit-results/` is a severity-tier policy doc.
- `doc/` is a single Keynote file.

**Income signal**: zero directly. **Cost-avoidance signal**: `pip-audit` and the security audit doc are exactly what closes the "do you take security seriously" question from a regulated-industry client. Keep them green.

**30-day next step**: re-run `make smoke` on `leads-pipeline/` and `pip-audit` on the whole repo; if either is red, that's the leak.

---

## Summary table

| Project | $/qtr | $/yr | Effort | Verdict |
|---|---|---|---|---|
| `leads-pipeline/` | 4 | 5 | 1 | `KEEP` |
| `realtime-stock-pipeline/trade-finder/` | 2 | 3 | 2 | `DEPLOY` |
| `trading-bot/` | 1 | 2 | 1 | `KEEP` (paper) |
| `ai-engineering/` | 1 | 3 | 3 | `POLISH-OR-PARK` |
| `data-engineering/` | 1 | 3 | 3 | `POLISH-OR-PARK` |
| `agentic-ai/` | 1 | 2 | 2 | `POLISH-OR-PARK` |
| `ml/` | 0 | 1 | 4 | `POLISH-OR-PARK` |
| `Spark/`, `Python/`, `flink-cdc-dashboard/`, `postgres_cdc_kafka/`, `golang/` | 0 | 1 | 4 | `POLISH-OR-PARK` |
| `ai-course-public/`, `pincel-ai-program/`, `ml/notebooks/` | 0 | 0 | n/a | `ARCHIVE` |
| `sam-installation/` | 0 | 0 | n/a | `ARCHIVE` |
| `Resume/`, `Senior Delivery Consultant - Data Engineering/` | n/a | n/a | 1 | `POLISH` (you) |
| `app/`, `aws/`, `scripts/`, `docs/`, `audit-results/`, `doc/` | 0 | 0 | 1 | `KEEP` (enablers) |

## The 30-day plan, ranked

1. **Reply-tracking on `leads-pipeline/`** — one new column, one weekly review. Single highest-ROI change. Affects $/yr directly.
2. **First supplier RFQ on `realtime-stock-pipeline/trade-finder/`** — 3 emails, 1 shortlist, 1 cost matrix. Closes 3 of 4 risks in the audit.
3. **Rotate AWS keys in `agentic-ai/5-amazon-transcribe/`** — the hardcoded key is a real exposure, not a hypothetical. 30 minutes, removes a "this is unsafe" objection in any client demo.
4. **Pick the one `ai-engineering/` project to pin to GitHub About** — the whole subtree is too much for a client to digest; one anchor is the difference between "this person built a lot" and "this person is the one I'd hire for X."
5. **Clean `data-engineering/` directory** — drop or merge the 3 duplicate inner `data-engineering*` subdirs; flatten the worktree noise; write a 1-page curated path for the bank-audit client.
6. **Re-run `leads-ci` + `pip-audit`** — green builds are the table-stakes that close the regulated-industry client.

Everything else is portfolio polish that can wait a quarter.

---

**Last updated:** 2026-10-13  
**License:** MIT — use freely in your own courses, prototypes, and products.  
