# AI Governance For Startups — Notion Bundle

**The complete AI governance workspace for a startup, in 15 pre-built Notion databases.** Clone the workspace, customize 6 fields per database, and you have a working governance program that passes enterprise security review and survives an EU AI Act audit. No spreadsheets to build. No templates to design.

---

## What you get

**1. Model Inventory Dashboard** — The landing page. Every model in production with: name, owner, risk tier (1-4), last evaluated date, current model card status. Color-coded: green if current, red if anything is older than 90 days.

**2. Model Card Database** — One row per model, with the full Google model card template embedded as a Notion page. Fields: intended use, out-of-scope use, training data summary, eval results, known limitations, contact. Clone the template, fill in, ship.

**3. Risk Tier Database** — Every model with its EU AI Act + NIST risk tier, the rationale (why this tier), and the conformity assessment status (required for tier 3, prohibited for tier 4). Pre-populated with the risk tier definitions from the EU AI Act.

**4. Data Lineage Database** — One row per (model, dataset) pair. Fields: source, collection date, consent basis, retention period, deletion endpoint, sub-processor. The single most-failed audit item — pre-built so you don't have to invent the schema.

**5. Change Log Database** — One row per model release. Fields: version, date, what changed, who approved, test results, rollback plan. Pre-formatted to match the EU AI Act Article 12 requirements.

**6. Bias Test Log** — Quarterly bias test results. Fields: model, protected attribute, fairness metric, result, mitigation, follow-up date. Pre-built views by quarter, by model, by metric.

**7. Vendor (Sub-Processor) Database** — Every third-party AI provider you use (OpenAI, Anthropic, Hugging Face, etc.) with their SOC2 status, DPA signed date, last review. Pre-populated with the 10 most common AI vendors.

**8. Friday Governance Review** — Templated page with the 8-item weekly checklist. Duplicate every Friday, walk through, check. The auditor can pull 52 weeks of these in 5 minutes.

**9. Incident Log** — Every AI-related incident and near-miss. Date, model, type (bias, hallucination, jailbreak, data leak), severity, mitigation, post-mortem. Required for tier 3; good practice for everything.

**10. Conformity Assessment Templates** — The 30-page conformity assessment template for tier 3 models. Pre-structured per EU AI Act Annex IV. You fill in the model-specific details; the format is done.

**11. Customer-Facing AI Disclosure Database** — Every model that touches customers, with the disclosure language you're using ("AI-powered," "AI-generated," etc.) and the location (UI tooltip, terms of service, marketing page). Required for tier 2 transparency obligations.

**12. Quarterly Access Review** — Templated page for the 90-minute quarterly review. Lists every employee, every model they have access to, every API key they own. Pre-formatted to revoke dormant access.

**13. Bias Audit Calendar** — Shows when each tier 2+ model is due for its next bias test, who owns it, and the test framework (Fairlearn, Aequitas, or custom). Auto-flags any model more than 90 days past due.

**14. EU AI Act Compliance Tracker** — Per-article checklist of every EU AI Act obligation that applies to your products. Pre-mapped to the risk tiers. Auditor can pull this and immediately see your coverage.

**15. Enterprise Security Questionnaire Answer Bank** — 40 of the most common enterprise AI security questions with the answer an enterprise CISO expects to hear. The questions you can't answer are the gaps in your program.

---

## How to use it

**Day 1 (1 hour):** Duplicate the template workspace into your Notion. You'll have 15 empty databases. The structure is pre-built — you just need to add data.

**Week 1 (4-6 hours):** Inventory all your models. Fill in the Model Card Database. Risk-tier everything in the Risk Tier Database. The inventory is the foundation; the documents follow.

**Week 2-3:** Fill in Data Lineage. Fill in Vendor database. Connect the Change Log to your GitHub releases via Zapier (template included). Run your first Friday review.

**Week 4:** Open the EU AI Act Compliance Tracker. For each article that applies, link the database (model card, change log, etc.) that satisfies it. Run your first internal audit using the Customer-Facing Disclosure database and the Bias Audit Calendar.

**Day 30:** You have a working AI governance program. The next enterprise security review takes you an afternoon instead of a sprint.

---

## What's NOT included

- **The actual model cards.** The template structure is here; the model-specific content is yours to write. Use the playbook (`The AI Governance For Startups Playbook`) for guidance on what to put in each section.
- **The bias test code.** The Bias Test Log is the database where results go. The Python/R scripts to run Fairlearn or Aequitas are separate. The playbook links to both.
- **The legal review.** Tier 3 conformity assessments need a lawyer's sign-off in some jurisdictions. This is the format, not the legal advice.
- **The customer-facing language review.** Your disclosure text should be reviewed by your lawyer for the specific jurisdictions you operate in.

---

## Why a Notion bundle, not a PDF

A PDF of "here are the 4 documents you need" is what every consultant sells. You print it, file it, never look at it again. A Notion workspace is something you actually use — every Friday for the review, every release for the change log, every quarter for the bias audit. The audit becomes a 30-minute export instead of a 3-week panic.

The governance programs that survive 12 months are the ones that live where the work lives. Notion is where you already do everything else. Put governance there too.
