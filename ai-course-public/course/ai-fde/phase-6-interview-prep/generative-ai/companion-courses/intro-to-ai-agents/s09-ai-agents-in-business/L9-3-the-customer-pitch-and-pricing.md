# L9.3: The customer pitch and pricing — the 10-minute close, the 3 pricing models, the engagement structure

> **FDE framing in one line:** the customer pitch is the synthesis of the entire course. The FDE delivers the 10-minute pitch, names the 3 pricing models, and proposes the engagement structure. The wrong choice is to over-pitch (the customer walks away) or under-pitch (the FDE leaves money on the table). The right choice is the 10-minute pitch + the 3 pricing models + the engagement structure.

## In 60 seconds

> "10-minute pitch: 5 slides, 2 minutes each (FDE pattern, use case + ROI, demo, engagement, next steps). 3 pricing models: per-run (variable, lowest risk), subscription (predictable, budget-friendly), outcome (aligned with value, FDE incentive = customer incentive). 3-stage engagement: pilot ($5K, 1 week, 1 use case) → engagement ($20K, 4 weeks, 3 use cases) → contract ($20K/month, 6 months, 10 use cases). The wrong choice is a 30-minute pitch with no demo. The right choice is the 10 + 3 + 3 + the pre-flight checklist + the ask for the signature."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The 10-minute pitch structure: 5 slides, 2 minutes each. The 5 slides are: (1) the FDE pattern, (2) the use case + ROI, (3) the demo, (4) the engagement structure, (5) the next steps. The 10-minute pitch is the FDE's signature; the candidate who can deliver it in 10 minutes is the candidate who can close the deal.
2. The 3 pricing models: per-run (variable, aligned with usage), subscription (predictable, aligned with budget), outcome (aligned with value). The FDE picks the model that matches the customer's dominant concern; the wrong choice is to over-price (the customer walks away) or under-price (the FDE leaves money on the table).
3. The 3-stage engagement structure: pilot (1 week, $5K, validate the approach), engagement (4 weeks, $20K, ship 3 use cases), contract (6 months, $20K/month, scale to 10 use cases). The structure is the FDE's risk-managed path to scale; the wrong choice is to jump to the contract (the customer can't validate without the pilot).

## Concept

The customer pitch is the synthesis of the entire course. The FDE has built the agent (Sections 1-8), computed the ROI (Section 9.1), selected the use case (Section 9.2). Now the FDE delivers the 10-minute pitch, names the 3 pricing models, and proposes the engagement structure. **The wrong choice is to over-pitch (the customer walks away) or under-pitch (the FDE leaves money on the table). The right choice is the 10-minute pitch + the 3 pricing models + the 3-stage engagement structure.**

The 10-minute pitch structure (5 slides, 2 minutes each):

1. **Slide 1: The FDE pattern.** Who I am, what I do, the 7 ingredients + 5 guardrails + 4 testing layers. 2 minutes. The customer understands the FDE's craft.
2. **Slide 2: The use case + ROI.** The customer's use case (e.g., CS email drafting), the current cost, the future cost with the agent, the ROI. 2 minutes. The customer sees the value.
3. **Slide 3: The demo.** Live demo of the agent handling 3 sample tasks. 2 minutes. The customer sees the agent work.
4. **Slide 4: The engagement structure.** Pilot (1 week, $5K) → engagement (4 weeks, $20K) → contract (6 months, $20K/month). 2 minutes. The customer sees the path to scale.
5. **Slide 5: The next steps.** Sign the SOW today; start the pilot next Monday; review the success rate after 1 week. 2 minutes. The customer signs.

The 3 pricing models:

1. **Per-run.** Customer pays per agent run (e.g., $0.01 per email). The model is variable; the customer's bill scales with usage. The model is right when the customer wants to align cost with usage; the model is wrong when the customer wants budget predictability.
2. **Subscription.** Customer pays a monthly fee (e.g., $5K/month) for unlimited runs up to a cap. The model is predictable; the customer can budget. The model is right when the customer wants budget predictability; the model is wrong when the customer has spiky usage (paying for unused capacity).
3. **Outcome.** Customer pays per successful outcome (e.g., $0.50 per qualified lead). The model is aligned with value; the FDE's incentive is the customer's incentive. The model is right when the outcome is measurable; the model is wrong when the outcome is subjective (e.g., "is this email good?").

The 3-stage engagement structure:

