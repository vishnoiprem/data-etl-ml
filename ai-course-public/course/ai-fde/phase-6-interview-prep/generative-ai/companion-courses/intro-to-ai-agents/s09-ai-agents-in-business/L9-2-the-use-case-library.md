# L9.2: The use case library — 12 use cases across 6 verticals

> **FDE framing in one line:** AI agents work best for tasks that are repetitive, language-heavy, tool-using, and have a clear success metric. The 12 use cases in the FDE's library cover 6 verticals; each has a known ROI, a known failure mode, and a known pattern. The FDE who can name the use case + the ROI + the failure mode is the FDE who can scope the engagement in 30 minutes.

## The 3 things you'll learn

1. The 4 use case criteria: repetitive (the task happens > 100 times/day), language-heavy (the task is text or speech), tool-using (the task requires calling APIs or querying data), measurable (the success is verifiable). Each use case in the library meets all 4 criteria.
2. The 12 use cases across 6 verticals: CS (email drafting, ticket routing), sales (lead qualification, outreach), ops (report generation, anomaly detection), finance (invoice processing, expense categorization), legal (contract review, compliance checking), healthcare (clinical notes, prior auth). Each has a known ROI + a known failure mode.
3. The "use case fit" rubric: the FDE scores each potential use case on 4 axes (volume, language, tool-use, measurability) + 2 risk axes (hallucination tolerance, compliance). The score (0-6) determines if the use case is a fit.

## Concept

AI agents work best for tasks that are repetitive, language-heavy, tool-using, and have a clear success metric. **The 4 criteria are the filter; the 12 use cases in the FDE's library meet all 4.** The FDE's job is to know the library, score new use cases against the 4 criteria, and recommend the use cases that fit.

The 4 use case criteria:

1. **Repetitive.** The task happens > 100 times/day. The agent's value scales with volume; a task that happens 10 times/day is not worth automating. Example: CS email drafting (150/day at PacificFreight) is a fit; ad-hoc strategy work (1/week) is not.
2. **Language-heavy.** The task is text or speech. The agent's strength is language; tasks that don't involve language (e.g., physical manipulation, image classification without language) are not the right fit. Example: customer email drafting is a fit; physical inventory scanning is not.
3. **Tool-using.** The task requires calling APIs or querying data. The agent's superpower is tool use; tasks that don't require tools (e.g., pure Q&A) are a fit for a chatbot, not an agent. Example: lead qualification (Clearbit + HubSpot + Slack) is a fit; pure FAQ is not.
4. **Measurable.** The success is verifiable. The agent needs an eval set; tasks where success is subjective (e.g., "is this email good?") are harder to measure than tasks where success is objective (e.g., "did the lead get qualified?"). Example: invoice processing (output: structured JSON) is a fit; brand voice drafting (subjective) is harder.

