# L7.8: When to use n8n vs code — the 4-axis platform rubric

> **FDE framing in one line:** the platform decision is a tradeoff between 4 axes: team (engineering-first or not), scale (concurrent runs), latency (sub-second or not), cost (infrastructure vs developer time). n8n wins on team + cost; code wins on scale + latency. The FDE picks the platform that matches the customer's dominant axis.

## The 3 things you'll learn

1. The 4-axis platform rubric: team (engineering-first or not), scale (concurrent runs: <100 or >100), latency (p95: >1s or <1s), cost (developer time vs infrastructure). Each axis has a clear winner; the FDE picks the platform that wins on the dominant axis.
2. The 3 hybrid patterns: n8n for orchestration + Python for the hot path, Python for the agent + n8n for the integrations, code-first with n8n for the demo. The hybrid is the FDE's escape hatch when no single platform fits.
3. The "platform migration path" pattern: start with n8n (week 1), graduate to code as the workload grows (month 3), keep n8n for ops-facing workflows (forever). The migration is the FDE's response to scale.

## Concept

The platform decision is the FDE's most consequential choice in the first week of an engagement. Pick wrong and the FDE rebuilds the agent in month 3; pick right and the FDE ships the agent and moves on. The 4-axis rubric is the FDE's decision framework: **the platform that wins on the dominant axis is the right platform; the platform that loses on the dominant axis is the wrong platform, even if it wins on other axes.**

The 4 axes:

1. **Team.** Is the customer's team engineering-first? Engineering-first teams (5+ engineers, CI/CD, code review, infrastructure-as-code) prefer code; ops-first teams (1 engineer, 5 ops people, no CI/CD) prefer n8n. The FDE's bias is to assume engineering-first; the FDE's discipline is to ask.
2. **Scale.** How many concurrent runs does the customer need? n8n handles ~100 concurrent runs per instance; code handles 1000s. If the customer needs <100, n8n is fine; if the customer needs 1000+, code is required.
4. **Latency.** What p95 latency does the customer need? n8n has a ~1s cold start; container code has a <100ms warm start. If the customer needs sub-second p95, code is required; if the customer can tolerate 1-5s, n8n is fine.
5. **Cost.** What's the dominant cost? n8n is cheaper on developer time (1 day vs 1 sprint); code is cheaper on infrastructure at scale ($20/month VM vs $200/month n8n cloud). For SMB workloads, developer time dominates; for enterprise workloads, infrastructure dominates.

The 3 hybrid patterns:

1. **n8n orchestrates + Python does the hot path.** The n8n workflow calls a Python API for the slow / complex / sub-second step. The FDE uses this pattern when the orchestration is ops-friendly (n8n) but the core logic is engineering-heavy (Python). Example: n8n for the lead qualification workflow + Python for the actual ML scoring model.
2. **Python agent + n8n for integrations.** The Python agent calls n8n webhooks for the integrations the customer needs. The FDE uses this pattern when the core agent is engineering-heavy (Python) but the customer's tech stack is ops-friendly (n8n). Example: Python for the ML model + n8n for the Slack/HubSpot/Salesforce integrations.
3. **Code-first with n8n for the demo.** The FDE builds the production system in code; the FDE builds a thin n8n workflow that demos the system to non-engineers. The FDE uses this pattern when the customer is ops-first but the production system needs to scale. Example: Python agent in production + n8n workflow that demos the agent to the customer's VP of Ops.

The "platform migration path" pattern is the FDE's response to scale. The path is:

1. **Week 1:** Start with n8n. The FDE ships a 6-node workflow in 1 day. The customer sees the result immediately.
2. **Month 1-3:** Iterate on n8n. The FDE adds nodes, tools, and integrations based on customer feedback. The cost stays low.
3. **Month 3-6:** Graduate the hot path to code. The FDE identifies the step that's slow / expensive / complex and rewrites it in Python. The n8n workflow calls the Python API.
4. **Month 6+:** Keep n8n for ops-facing workflows. The customer uses n8n to add new integrations, new triggers, new outputs without FDE involvement. The FDE moves on to the next engagement.

**The migration is the FDE's response to scale; the wrong choice is to over-engineer on day 1 (build in Python when n8n is enough) or under-engineer on month 6 (stay on n8n when the customer needs scale).**

## The pattern

