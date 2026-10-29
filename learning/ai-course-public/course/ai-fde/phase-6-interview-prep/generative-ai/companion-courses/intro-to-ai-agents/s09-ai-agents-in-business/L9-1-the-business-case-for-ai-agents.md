# L9.1: The business case for AI agents — the ROI formula and the CFO pitch

> **FDE framing in one line:** the business case for an AI agent is hours saved × hourly cost × adoption rate × success rate, minus the agent's cost. The FDE's job is to compute the ROI, defend it to the CFO, and structure the engagement so the customer captures the value. The wrong choice is to pitch the LLM; the right choice is to pitch the ROI.

## In 60 seconds

> "ROI = (hours saved × hourly cost × volume × adoption × success rate) − agent cost. 3 personas: CFO (ROI), VP of Ops (adoption), CTO (security). 4 objections: hallucination (5 guardrails + 80% by design), prior failure (start with high-success use case), data sensitivity (on-prem + private model), cost of change (1-week pilot). 3 pricing models: per-run (variable), subscription (predictable), outcome (aligned). The wrong choice is to pitch the LLM. The right choice is the ROI + the personas + the objections + the engagement structure."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The ROI formula: (hours_saved_per_task × hourly_cost × task_volume × adoption_rate × success_rate) − (agent_cost). Each variable is measurable; the FDE names the source for each (e.g., "Mei currently spends 5 minutes per email; the agent does it in 30 seconds").
2. The 3 customer personas: the CFO (asks "what's the ROI?"), the VP of Ops (asks "will my team use it?"), the CTO (asks "is it secure?"). The FDE's pitch adapts to the persona; the wrong choice is to pitch all 3 with the same deck.
3. The 4 objection handlers: "the AI will hallucinate" → guardrails + eval set; "we tried AI before, it didn't work" → start with a high-success use case; "our data is sensitive" → on-prem + private model; "we can't afford the change" → start with a 1-week pilot. The FDE names the objection + the answer in 60 seconds.

## Concept

The business case for an AI agent is the answer to "is it worth the money?" The FDE's job is to compute the ROI, defend it to the customer (typically the CFO), and structure the engagement so the customer captures the value. **The wrong choice is to pitch the LLM (the customer doesn't care about the model); the right choice is to pitch the ROI in the customer's language (hours, dollars, payback period).**

The ROI formula:

```
ROI = (hours_saved_per_task × hourly_cost × task_volume × adoption_rate × success_rate) − (agent_cost)
```

Each variable is measurable:

1. **hours_saved_per_task.** The time the agent saves per task. Example: Mei currently spends 5 minutes per email; the agent does it in 30 seconds; savings = 4.5 minutes = 0.075 hours.
2. **hourly_cost.** The fully-loaded cost of the human doing the task. Example: Mei is paid $30/hour fully loaded (salary + benefits + overhead); the cost per minute is $0.50.
3. **task_volume.** The number of tasks per day / month / year. Example: Mei handles 150 emails/day = 54,750/year.
4. **adoption_rate.** The fraction of tasks the agent handles vs. the human. Example: in the first month, adoption is 50%; by month 3, adoption is 90%.
5. **success_rate.** The fraction of agent outputs that are accepted (no human revision). Example: the agent's success rate is 80% (Mei accepts 80% of drafts; revises 20%).
6. **agent_cost.** The cost of the agent: LLM API calls + infrastructure + observability + the FDE's fee. Example: $0.001 per task × 54,750 tasks = $55/year + $20K/year FDE fee = $20,055/year.

The 3 customer personas:

1. **The CFO.** Asks "what's the ROI?" The FDE's pitch: hours saved × hourly cost × adoption rate × success rate − agent cost = net savings / agent cost = ROI multiple. The CFO cares about: payback period (months), ROI multiple (3x in year 1), risk (what if it doesn't work?).
2. **The VP of Ops.** Asks "will my team use it?" The FDE's pitch: adoption rate is the leading indicator; we start with a pilot (1 use case, 1 team), measure adoption, then expand. The VP of Ops cares about: change management (how do we get the team to use it?), workflow integration (does it fit the existing process?), and the team's satisfaction.
3. **The CTO.** Asks "is it secure?" The FDE's pitch: the security perimeter is 5 layers (L8.5); the data never leaves the customer's VPC; the audit log is queryable; the agent is SOC 2 / HIPAA / PCI compliant. The CTO cares about: data residency (where does the data live?), compliance (SOC 2 / HIPAA / PCI), vendor lock-in (can we leave?).