The 12 use cases across 6 verticals (the FDE's library):

| # | Vertical | Use case | Volume (per day) | ROI per year | Failure mode |
|---|----------|----------|------------------|--------------|--------------|
| 1 | CS | Email drafting | 100-1000 | $50-500K | Hallucinated product info |
| 2 | CS | Ticket routing | 500-5000 | $100-1000K | Misrouted tickets |
| 3 | Sales | Lead qualification | 50-500 | $20-200K | False negatives (missed leads) |
| 4 | Sales | Outreach | 100-1000 | $30-300K | Generic / off-brand messaging |
| 5 | Ops | Report generation | 10-100 | $20-200K | Wrong data / missing context |
| 6 | Ops | Anomaly detection | 100-10K | $50-500K | False positives (alert fatigue) |
| 7 | Finance | Invoice processing | 100-10K | $100-1000K | Wrong amounts / missed fields |
| 8 | Finance | Expense categorization | 50-500 | $20-200K | Mis-categorized expenses |
| 9 | Legal | Contract review | 10-100 | $50-500K | Missed clauses / wrong analysis |
| 10 | Legal | Compliance checking | 50-500 | $50-500K | False negatives (missed violations) |
| 11 | Healthcare | Clinical notes | 100-1000 | $100-1000K | Hallucinated medical info |
| 12 | Healthcare | Prior auth | 50-500 | $50-500K | Wrong CPT codes / wrong approvals |

The "use case fit" rubric: the FDE scores each potential use case on 6 axes (4 fit axes + 2 risk axes):

1. **Volume (0-3).** 0 = <10/day (not worth); 1 = 10-100/day; 2 = 100-1000/day; 3 = >1000/day.
2. **Language-heavy (0-3).** 0 = no language; 1 = minimal; 2 = mostly language; 3 = pure language.
3. **Tool-using (0-3).** 0 = no tools; 1 = minimal; 2 = some tools; 3 = many tools.
4. **Measurable (0-3).** 0 = subjective; 1 = mostly subjective; 2 = mostly objective; 3 = objective.
5. **Hallucination tolerance (0-3, inverse).** 0 = zero tolerance (e.g., medical); 1 = low; 2 = medium; 3 = high.
6. **Compliance risk (0-3, inverse).** 0 = high (HIPAA, PCI); 1 = medium; 2 = low; 3 = none.

The score is the sum of all 6 axes. A score of 12-18 is a strong fit; 8-11 is a moderate fit; <8 is a weak fit. The FDE recommends the use cases that score 12+.

## The pattern

The 12 use cases in detail (the FDE's reference):

```python
USE_CASE_LIBRARY = {
    "cs_email_drafting": {
        "vertical": "Customer service",
        "task": "Draft replies to customer emails",
        "volume_per_day": "100-1000",
        "language_heavy": True,
        "tool_using": True,  # tracker, CRM, knowledge base
        "measurable": True,  # thumbs-up rate
        "hallucination_tolerance": "medium",  # Mei can edit
        "compliance_risk": "low",
        "fit_score": 16,
        "annual_roi_usd": "50K-500K",
        "failure_mode": "Hallucinated product info; off-brand voice",
        "guardrails": "Human-in-the-loop (Mei reviews every draft); brand voice in system prompt; product info from RAG",
        "pacific_freight_case": "150 emails/day, $0.001/draft, 80% thumbs-up, $20K/year savings",
    },
    "cs_ticket_routing": {
        "vertical": "Customer service",
        "task": "Route incoming tickets to the right team",
        "volume_per_day": "500-5000",
        "language_heavy": True,
        "tool_using": True,  # ticket system, team directory
        "measurable": True,  # did the ticket reach the right team?
        "hallucination_tolerance": "low",  # wrong routing = customer frustration
        "compliance_risk": "low",
        "fit_score": 15,
        "annual_roi_usd": "100K-1M",
        "failure_mode": "Misrouted tickets (customer waits)",
        "guardrails": "Confidence threshold; fallback to human; routing rules in the system prompt",
    },
    "sales_lead_qualification": {
        "vertical": "Sales",
        "task": "Score inbound leads and route to sales reps",
        "volume_per_day": "50-500",
        "language_heavy": True,
        "tool_using": True,  # Clearbit, HubSpot, LinkedIn
        "measurable": True,  # did the lead convert?
        "hallucination_tolerance": "low",  # false positives waste sales time
        "compliance_risk": "low",
        "fit_score": 15,
        "annual_roi_usd": "20K-200K",
        "failure_mode": "False negatives (missed leads)",
        "guardrails": "Conservative scoring; human reviews medium-score leads; weekly feedback loop",
        "northwind_case": "200 leads/day, 70% qualified, $0.001/lead, $50K/year savings",
    },
    "sales_outreach": {
        "vertical": "Sales",
        "task": "Personalize outreach emails for prospects",
        "volume_per_day": "100-1000",
        "language_heavy": True,
        "tool_using": True,  # LinkedIn, CRM, email
        "measurable": True,  # open rate, reply rate
        "hallucination_tolerance": "low",  # off-brand = spam
        "compliance_risk": "medium",  # CAN-SPAM, GDPR
        "fit_score": 13,
        "annual_roi_usd": "30K-300K",
        "failure_mode": "Generic / off-brand messaging",
        "guardrails": "Brand voice template; prospect data from CRM; human review for high-value prospects",
    },
    "ops_report_generation": {
        "vertical": "Operations",
        "task": "Generate daily/weekly reports from data",
        "volume_per_day": "10-100",
        "language_heavy": True,
        "tool_using": True,  # database, BI tool
        "measurable": True,  # report accuracy
        "hallucination_tolerance": "low",  # wrong data = bad decisions
        "compliance_risk": "low",
        "fit_score": 14,
        "annual_roi_usd": "20K-200K",
        "failure_mode": "Wrong data / missing context",
        "guardrails": "Data from queries (not generated); human review of every report; template in the system prompt",
    },
    "ops_anomaly_detection": {
        "vertical": "Operations",
        "task": "Detect anomalies in metrics (revenue drop, traffic spike)",
        "volume_per_day": "100-10K",
        "language_heavy": True,
        "tool_using": True,  # database, alerting
        "measurable": True,  # was the anomaly real?
        "hallucination_tolerance": "low",  # false positives = alert fatigue
        "compliance_risk": "low",
        "fit_score": 14,
        "annual_roi_usd": "50K-500K",
        "failure_mode": "False positives (alert fatigue)",
        "guardrails": "Confidence threshold; alert only on high-confidence anomalies; human review of medium-confidence",
    },
    "finance_invoice_processing": {
        "vertical": "Finance",
        "task": "Extract data from invoices (PDF → structured JSON)",
        "volume_per_day": "100-10K",
        "language_heavy": True,
        "tool_using": True,  # OCR, ERP
        "measurable": True,  # field accuracy
        "hallucination_tolerance": "zero",  # wrong amount = wrong payment
        "compliance_risk": "high",  # SOX, audit
        "fit_score": 13,
        "annual_roi_usd": "100K-1M",
        "failure_mode": "Wrong amounts / missed fields",
        "guardrails": "High confidence threshold; human review of low-confidence; audit log of every extraction",
    },
    "finance_expense_categorization": {
        "vertical": "Finance",
        "task": "Categorize expenses (travel, software, office)",
        "volume_per_day": "50-500",
        "language_heavy": True,
        "tool_using": True,  # ERP, expense system
        "measurable": True,  # categorization accuracy
        "hallucination_tolerance": "low",
        "compliance_risk": "medium",
        "fit_score": 14,
        "annual_roi_usd": "20K-200K",
        "failure_mode": "Mis-categorized expenses",
        "guardrails": "Confidence threshold; clear category list; human review of low-confidence",
    },
    "legal_contract_review": {
        "vertical": "Legal",
        "task": "Review contracts for key clauses (term, liability, IP)",
        "volume_per_day": "10-100",
        "language_heavy": True,
        "tool_using": True,  # document storage, clause library
        "measurable": True,  # did we catch the clause?
        "hallucination_tolerance": "zero",  # missed clause = lawsuit
        "compliance_risk": "high",
        "fit_score": 12,
        "annual_roi_usd": "50K-500K",
        "failure_mode": "Missed clauses / wrong analysis",
        "guardrails": "Lawyer review of every contract; clause library in RAG; high confidence threshold",
    },
    "legal_compliance_checking": {
        "vertical": "Legal",
        "task": "Check documents for compliance (GDPR, HIPAA, SOC 2)",
        "volume_per_day": "50-500",
        "language_heavy": True,
        "tool_using": True,  # document storage, compliance rules
        "measurable": True,  # violation detection
        "hallucination_tolerance": "zero",  # missed violation = fine
        "compliance_risk": "high",
        "fit_score": 13,
        "annual_roi_usd": "50K-500K",
        "failure_mode": "False negatives (missed violations)",
        "guardrails": "Compliance rules in the system prompt; lawyer review of every report",
    },
    "healthcare_clinical_notes": {
        "vertical": "Healthcare",
        "task": "Generate clinical notes from doctor-patient conversations",
        "volume_per_day": "100-1000",
        "language_heavy": True,
        "tool_using": True,  # EMR, transcription
        "measurable": True,  # note accuracy
        "hallucination_tolerance": "zero",  # hallucinated medical info = harm
        "compliance_risk": "high",  # HIPAA
        "fit_score": 12,
        "annual_roi_usd": "100K-1M",
        "failure_mode": "Hallucinated medical info",
        "guardrails": "Doctor review of every note; medical references in RAG; high confidence threshold",
    },
    "healthcare_prior_auth": {
        "vertical": "Healthcare",
        "task": "Process prior authorization requests (insurance)",
        "volume_per_day": "50-500",
        "language_heavy": True,
        "tool_using": True,  # insurance API, EMR
        "measurable": True,  # approval rate
        "hallucination_tolerance": "zero",
        "compliance_risk": "high",  # HIPAA + insurance
        "fit_score": 12,
        "annual_roi_usd": "50K-500K",
        "failure_mode": "Wrong CPT codes / wrong approvals",
        "guardrails": "CPT code lookup; insurance rules; human review of every request",
    },
}
```

The 6-axis use case fit rubric:

```python
def score_use_case(use_case: dict) -> int:
    """Score a use case on 6 axes (4 fit + 2 risk)."""
    score = 0
    # Fit axes (0-3 each, higher is better)
    score += min(3, use_case.get("volume_per_day", 0) // 100)  # 0, 1, 2, 3
    score += 3 if use_case.get("language_heavy") else 0
    score += 3 if use_case.get("tool_using") else 0
    score += 3 if use_case.get("measurable") else 0
    # Risk axes (0-3 each, higher is better, INVERSE)
    hall_tolerance = use_case.get("hallucination_tolerance", "zero")
    score += {"zero": 0, "low": 1, "medium": 2, "high": 3}[hall_tolerance]
    compliance = use_case.get("compliance_risk", "high")
    score += {"high": 0, "medium": 1, "low": 2, "none": 3}[compliance]
    return score

# Strong fit: 12-18
# Moderate fit: 8-11
# Weak fit: <8
```

The use case selection matrix (the FDE's reference):

```python
def recommend_use_cases(customer_profile: dict) -> list:
    """Recommend use cases for a customer based on their profile."""
    vertical = customer_profile.get("vertical", "cs")
    volume = customer_profile.get("volume_per_day", 100)
    compliance = customer_profile.get("compliance_regime", "none")
    budget = customer_profile.get("budget_per_month_usd", 5000)

    recommendations = []

    # Pick use cases from the library that match the customer's profile
    for use_case_name, use_case in USE_CASE_LIBRARY.items():
        if use_case["vertical"] != vertical:
            continue
        if volume < 10:
            continue
        if use_case["compliance_risk"] == "high" and compliance == "none":
            continue  # Skip high-compliance use cases for non-compliant customers
        if use_case["fit_score"] < 12:
            continue  # Only strong fits
        # Check ROI fits the budget
        annual_roi = use_case["annual_roi_usd"]
        if "K" in annual_roi:
            roi_low = int(annual_roi.split("K")[0].split("-")[0]) * 1000
            if roi_low < budget * 12 * 3:  # ROI should be 3x the budget
                continue
        recommendations.append(use_case_name)

    return recommendations
```

The pattern that wins interviews is the "4 criteria + 12 use cases + 6-axis rubric" pattern. The candidate who says "I score use cases on 6 axes (volume, language, tool-use, measurability, hallucination tolerance, compliance). 12 use cases across 6 verticals meet all 4 criteria. The strong fits are 12-18; moderate 8-11; weak <8. The wrong choice is to pitch a weak-fit use case (e.g., brand voice drafting) just because the customer asked. The right choice is the rubric + the library + the recommendation" is the candidate who demonstrates the use-case-mindset.

## Code or example

The 5 most common use case fit errors:

```python
USE_CASE_ERRORS = {
    "low_volume": {
        "symptom": "FDE builds the agent; the customer uses it 5 times/day; the ROI is 0",
        "cause": "The use case doesn't meet the volume criterion (>100/day)",
        "fix": "Score the use case first; reject low-volume use cases; ask the customer for a higher-volume use case",
    },
    "not_language_heavy": {
        "symptom": "The agent is forced to do image classification; the accuracy is poor",
        "cause": "The use case doesn't meet the language-heavy criterion",
        "fix": "Pick a use case that is text or speech; reject image-only use cases (or add a vision model)",
    },
    "subjective_success": {
        "symptom": "The agent's output is hard to evaluate; the customer says 'it's not quite right'",
        "cause": "The use case doesn't meet the measurable criterion",
        "fix": "Pick a use case with objective success criteria; for subjective tasks, add a human reviewer",
    },
    "zero_hallucination_tolerance": {
        "symptom": "The customer rejects the agent because of a single hallucination",
        "cause": "The use case has zero hallucination tolerance; the agent is not the right tool",
        "fix": "Pick a use case with medium-to-high tolerance; for zero-tolerance tasks, design a human-in-the-loop",
    },
    "compliance_underestimated": {
        "symptom": "The agent processes PHI; the customer realizes the agent isn't HIPAA compliant",
        "cause": "FDE missed the compliance criterion; built the agent without HIPAA controls",
        "fix": "Score compliance first; if high, design for HIPAA / PCI / SOC 2 from day 1; never retrofit",
    },
}
```

The 3 use case expansion patterns (the FDE's growth strategy):

```python
EXPANSION_PATTERNS = {
    "vertical_expansion": {
        "description": "Start with 1 use case in 1 vertical; expand to 3+ use cases in the same vertical",
        "example": "PacificFreight: CS email drafting → CS ticket routing → CS FAQ answering",
        "best_for": "Single-team customers; the FDE proves value in 1 team, then expands to adjacent teams",
    },
    "vertical_to_vertical": {
        "description": "Start with 1 use case in 1 vertical; expand to other verticals",
        "example": "PacificFreight: CS email drafting → sales lead qualification → ops report generation",
        "best_for": "Multi-team customers; the FDE proves value in CS, then expands to sales and ops",
    },
    "use_case_to_platform": {
        "description": "Start with 1 use case; build the platform; let the customer self-serve new use cases",
        "example": "Northwind: lead qualification → custom workflows in n8n → customer-built use cases",
        "best_for": "Mature customers; the FDE builds the platform, the customer self-serves",
    },
}
```

The AtlasMart use case library (the case study):

```python
ATLASMART_USE_CASES = {
    "cs_email_drafting": {
        "vertical": "Customer service",
        "volume_per_day": 5000,
        "annual_roi_usd": 500000,
        "fit_score": 16,
        "implementation": "Agent handles 70%; human reviews 30%",
        "status": "In production",
    },
    "cs_ticket_routing": {
        "vertical": "Customer service",
        "volume_per_day": 5000,
        "annual_roi_usd": 1000000,
        "fit_score": 15,
        "implementation": "Agent routes 95%; human reviews 5% (low-confidence)",
        "status": "In production",
    },
    "ops_anomaly_detection": {
        "vertical": "Operations",
        "volume_per_day": 100,
        "annual_roi_usd": 200000,
        "fit_score": 14,
        "implementation": "Agent detects revenue drops, traffic spikes, error spikes",
        "status": "In pilot",
    },
    "finance_invoice_processing": {
        "vertical": "Finance",
        "volume_per_day": 1000,
        "annual_roi_usd": 300000,
        "fit_score": 13,
        "implementation": "Agent extracts data from invoices; human reviews <5%",
        "status": "Planned Q1 2027",
    },
    "total_annual_roi": "$2M across 4 use cases",
    "expansion_strategy": "Vertical expansion: add 1-2 use cases per quarter; aim for 10 use cases by 2027",
}
```

## Production addendum

The use case library question is the answer to "where do AI agents work best." The 60-second script:

> "4 criteria: repetitive (>100/day), language-heavy (text or speech), tool-using (APIs or queries), measurable (objective success). 12 use cases across 6 verticals: CS (email drafting, ticket routing), sales (lead qualification, outreach), ops (report generation, anomaly detection), finance (invoice processing, expense categorization), legal (contract review, compliance), healthcare (clinical notes, prior auth). 6-axis rubric scores volume + language + tool-use + measurability + hallucination tolerance + compliance. Strong fit is 12-18; moderate 8-11; weak <8. The wrong choice is to pitch a weak-fit use case. The right choice is the rubric + the library + the recommendation."

This is the difference between a candidate who says "AI agents can do many things" and a candidate who says "4 criteria, 12 use cases across 6 verticals, 6-axis rubric, 3 expansion patterns, strong fit 12-18, the AtlasMart case is 4 use cases + $2M ROI." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-applications/use-cases/` — the use case library.
- **Reference implementation**: `course/hardcode/level-9-business/02-use-cases.md` — the canonical use case catalog.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/21-use-cases.md` — use cases as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/case-studies/engagement-1-pf-drafter.md` — the PacificFreight use case.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/company-experiences/` — use cases in interviews.

## The 3 questions this lecture preps you for

1. **"Where do AI agents work best?"** Answer: 4 criteria (repetitive >100/day, language-heavy, tool-using, measurable). 12 use cases across 6 verticals (CS, sales, ops, finance, legal, healthcare). The strong fits score 12-18 on the 6-axis rubric (volume + language + tool-use + measurability + hallucination tolerance + compliance).
2. **"How do you score a use case?"** Answer: 6-axis rubric. Volume (0-3 by orders of magnitude), language-heavy (0 or 3), tool-using (0 or 3), measurable (0 or 3), hallucination tolerance (0-3 inverse), compliance risk (0-3 inverse). Strong fit: 12-18. Moderate: 8-11. Weak: <8. The FDE rejects weak-fit use cases; the FDE recommends strong fits.
3. **"What is the use case expansion pattern?"** Answer: 3 patterns. (1) Vertical expansion: 1 use case → 3+ use cases in the same vertical. (2) Vertical-to-vertical: 1 use case → other verticals. (3) Use-case-to-platform: 1 use case → platform → customer self-serves. The pattern that wins is vertical expansion (lowest risk; same team; same workflow).

## Read next

`L9-3-the-customer-pitch-and-pricing.md` — the 10-minute pitch, the 3 pricing models, the engagement structure. The FDE's commercial toolkit for closing the deal.