The 4-axis rubric (the FDE's decision framework):

```python
def pick_platform(requirements: dict) -> str:
    """Pick n8n, code, or hybrid based on the 4 axes."""
    team_eng_first = requirements.get("team_engineering_first", False)
    concurrent_runs = requirements.get("concurrent_runs", 50)
    latency_p95_s = requirements.get("latency_p95_s", 2.0)
    monthly_infra_budget = requirements.get("monthly_infra_budget_usd", 100)
    developer_time_days = requirements.get("developer_time_days", 5)

    # Score each platform
    n8n_score = 0
    code_score = 0
    hybrid_score = 0

    # Team axis: n8n wins for ops-first teams
    if not team_eng_first:
        n8n_score += 3
        hybrid_score += 1
    else:
        code_score += 3
        hybrid_score += 1

    # Scale axis: code wins for >100 concurrent runs
    if concurrent_runs > 100:
        code_score += 3
        hybrid_score += 2
    else:
        n8n_score += 2

    # Latency axis: code wins for sub-second p95
    if latency_p95_s < 1.0:
        code_score += 3
        hybrid_score += 2
    else:
        n8n_score += 2

    # Cost axis: depends on the dominant cost
    if developer_time_days < 3 and monthly_infra_budget > 200:
        code_score += 2  # Developer time is not the bottleneck
    elif developer_time_days >= 3 and monthly_infra_budget < 100:
        n8n_score += 3  # Developer time is the bottleneck
    else:
        hybrid_score += 2

    # Pick the winner
    scores = {"n8n": n8n_score, "code": code_score, "hybrid": hybrid_score}
    return max(scores, key=scores.get)
```

The platform comparison matrix (the FDE's reference):

```python
PLATFORM_COMPARISON = {
    "n8n": {
        "team_fit": "Ops-first; non-engineering teams",
        "scale": "<100 concurrent runs per instance",
        "latency": "p95 1-5s (cold start ~1s)",
        "cost_setup": "$0 (self-hosted) or $20/month (cloud)",
        "cost_dev_time": "1 day for 6-node workflow",
        "best_for": "SMB, ops-first, integrations-heavy, latency-tolerant",
        "weakness": "Sub-second latency, 1000s of concurrent runs, complex custom logic",
    },
    "code": {
        "team_fit": "Engineering-first teams",
        "scale": "1000s of concurrent runs (container + auto-scaling)",
        "latency": "p95 <500ms (warm container)",
        "cost_setup": "$20-200/month depending on infra",
        "cost_dev_time": "1-2 weeks for the same workflow",
        "best_for": "Enterprise, engineering-first, sub-second latency, scale",
        "weakness": "Slower to ship; higher upfront cost; requires engineering team",
    },
    "hybrid": {
        "team_fit": "Mixed; engineering + ops",
        "scale": "Depends on the code component",
        "latency": "Depends on the code component",
        "cost_setup": "$50-200/month",
        "cost_dev_time": "1 week for the hot path + 1 day for n8n",
        "best_for": "Mixed teams; engineering-heavy core + ops-heavy integrations",
        "weakness": "Two systems to maintain; FDE owns both",
    },
}
```

The 3 hybrid patterns in detail:

```python
HYBRID_PATTERNS = {
    "n8n_orchestrates_python_hot_path": {
        "description": "n8n workflow calls a Python API for the slow / complex / sub-second step",
        "example": "Northwind lead qualification: n8n workflow + Python ML scoring model",
        "architecture": "n8n (Webhook → AI Agent → IF) → POST to Python API → Python returns score → IF branches",
        "best_for": "Ops-friendly orchestration + engineering-heavy core logic",
        "maintenance": "FDE owns Python; customer owns n8n",
    },
    "python_agent_n8n_integrations": {
        "description": "Python agent calls n8n webhooks for the integrations",
        "example": "PacificFreight drafter (Python) → n8n workflow → Slack/HubSpot/Postgres",
        "architecture": "Python agent emits 'integration_call' → POST to n8n webhook → n8n executes integration",
        "best_for": "Engineering-heavy core + ops-friendly tech stack",
        "maintenance": "FDE owns Python; customer owns n8n integrations",
    },
    "code_first_n8n_for_demo": {
        "description": "Production in code; n8n workflow demos the system to non-engineers",
        "example": "Multi-agent dispatcher (Python) + n8n workflow that demos 3 agents to VP of Ops",
        "architecture": "Python in production; n8n workflow calls the Python API for demo purposes",
        "best_for": "Ops-first customer + engineering-heavy production system",
        "maintenance": "FDE owns Python; customer owns the n8n demo workflow",
    },
}
```

The platform migration path (the FDE's response to scale):

```python
MIGRATION_PATH = {
    "week_1": {
        "platform": "n8n",
        "deliverable": "6-node workflow; working end-to-end",
        "rationale": "Ship fast; prove the value; defer the engineering decision",
        "team": "FDE + customer ops team",
    },
    "month_1_to_3": {
        "platform": "n8n + light code",
        "deliverable": "Add tools, integrations, outputs based on customer feedback",
        "rationale": "Iterate on the workflow; cost stays low; FDE adds Python only for hot paths",
        "team": "FDE + customer ops team",
    },
    "month_3_to_6": {
        "platform": "n8n + significant code",
        "deliverable": "Hot path rewritten in Python; n8n calls the Python API",
        "rationale": "Customer's scale demands sub-second latency or 1000s of concurrent runs",
        "team": "FDE + customer engineering team",
    },
    "month_6_plus": {
        "platform": "n8n (for ops-facing workflows) + code (for hot paths)",
        "deliverable": "Production system in code; customer uses n8n to add new integrations",
        "rationale": "Customer self-serves new workflows; FDE moves on",
        "team": "Customer ops team (self-serve) + customer engineering team (hot paths)",
    },
}
```

The pattern that wins interviews is the "4 axes + 3 hybrids + migration path" pattern. The candidate who says "I pick the platform based on 4 axes: team (engineering-first or not), scale (concurrent runs), latency (p95), cost (developer time vs infrastructure). The 3 hybrid patterns cover the mixed cases: n8n orchestrates + Python does the hot path; Python agent + n8n for integrations; code-first with n8n for the demo. The migration path is start with n8n (week 1), graduate to code as the workload grows (month 3), keep n8n for ops-facing workflows (forever). The wrong choice is to over-engineer on day 1 (build in Python when n8n is enough) or under-engineer on month 6 (stay on n8n when the customer needs scale)" is the candidate who demonstrates the platform-mindset.

## Code or example

The 5 platform-decision scenarios (the FDE's case studies):

```python
PLATFORM_SCENARIOS = {
    "scenario_1_northwind": {
        "customer": "8-person SMB, 1 engineer, ops-first",
        "team": "ops-first",
        "scale": "200 leads/day = 5 concurrent",
        "latency": "5 seconds is fine",
        "cost": "developer time is critical",
        "verdict": "n8n (the case study in L7.7)",
        "rationale": "All 4 axes favor n8n; ship in 1 day",
    },
    "scenario_2_pacificfreight": {
        "customer": "12-person SMB, 1 engineer, ops + engineering",
        "team": "mixed",
        "scale": "150 emails/day = 3 concurrent",
        "latency": "1.8s p95 is acceptable",
        "cost": "developer time matters but infra is also a factor",
        "verdict": "hybrid (Python agent + n8n for integrations)",
        "rationale": "Python for the drafter (engineering); n8n for Slack/CRM (ops)",
    },
    "scenario_3_acme_enterprise": {
        "customer": "500-person enterprise, 20 engineers, engineering-first",
        "team": "engineering-first",
        "scale": "10,000 emails/day = 200 concurrent",
        "latency": "sub-second required",
        "cost": "infrastructure budget is $5K/mo",
        "verdict": "code (containerized Python + LangGraph + K8s)",
        "rationale": "All 4 axes favor code; n8n is too slow and can't scale",
    },
    "scenario_4_government_agency": {
        "customer": "1000-person agency, 5 engineers, ops-first, on-prem required",
        "team": "ops-first",
        "scale": "5,000 requests/day = 50 concurrent",
        "latency": "10 seconds is fine",
        "cost": "developer time is critical; infra is on-prem",
        "verdict": "n8n (self-hosted on-prem)",
        "rationale": "n8n works on-prem; ops-friendly; latency-tolerant",
    },
    "scenario_5_fintech_startup": {
        "customer": "20-person startup, 5 engineers, engineering-first, sub-second latency required",
        "team": "engineering-first",
        "scale": "100,000 requests/day = 500 concurrent",
        "latency": "sub-second required",
        "cost": "infra is the bottleneck",
        "verdict": "code (high-performance Python + gRPC + Redis)",
        "rationale": "All 4 axes favor code; n8n is not fast enough",
    },
}
```

The FDE's platform-decision interview answer:

```python
def interview_answer_platform(requirements: dict) -> str:
    """The 60-second platform decision answer."""
    team = "ops-first" if not requirements["team_eng_first"] else "engineering-first"
    scale = "high" if requirements["concurrent_runs"] > 100 else "low"
    latency = "sub-second" if requirements["latency_p95_s"] < 1.0 else "tolerant"
    cost = "developer-time-critical" if requirements["developer_time_days"] >= 3 else "infra-critical"

    return f"""The platform decision is a tradeoff between 4 axes. Team is {team}; scale is {scale};
    latency is {latency}; cost is {cost}.

    n8n wins on team (ops-first) + low scale + tolerant latency + developer-time-critical.
    Code wins on engineering-first team + high scale + sub-second + infra-critical.

    The 3 hybrid patterns cover the mixed cases. The migration path is start with n8n (week 1),
    graduate to code as the workload grows (month 3), keep n8n for ops-facing workflows (forever).

    For this customer, I'd pick {pick_platform(requirements)}."""
```

The PacificFreight + n8n migration (the canonical case):

```python
# PacificFreight: started with code (Phase 3), added n8n for ops-facing workflows (Phase 4)
PACIFICFREIGHT_PLATFORM_EVOLUTION = {
    "phase_1_to_3": {
        "platform": "code (Python + FastAPI + Postgres)",
        "rationale": "Engineering-first team; sub-second latency required; 150 emails/day",
    },
    "phase_4_addition": {
        "platform": "+ n8n for ops-facing workflows",
        "new_workflows": [
            "Customer onboarding: Typeform → n8n → HubSpot → Slack",
            "Daily ops report: Postgres → n8n → Slack #ops-daily",
            "Customer health score: Postgres → n8n → Linear (if score drops)",
        ],
        "rationale": "Customer ops team can self-serve new workflows without FDE",
        "team": "FDE owns the code; customer ops owns n8n",
    },
    "future": {
        "platform": "code + n8n (stable)",
        "rationale": "Customer self-serves new n8n automations; FDE on-call for code",
        "outcome": "FDE engagement ends; customer continues to ship",
    },
}
```

## Production addendum

The platform decision question is the answer to "n8n vs code, when do you pick each." The 60-second script:

> "4 axes. Team (engineering-first or not). Scale (concurrent runs: <100 or >100). Latency (p95: sub-second or tolerant). Cost (developer time vs infrastructure). n8n wins on team + low scale + tolerant latency + developer-time-critical. Code wins on engineering-first + high scale + sub-second + infra-critical. 3 hybrid patterns cover the mixed cases: n8n orchestrates + Python hot path; Python agent + n8n integrations; code-first + n8n for the demo. The migration path is start with n8n (week 1), graduate to code (month 3), keep n8n for ops-facing workflows (forever). The wrong choice is over-engineering on day 1 or under-engineering on month 6. The right choice is the 4 axes + 3 hybrids + migration path."

This is the difference between a candidate who says "we use n8n" or "we use code" and a candidate who says "4 axes, 3 hybrids, migration path, the platform matches the dominant axis, the wrong choice is over-engineering on day 1." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-applications/n8n/platform-decision.md` — the platform rubric.
- **Reference implementation**: `course/hardcode/level-7-n8n/08-platform-decision.md` — the canonical decision framework.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/15-low-code-platforms.md` — n8n as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/` — Phase 4 uses both Python (Projects 1-3) and adds n8n for ops-facing workflows.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/10-low-code-platforms.md` — n8n as a system design choice.

## The 3 questions this lecture preps you for

1. **"n8n vs code, when do you pick each?"** Answer: 4 axes. n8n wins on ops-first team, <100 concurrent runs, latency-tolerant, developer-time-critical. Code wins on engineering-first team, >100 concurrent runs, sub-second latency, infra-critical. The 3 hybrid patterns cover mixed cases. The migration path is start with n8n (week 1), graduate to code (month 3), keep n8n for ops (forever).
2. **"What are the 3 hybrid patterns?"** Answer: (1) n8n orchestrates + Python hot path (ops-friendly orchestration + engineering-heavy core); (2) Python agent + n8n integrations (engineering-heavy core + ops-friendly tech stack); (3) code-first + n8n for the demo (production in code, n8n demos to non-engineers). The hybrid is the escape hatch when no single platform fits.
3. **"What is the platform migration path?"** Answer: start with n8n (week 1, ship fast), iterate on n8n (month 1-3, cost stays low), graduate the hot path to code (month 3-6, scale demands), keep n8n for ops-facing workflows (month 6+, customer self-serves). The migration is the FDE's response to scale; the wrong choice is over-engineering on day 1 or under-engineering on month 6.

## Read next

`S8-agent-infrastructure/L8-1-the-infrastructure-stack.md` — Section 8 dives into agent infrastructure. The deployment, monitoring, and operations of the agent at the platform layer. From n8n (low-code) to production-grade infrastructure (high-code): Kubernetes, message brokers, vector databases, observability stacks.