1. **Pilot (1 week, $5K).** Validate the approach. The FDE ships a working agent for 1 use case; the customer measures the success rate. The go/no-go: if success rate > 70%, proceed to the engagement.
2. **Engagement (4 weeks, $20K).** Ship 3 use cases. The FDE builds the agent for 3 use cases, onboards 3 teams, measures the ROI. The go/no-go: if ROI > 2x and adoption > 50%, proceed to the contract.
3. **Contract (6 months, $20K/month).** Scale to 10 use cases. The FDE builds the agent for 10 use cases, onboards 10 teams, runs the on-call rotation. The exit: 30-day notice; the FDE hands off the runbook; the customer can self-serve or hire a new FDE.

## The pattern

The 10-minute pitch script (the FDE's signature):

```markdown
# The 10-Minute AI Agent Pitch

## Slide 1: The FDE Pattern (2 min)
"I build AI agents that survive the customer. The 7 ingredients are model, tools, memory, cost ceiling, system prompt, parser, loop driver. The 5 guardrails are loop detector, schema validator, cost ceiling, idempotency, audit log. I've shipped this pattern at PacificFreight (150 emails/day, 80% success rate, $0.001/draft) and AtlasMart (5,000 requests/day, 70% automation, 23.5x ROI)."

## Slide 2: The Use Case + ROI (2 min)
"Your use case: customer service email drafting. 5,000 emails/day, currently $X/year in headcount. The agent handles 70% (3,500/day) with 80% success rate; the human reviews 30% (1,500/day). The cost is $Y in LLM + $20K/year in FDE fee. Net savings: $Z/year. Payback period: <1 month. Year 1 ROI: 23.5x."

## Slide 3: The Demo (2 min)
"Watch me demo. *opens the laptop*  Here's a customer email: 'Where is my shipment PF-1003?' The agent calls the tracker tool, gets the status, and drafts a reply. Mei can edit and send. Total time: 5 seconds vs 5 minutes. The cost: $0.001. The audit log records every step. *sends a second email*  The agent drafts a refund request. Mei reviews and approves. *sends a third email*  The agent escalates to a human. The error workflow fires; Slack alert to #oncall."

## Slide 4: The Engagement Structure (2 min)
"Here's the path to scale. Week 1: pilot ($5K) — 1 use case, 1 team. If the success rate is > 70%, we proceed. Week 2-4: engagement ($20K) — 3 use cases, 3 teams. If the ROI is > 2x, we proceed. Month 2-7: contract ($20K/month) — 10 use cases, 10 teams, on-call rotation. The risk is bounded; the customer can walk away after the pilot."

## Slide 5: The Next Steps (2 min)
"Sign the SOW today; start the pilot next Monday; review the success rate after 1 week. If the pilot succeeds, we proceed to the engagement. If the engagement succeeds, we proceed to the contract. The first ROI is in <1 month; the first use case is in production in <2 weeks. Questions?"
```

The 3 pricing models compared (the FDE's commercial toolkit):

```python
PRICING_MODELS = {
    "per_run": {
        "description": "Customer pays per agent run (e.g., $0.01 per email)",
        "structure": "Variable cost; scales with usage",
        "example_pricing": "$0.01 per email; volume = 5000/day; monthly = $1500",
        "best_for": "Spiky workloads; the customer wants to align cost with usage",
        "fde_revenue_usd_per_month": "1500",
        "customer_perspective": "I only pay for what I use; budget is variable",
        "fde_risk": "Revenue is variable; the customer can churn if volume drops",
    },
    "subscription": {
        "description": "Customer pays a monthly fee for unlimited runs up to a cap",
        "structure": "Predictable cost; capped usage",
        "example_pricing": "$5000/month for up to 100K runs; $0.01 per run over the cap",
        "best_for": "Predictable workloads; the customer wants budget predictability",
        "fde_revenue_usd_per_month": "5000 (with 80% utilization)",
        "customer_perspective": "I know my monthly cost; I can budget",
        "fde_risk": "The customer may over-use (need a fair-use cap); the customer may under-use (revenue drops)",
    },
    "outcome": {
        "description": "Customer pays per successful outcome (e.g., $0.50 per qualified lead)",
        "structure": "Aligned with value; FDE's incentive = customer's incentive",
        "example_pricing": "$0.50 per qualified lead; volume = 5000 leads/month; monthly = $2500 (assuming 100% conversion)",
        "best_for": "Measurable outcomes; the customer wants to pay for value",
        "fde_revenue_usd_per_month": "2500 (variable based on success rate)",
        "customer_perspective": "I only pay for results; the FDE is incentivized to make the agent better",
        "fde_risk": "Revenue is variable; need a minimum monthly fee to cover costs",
    },
}
```

The 3-stage engagement structure (the FDE's risk-managed path):

```python
ENGAGEMENT_STRUCTURE = {
    "stage_1_pilot": {
        "duration_days": 5,
        "fee_usd": 5000,
        "team_size": 1,  # FDE alone
        "deliverables": [
            "Working agent for 1 use case",
            "Eval set with 50+ examples",
            "Success rate measured (target: > 70%)",
            "Customer team trained on the agent",
        ],
        "go_no_go": "If success rate > 70% AND the customer can name 3+ use cases, proceed to stage 2",
    },
    "stage_2_engagement": {
        "duration_weeks": 4,
        "fee_usd": 20000,
        "team_size": 2,  # FDE + 1 engineer
        "deliverables": [
            "Working agent for 3 use cases",
            "3 customer teams onboarded",
            "ROI measured (target: > 2x)",
            "Runbook written; on-call rotation established",
        ],
        "go_no_go": "If ROI > 2x AND adoption > 50%, proceed to stage 3",
    },
    "stage_3_contract": {
        "duration_months": 6,
        "fee_usd_per_month": 20000,
        "team_size": 3,  # FDE + 1 engineer + 1 ops
        "deliverables": [
            "Working agent for 10 use cases",
            "10 customer teams onboarded",
            "On-call rotation; quarterly reviews",
            "Customer self-serve capability (n8n workflows, runbook)",
        ],
        "exit_clause": "30-day notice; FDE hands off the runbook; customer can self-serve or hire a new FDE",
    },
}
```

The 3 pricing model selection rubric (the FDE's reference):

```python
def pick_pricing_model(customer_profile: dict) -> str:
    """Pick the right pricing model for the customer."""
    workload = customer_profile.get("workload", "spiky")  # spiky, steady, bursty
    customer_concern = customer_profile.get("customer_concern", "value")  # value, budget, risk
    outcome_measurable = customer_profile.get("outcome_measurable", True)
    volume_per_month = customer_profile.get("volume_per_month", 1000)

    if customer_concern == "risk":
        return "per_run"  # Customer only pays for what they use; lowest risk
    if customer_concern == "budget" and workload == "steady":
        return "subscription"  # Predictable cost; matches steady workload
    if outcome_measurable and customer_concern == "value":
        return "outcome"  # Aligned incentives; FDE is incentivized to make the agent better
    return "subscription"  # Default: predictable, low complexity
```

The 5 most common pitch errors and fixes:

```python
PITCH_ERRORS = {
    "too_long": {
        "symptom": "FDE talks for 30 minutes; the customer's eyes glaze over",
        "cause": "FDE over-explains the technology; ignores the customer's interest",
        "fix": "10 minutes, 5 slides, 2 minutes each; cut anything that doesn't answer 'what's the ROI?'",
    },
    "no_demo": {
        "symptom": "FDE pitches the technology; the customer can't see the value",
        "cause": "FDE doesn't have a working demo; the customer has to imagine",
        "fix": "Always demo; show 3 sample tasks; show the audit log; show the error workflow",
    },
    "no_engagement_structure": {
        "symptom": "FDE asks for a $200K contract; the customer says 'no'",
        "cause": "The risk is too high; the customer needs to validate the approach",
        "fix": "Pilot ($5K) → engagement ($20K) → contract ($20K/month); the risk is bounded",
    },
    "wrong_pricing_model": {
        "symptom": "Customer asks 'what's my monthly cost?'; FDE says 'it depends on usage'",
        "cause": "FDE picked per-run pricing; the customer wants budget predictability",
        "fix": "Ask the customer about their concern (value, budget, risk); pick the model that matches",
    },
    "no_next_steps": {
        "symptom": "FDE delivers a great pitch; the customer says 'we'll get back to you'; nothing happens",
        "cause": "FDE doesn't ask for the order; the customer doesn't know what to do next",
        "fix": "End the pitch with 'sign the SOW today; start the pilot next Monday'; ask for the signature",
    },
}
```

The pattern that wins interviews is the "10-minute pitch + 3 pricing models + 3-stage engagement" pattern. The candidate who says "I deliver a 10-minute pitch (5 slides, 2 minutes each: FDE pattern, use case + ROI, demo, engagement, next steps). 3 pricing models (per-run, subscription, outcome). 3-stage engagement (pilot $5K → engagement $20K → contract $20K/month). The wrong choice is a 30-minute pitch with no demo. The right choice is the 10 + 3 + 3" is the candidate who demonstrates the sales-mindset.

## Code or example

The 10-minute pitch as a checklist (the FDE's pre-pitch ritual):

```markdown
# 10-Minute Pitch Pre-Flight Checklist

## 5 Minutes Before
- [ ] Laptop charged; demo environment running
- [ ] 3 sample tasks prepared (1 happy path, 1 edge case, 1 error)
- [ ] Dashboard loaded (cost, latency, success rate)
- [ ] Audit log ready (1 example run with 5+ steps)
- [ ] Error workflow ready (1 example Slack alert)

## Slide 1: FDE Pattern (2 min)
- [ ] 1 sentence: who I am
- [ ] 1 sentence: what I do
- [ ] 1 sentence: the 7 ingredients
- [ ] 1 sentence: the 5 guardrails
- [ ] 1 example: PacificFreight (150 emails/day, 80% success rate)

## Slide 2: Use Case + ROI (2 min)
- [ ] 1 use case (named; specific to the customer)
- [ ] Current cost (with numbers; sourced from the customer)
- [ ] Future cost (with numbers; with the agent)
- [ ] ROI (with the formula; with the multiple)

## Slide 3: Demo (2 min)
- [ ] Task 1: happy path (1 min)
- [ ] Task 2: edge case (30 sec)
- [ ] Task 3: error handling (30 sec)

## Slide 4: Engagement Structure (2 min)
- [ ] Stage 1: pilot ($5K, 1 week, 1 use case)
- [ ] Stage 2: engagement ($20K, 4 weeks, 3 use cases)
- [ ] Stage 3: contract ($20K/month, 6 months, 10 use cases)
- [ ] Exit clause: 30-day notice; runbook; self-serve

## Slide 5: Next Steps (2 min)
- [ ] "Sign the SOW today"
- [ ] "Start the pilot next Monday"
- [ ] "Review the success rate after 1 week"
- [ ] "Questions?"

## After the Pitch
- [ ] Ask for the signature
- [ ] Schedule the kickoff (if signed)
- [ ] Send the SOW (if not signed; within 24 hours)
```

The 3 pricing model selection scenarios (the FDE's case studies):

```python
PRICING_SCENARIOS = {
    "northwind_smb": {
        "customer": "8-person SMB, 200 leads/day",
        "customer_concern": "risk",  # SMBs are risk-averse
        "outcome_measurable": True,
        "verdict": "per_run",
        "rationale": "SMB wants to align cost with usage; per-run is the lowest-risk model",
        "pricing": "$0.005 per qualified lead; $300/month",
    },
    "pacificfreight_mid": {
        "customer": "12-person SMB, 150 emails/day",
        "customer_concern": "budget",  # Mid-market wants predictability
        "outcome_measurable": False,  # Email quality is subjective
        "verdict": "subscription",
        "rationale": "Mid-market wants budget predictability; subscription is the right model",
        "pricing": "$2000/month for up to 10K emails; $0.10 per email over",
    },
    "atlasmart_enterprise": {
        "customer": "200-person enterprise, 5000 emails/day",
        "customer_concern": "value",  # Enterprise wants to pay for value
        "outcome_measurable": True,  # Email success rate is measurable
        "verdict": "outcome",
        "rationale": "Enterprise wants aligned incentives; outcome pricing aligns FDE and customer",
        "pricing": "$0.50 per successful resolution (no human revision); $20K/month minimum",
    },
}
```

The AtlasMart engagement (the case study):

```python
ATLASMART_ENGAGEMENT = {
    "stage_1_pilot": {
        "duration_days": 5,
        "fee_usd": 5000,
        "use_case": "CS email drafting (1 of 5,000 emails/day)",
        "deliverable": "Working agent for 1 use case; success rate measured",
        "go_no_go": "Success rate 78% (target: > 70%); proceed to stage 2",
    },
    "stage_2_engagement": {
        "duration_weeks": 4,
        "fee_usd": 20000,
        "use_cases": ["CS email drafting", "CS ticket routing", "Ops anomaly detection"],
        "deliverable": "3 use cases; 3 teams onboarded; ROI measured",
        "go_no_go": "ROI 4.2x (target: > 2x); adoption 65% (target: > 50%); proceed to stage 3",
    },
    "stage_3_contract": {
        "duration_months": 6,
        "fee_usd_per_month": 20000,
        "use_cases_target": 10,
        "deliverable": "10 use cases; 10 teams; on-call rotation; quarterly reviews",
        "pricing_model": "subscription ($20K/month for up to 100K runs; $0.10 per run over)",
        "annual_value_to_customer": "$5.65M (savings) - $240K (FDE fee) = $5.41M",
        "annual_value_to_fde": "$240K",
    },
    "post_contract": {
        "outcome": "Customer self-serves via n8n; FDE moves on to the next engagement",
        "runbook": "100+ pages; covers monitoring, error handling, expansion patterns",
        "exit_interview": "Customer says: 'the FDE pattern worked; the agent is part of the team'",
    },
}
```

## Production addendum

The customer pitch question is the answer to "how do you sell an AI agent." The 60-second script:

> "10-minute pitch: 5 slides, 2 minutes each (FDE pattern, use case + ROI, demo, engagement, next steps). 3 pricing models: per-run (variable, lowest risk), subscription (predictable, budget-friendly), outcome (aligned with value, FDE incentive = customer incentive). 3-stage engagement: pilot ($5K, 1 week, 1 use case) → engagement ($20K, 4 weeks, 3 use cases) → contract ($20K/month, 6 months, 10 use cases). The wrong choice is a 30-minute pitch with no demo. The right choice is the 10 + 3 + 3 + the pre-flight checklist + the ask for the signature."

This is the difference between a candidate who says "I can sell AI agents" and a candidate who says "10-minute pitch, 3 pricing models, 3-stage engagement, pre-flight checklist, the ask is 'sign the SOW today, start the pilot next Monday'." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/consulting/02-prd-and-solution-design.md` — the pitch template.
- **Reference implementation**: `course/hardcode/level-2-ai-workflows/03-email-triage-pipeline.py` — the canonical pitch.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the pitch as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/case-studies/engagement-1-pf-drafter.md` — the PacificFreight engagement.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/company-experiences/` — the pitch in interviews.

## The 3 questions this lecture preps you for

1. **"How do you sell an AI agent?"** Answer: 10-minute pitch (5 slides, 2 minutes each). 3 pricing models (per-run, subscription, outcome). 3-stage engagement (pilot $5K → engagement $20K → contract $20K/month). The pre-flight checklist + the ask for the signature. The wrong choice is a 30-minute pitch with no demo. The right choice is the 10 + 3 + 3.
2. **"What are the 3 pricing models?"** Answer: (1) per-run — variable, aligned with usage, lowest risk for the customer; (2) subscription — predictable, capped usage, budget-friendly; (3) outcome — aligned with value, FDE's incentive = customer's incentive, requires measurable outcomes. The FDE picks the model that matches the customer's dominant concern (value, budget, risk).
3. **"What is the engagement structure?"** Answer: 3 stages. Pilot ($5K, 1 week, 1 use case) — validate the approach. Engagement ($20K, 4 weeks, 3 use cases) — ship + measure ROI. Contract ($20K/month, 6 months, 10 use cases) — scale. Each stage has a go/no-go gate; the customer can walk away after any stage. The risk is bounded; the FDE earns the right to scale.

## Read next — beyond this course

You have finished the conceptual content. The next step is the rest of the FDE program:

- **`course/ai-fde/phase-2-core-build/`** — the 200-line shipping agent. The FDE writes the code that implements every pattern in Sections 2, 5, 6, 8. The 7 ingredients + 5 guardrails become runnable Python.
- **`course/ai-fde/phase-3-deployment/`** — the production service. FastAPI + Postgres + Redis + Prometheus + LangGraph. The agent becomes a service the customer can call.
- **`course/ai-fde/phase-4-capstone/`** — the 4 projects (MCP, multi-agent, SLM, data analyst) + the 5 case studies + the capstone presentation. The FDE ships the full delivery.
- **`course/ai-fde/phase-5-engagement/`** — the engagement simulation. The FDE runs the 3-stage engagement from L9.3 against a mock customer; the FDE is graded on the deliverable, not the pitch.
- **`course/ai-fde/phase-6-interview-prep/`** — the centerpiece-round rehearsal. The FDE does the live build, the system design, the postmortem, the commercial round — all graded against the rubric this course preps you for.

**The wrong choice is to read this course and stop.** The right choice is to write the code, ship the engagement, run the postmortem, and move on to the next customer.

## The course is complete

You have read all 9 sections of "Intro to AI Agents and Agentic AI" — 54 lectures, ~200K words, ~12 hours of reading. The agent is now a product; the product is a business; the FDE is the bridge.

**The 7 ingredients + 5 guardrails + 4 testing layers + 4 infrastructure pillars + the n8n platform + the 6-axis use case rubric + the 10-minute pitch + the 3-stage engagement = the FDE pattern.**

The wrong choice is to know the technology without knowing the business. The right choice is to know both; the FDE pattern is the synthesis.

The next step is yours. Build the agent. Ship the engagement. Write the postmortem. Move on to the next customer. **The FDE is the craft; the craft is the practice; the practice is the loop. The loop is the FDE.**

— End of Section 9 — End of the Course —