The 3 personas × 3 pricing models matrix (the FDE's CFO-deck slide):

| Persona | Asks | Per-run model | Subscription model | Outcome model |
|---------|------|---------------|-------------------|---------------|
| **CFO** | "What's the ROI?" | Pay-per-task, easy to attribute savings | Predictable monthly bill | Only pay for verified value — strongest CFO hook |
| **VP of Ops** | "Will my team use it?" | Adoption drives cost; rewards team buy-in | Fixed cost; no per-use penalty | Team satisfaction is the outcome metric |
| **CTO** | "Is it secure?" | Metered = auditable, less data exposure | Long-term commitment, more integration | Compliance audit is the outcome metric |

**The FDE's whiteboard line:** "Match pricing to the dominant persona. The CFO's first question is ROI; pick the per-run or outcome model. The VP of Ops' first question is adoption; pick the subscription model (no per-use penalty for trying). The CTO's first question is security; pick whichever model lets you show the audit log + data residency. The wrong choice is to force a single pricing model on all 3 personas; the right choice is to lead with the model that answers the dominant persona's first question."

The 4 objection handlers:

1. **"The AI will hallucinate."** The FDE's answer: 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) + 4 RAGAS metrics + the eval set as the spec + human-in-the-loop for high-stakes outputs. Hallucination is bounded; the agent's success rate is 80% by design (the human reviews 20%).
2. **"We tried AI before, it didn't work."** The FDE's answer: the previous attempt probably failed because of a vague use case or a missing eval set. We start with a high-success use case (e.g., email triage, FAQ answering), build the eval set, ship in 2 weeks, and expand from there. The new attempt is grounded in the FDE pattern.
3. **"Our data is sensitive."** The FDE's answer: on-prem deployment (L8.2), private model (Azure OpenAI, AWS Bedrock, or self-hosted), no data retention by the model provider, the data never leaves the customer's VPC. The FDE shows the security perimeter (5 layers) and the compliance map (SOC 2 / HIPAA / PCI).
4. **"We can't afford the change."** The FDE's answer: start with a 1-week pilot ($5K); measure the ROI; if positive, expand to a 4-week engagement ($20K); if still positive, scale to a 6-month contract ($20K/month). The risk is bounded; the customer can walk away after the pilot.

## The pattern

The ROI formula in action (the PacificFreight case study):

```python
PACIFIC_FREIGHT_ROI = {
    "current_state": {
        "task": "Customer service email drafting",
        "human": "Mei (CS rep, $30/hour fully loaded)",
        "time_per_task_min": 5,
        "tasks_per_day": 150,
        "annual_cost_usd": 5 * 60 / 60 * 30 * 150 * 250 / 60,  # 5 min * 150 emails * 250 days * $30/hour
        "annual_cost_calculated": 5/60 * 30 * 150 * 250,  # $93,750
    },
    "future_state_with_agent": {
        "agent_time_per_task_min": 0.5,
        "human_review_time_per_task_min": 1,  # Mei reviews + edits
        "human_total_time_per_task_min": 1.5,
        "annual_human_cost_usd": 1.5/60 * 30 * 150 * 250,  # $28,125
        "agent_cost_per_task_usd": 0.005,
        "annual_agent_cost_usd": 0.005 * 150 * 250,  # $187.50
        "annual_fde_fee_usd": 20000,  # FDE engagement
        "annual_total_cost_usd": 28125 + 187.50 + 20000,  # $48,312
    },
    "savings": {
        "annual_savings_usd": 93750 - 48312,  # $45,438
        "monthly_savings_usd": 45438 / 12,  # $3,786
        "payback_period_months": 1,  # FDE fee recovered in <1 month
        "year_1_roi_multiple": 45438 / (20000 + 187.50),  # 2.25x
    },
    "non_financial_benefits": [
        "Faster response times (30 sec vs 5 min) → customer satisfaction +5%",
        "Mei's time reallocated to high-value work (relationship management)",
        "Scalable: 2x volume without 2x headcount",
    ],
}
```

The 3 customer personas mapped to the 4 slide deck:

```python
CUSTOMER_PERSONAS = {
    "cfo": {
        "asks": ["What's the ROI?", "What's the payback period?", "What's the risk?"],
        "deck": "ROI-focused: 1) current cost, 2) future cost, 3) savings, 4) payback period, 5) risk mitigation",
        "key_metric": "Payback period (months) and ROI multiple (year 1)",
        "objection": "Show the cost breakdown; show the risk mitigation (1-week pilot, success rate, guardrails)",
    },
    "vp_of_ops": {
        "asks": ["Will my team use it?", "How do I roll it out?", "What if the team resists?"],
        "deck": "Adoption-focused: 1) pilot use case, 2) success criteria, 3) rollout plan, 4) change management",
        "key_metric": "Adoption rate (% of tasks the agent handles) and team satisfaction (NPS)",
        "objection": "Start with a 4-week pilot with Mei only; measure adoption; expand based on results",
    },
    "cto": {
        "asks": ["Is it secure?", "Where does the data live?", "Can we leave?"],
        "deck": "Security-focused: 1) security perimeter (5 layers), 2) compliance (SOC 2 / HIPAA / PCI), 3) data residency, 4) exit strategy",
        "key_metric": "Compliance certifications; data residency; exit strategy (export all data + runbook)",
        "objection": "On-prem or VPC deployment; private model; no vendor lock-in (export all data)",
    },
}
```

The 4 objection handlers (the FDE's responses):

```python
OBJECTION_HANDLERS = {
    "ai_will_hallucinate": {
        "objection": "The AI will hallucinate; we can't trust the output.",
        "response": "5 guardrails bound hallucination: loop detector, schema validator, cost ceiling, idempotency, audit log. The agent's success rate is 80% by design; the human reviews 20% (human-in-the-loop). The eval set is the spec; the agent is tested weekly; the postmortem is the artifact.",
        "evidence": "PacificFreight: 80% thumbs-up rate; Mei reviews 20% in 30 seconds (vs 5 min from scratch)",
    },
    "tried_ai_before": {
        "objection": "We tried AI before; it didn't work.",
        "response": "The previous attempt probably failed because of a vague use case or a missing eval set. We start with a high-success use case (email triage, FAQ answering), build the eval set (100 examples), ship in 2 weeks, measure success rate, then expand. The new attempt is grounded in the FDE pattern.",
        "evidence": "PacificFreight: started with 1 use case (CS email drafting), shipped in 2 weeks, 80% success rate in month 1",
    },
    "data_is_sensitive": {
        "objection": "Our data is sensitive; we can't send it to OpenAI.",
        "response": "On-prem deployment (L8.2) or private model (Azure OpenAI, AWS Bedrock with no logging); the data never leaves the customer's VPC; the model provider is contractually obligated not to retain data; the audit log is queryable. SOC 2 / HIPAA / PCI compliant.",
        "evidence": "AtlasMart: on-prem Kubernetes; private model via Bedrock; SOC 2 Type II audited",
    },
    "cant_afford_change": {
        "objection": "We can't afford the change; the risk is too high.",
        "response": "Start with a 1-week pilot ($5K); the pilot delivers a working agent for 1 use case; if the success rate is > 70%, expand to a 4-week engagement ($20K); if the ROI is positive, scale to a 6-month contract ($20K/month). The risk is bounded; the customer can walk away after the pilot.",
        "evidence": "PacificFreight: $5K pilot → $20K engagement → $20K/month contract (10x revenue growth in 6 months)",
    },
}
```

The CFO pitch (10 minutes, 5 slides):

```markdown
# Slide 1: Current cost
- Task: customer service email drafting
- Volume: 150 emails/day = 54,750/year
- Time per task: 5 minutes
- Cost per task: $2.50 (5 min × $30/hour)
- Annual cost: $137K (Mei's fully-loaded cost)

# Slide 2: Future cost with agent
- Time per task: 1 minute (human review) + 30 sec (agent) = 1.5 min
- Cost per task: $0.75 (1.5 min × $30/hour)
- Annual cost: $41K (human) + $0.5K (LLM) + $20K (FDE) = $62K

# Slide 3: Savings
- Annual savings: $75K ($137K → $62K)
- Payback period: < 1 month (FDE fee recovered in <1 month)
- Year 1 ROI: 3.7x

# Slide 4: Risk mitigation
- 5 guardrails bound hallucination
- 4 RAGAS metrics measure quality
- Human-in-the-loop reviews 20%
- 1-week pilot validates the approach

# Slide 5: Next steps
- Week 1: pilot ($5K) — 1 use case, 1 team
- Week 2-4: expand ($20K) — 3 use cases, 3 teams
- Month 2-6: scale ($20K/month) — 10 use cases, 10 teams
- Sign the SOW today; start the pilot next Monday
```

The pattern that wins interviews is the "ROI formula + 3 personas + 4 objections" pattern. The candidate who says "the ROI is hours saved × hourly cost × volume × adoption × success rate − agent cost. The 3 personas are CFO (ROI), VP of Ops (adoption), CTO (security). The 4 objections are hallucination, prior failures, data sensitivity, cost of change. The wrong choice is to pitch the LLM (the customer doesn't care). The right choice is the ROI + the personas + the objections + the 10-minute CFO pitch" is the candidate who demonstrates the business-mindset.

## Code or example

The 5 most common business case errors and fixes:

```python
BUSINESS_CASE_ERRORS = {
    "vague_roi": {
        "symptom": "The ROI is 'significant savings' or 'increased efficiency' — no numbers",
        "cause": "FDE didn't measure the current state; didn't compute the future state",
        "fix": "Use the ROI formula: hours saved × hourly cost × volume × adoption × success rate. Every variable has a source.",
    },
    "no_pilot": {
        "symptom": "FDE asks for a $200K contract; the customer says 'no'",
        "cause": "The risk is too high; the customer needs to validate the approach",
        "fix": "Start with a 1-week pilot ($5K); measure the success rate; expand based on results",
    },
    "wrong_persona": {
        "symptom": "FDE pitches the CTO on ROI; the CTO doesn't care about dollars",
        "cause": "FDE uses the same deck for all 3 personas",
        "fix": "Adapt the deck: CFO (ROI), VP of Ops (adoption), CTO (security)",
    },
    "ignoring_change_management": {
        "symptom": "The agent is built but the team doesn't use it; the ROI is 0",
        "cause": "FDE focused on the technology; ignored the human side",
        "fix": "Pilot with 1 team; measure adoption weekly; iterate on the UX; reward the team for using the agent",
    },
    "overpromising": {
        "symptom": "FDE promises 95% success rate; the agent delivers 80%; the customer is disappointed",
        "cause": "FDE oversells to win the deal",
        "fix": "Under-promise, over-deliver. Ship at 80% success rate; iterate to 90% over 3 months. Honest numbers build trust.",
    },
}
```

The 3 customer pricing models (the FDE's commercial toolkit):

```python
PRICING_MODELS = {
    "per_run": {
        "description": "Customer pays per agent run (e.g., $0.01 per email)",
        "example": "0.01 * 54750 = $547.50/year per customer (plus the FDE fee)",
        "best_for": "Spiky workloads; the customer wants to align cost with usage",
        "risk": "Customer's bill varies; budget forecasting is hard",
    },
    "subscription": {
        "description": "Customer pays a monthly fee (e.g., $5K/month) for unlimited runs up to a cap",
        "example": "$5K/month = $60K/year per customer (predictable)",
        "best_for": "Predictable workloads; the customer wants budget predictability",
        "risk": "Customer may over-use; need a fair-use cap (e.g., 100K runs/month)",
    },
    "outcome": {
        "description": "Customer pays per successful outcome (e.g., $0.50 per qualified lead)",
        "example": "$0.50 * 500 leads/month * 12 = $3K/year per customer (variable)",
        "best_for": "The customer only pays for value; the FDE's incentive is aligned with the customer's",
        "risk": "FDE's revenue is variable; need a minimum monthly fee to cover costs",
    },
}
```

The engagement structure (the FDE's commercial scaffolding):

```python
ENGAGEMENT_STRUCTURE = {
    "week_0_pilot": {
        "duration_days": 5,
        "fee_usd": 5000,
        "deliverable": "Working agent for 1 use case; success rate measured; ROI validated",
        "go_no_go": "If success rate > 70% AND the customer can name 3+ use cases, proceed to the engagement",
    },
    "week_1_to_4_engagement": {
        "duration_weeks": 4,
        "fee_usd": 20000,
        "deliverable": "Working agent for 3 use cases; 3 teams onboarded; ROI measured",
        "go_no_go": "If ROI > 2x AND adoption > 50%, proceed to the contract",
    },
    "month_2_to_7_contract": {
        "duration_months": 6,
        "fee_usd_per_month": 20000,
        "deliverable": "Working agent for 10 use cases; 10 teams onboarded; on-call rotation; quarterly reviews",
        "exit_clause": "30-day notice; the FDE hands off the runbook; the customer can self-serve or hire a new FDE",
    },
}
```

The AtlasMart business case (the case study):

```python
ATLASMART_BUSINESS_CASE = {
    "current_state": {
        "team": "10 CS reps, $35/hour fully loaded",
        "task": "customer service email + chat handling",
        "volume": "5,000 requests/day = 1.8M/year",
        "time_per_task_min": 8,
        "annual_cost_usd": 8/60 * 35 * 1800000,  # $8.4M
    },
    "future_state": {
        "agent_handles_pct": 70,  # Agent handles 70% of requests without human intervention
        "agent_cost_per_task_usd": 0.005,
        "human_review_pct": 30,  # Human reviews 30% of agent outputs + 30% of requests
        "annual_agent_cost_usd": 0.005 * 1800000 * 0.70,  # $6,300
        "annual_human_cost_usd": 8/60 * 35 * 1800000 * 0.30,  # $2.5M
        "annual_fde_fee_usd": 240000,
        "annual_total_cost_usd": 6300 + 2500000 + 240000,  # $2.75M
    },
    "savings": {
        "annual_savings_usd": 8400000 - 2750000,  # $5.65M
        "monthly_savings_usd": 470833,
        "payback_period_months": 240000 / 470833,  # 0.5 months
        "year_1_roi_multiple": 5650000 / 240000,  # 23.5x
    },
    "engagement": "Pilot $5K → Engagement $20K → Contract $20K/month",
    "next_steps": "Sign the SOW; start the pilot next Monday; review the success rate after 1 week",
}
```

## Production addendum

The business case question is the answer to "what's the business case for AI agents." The 60-second script:

> "ROI = (hours saved × hourly cost × volume × adoption × success rate) − agent cost. 3 personas: CFO (ROI), VP of Ops (adoption), CTO (security). 4 objections: hallucination (5 guardrails + 80% by design), prior failure (start with high-success use case), data sensitivity (on-prem + private model), cost of change (1-week pilot). 3 pricing models: per-run (variable), subscription (predictable), outcome (aligned). The wrong choice is to pitch the LLM. The right choice is the ROI + the personas + the objections + the engagement structure."

This is the difference between a candidate who says "AI agents save money" and a candidate who says "ROI formula, 3 personas, 4 objections, 3 pricing models, the engagement structure is pilot → engagement → contract, the CFO pitch is 5 slides." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/consulting/02-prd-and-solution-design.md` — the ROI template.
- **Reference implementation**: `course/hardcode/level-9-failure-handling/17-circuit-breaker-llm.py` — the canonical ROI calculation.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the business case as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/case-studies/engagement-1-pf-drafter.md` — the PacificFreight case study.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/company-experiences/` — the business case in interviews.

## The 3 questions this lecture preps you for

1. **"What's the business case for AI agents?"** Answer: ROI = (hours saved × hourly cost × volume × adoption × success rate) − agent cost. The AtlasMart case: $8.4M → $2.75M = $5.65M annual savings, 23.5x ROI in year 1, payback in 0.5 months. The wrong choice is to pitch the LLM. The right choice is the ROI formula + the 3 personas + the 4 objections.
2. **"What are the 3 customer personas?"** Answer: CFO (asks "what's the ROI?", cares about payback period + risk), VP of Ops (asks "will my team use it?", cares about adoption + change management), CTO (asks "is it secure?", cares about data residency + compliance). The FDE adapts the deck to the persona; the wrong choice is the same deck for all 3.
3. **"What are the 4 objections?"** Answer: (1) hallucination → 5 guardrails + 80% by design; (2) prior failure → start with high-success use case; (3) data sensitivity → on-prem + private model; (4) cost of change → 1-week pilot. The FDE names the objection + the answer in 60 seconds; the wrong choice is to dismiss the objection (the customer walks away). The right choice is to acknowledge + provide evidence.

## Read next

`L9-2-the-use-case-library.md` — the 12 use cases across 6 verticals. The FDE's reference library for "where do AI agents work best?"
