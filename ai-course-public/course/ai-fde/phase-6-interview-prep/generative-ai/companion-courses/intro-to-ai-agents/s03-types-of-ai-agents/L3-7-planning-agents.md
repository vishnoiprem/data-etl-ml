# L3.7: Planning agents — plan, execute, replan

> **FDE framing in one line:** a planning agent generates a plan first, executes it step-by-step, and replans when an observation contradicts the plan. The right planning depth is the minimum that achieves the target accuracy; over-planning is 3× cost waste.

## The 3 things you'll learn

1. The 3 planning patterns: plan-and-execute (1 plan + N execute + 1 synthesize), plan-and-replan (replan when contradiction), HTN (hierarchical task network — recursive sub-plans).
2. The 3-axis planning rubric: task horizon, error cost, plan reversibility — and which axis dominates for which task.
3. The "plan is a contract" pattern: the plan is a typed data structure; the executor dispatches step-by-step; the synthesizer combines the results.

## Concept

A planning agent separates "what to do" from "how to do it." The planner generates a sequence of steps (the plan); the executor dispatches each step; the synthesizer combines the results into a final answer. The three patterns differ in when the plan is regenerated: plan-and-execute (once), plan-and-replan (on contradiction), HTN (recursively for each sub-task).

The three planning patterns:

1. **Plan-and-execute (PaE).** Generate a plan once (1 LLM call), execute the plan step-by-step (1 LLM call per step, but with the plan as context), synthesize the final answer (1 LLM call). The plan is a typed data structure (a list of `(tool, args)` tuples); the executor dispatches deterministically; no replanning. The canonical example: LangChain's `PlanAndExecute` agent. **PaE is 3× cheaper than ReAct on well-bounded tasks and 95% as accurate.**
2. **Plan-and-replan.** Same as PaE, but the executor checks each observation against the plan; if an observation contradicts the plan (e.g., the shipment is "unknown" when the plan said "look up the shipment"), the planner regenerates the remaining steps. The canonical example: ReAct with explicit plan tracking. **Plan-and-replan is more accurate on dynamic tasks; the cost is the replanning LLM calls.**
3. **Hierarchical task network (HTN).** The plan is a tree, not a list. Each step in the plan may be a sub-plan; the executor recurses into sub-plans; the synthesizer combines the leaves. The canonical example: classical AI planning (STRIPS, PDDL). **HTN is the most expressive; the cost is the recursion overhead and the harder plan-generation prompt.**

The 3-axis planning rubric:

1. **Task horizon.** How many steps does the task typically take? 1 step wants no plan (reflex); 3-5 steps wants PaE; 5-10 steps wants PaE with replan; 10+ steps wants HTN.
2. **Error cost.** How expensive is a wrong step? Low error cost (< $10) wants PaE; medium ($10-$100) wants PaE with replan; high (> $100) wants HTN with explicit preconditions.
3. **Plan reversibility.** Can the agent undo a wrong step? Reversible wants PaE; irreversible wants PaE with replan; very irreversible (moves money, deletes data) wants HTN with explicit preconditions and postconditions.

The "plan is a contract" pattern is the recognition that the plan is a typed data structure, not a free-form string. The plan is a list of `Step` objects, each with a `tool`, `args`, and `expected_outcome`. The executor dispatches step-by-step; the synthesizer combines the actual outcomes into a final answer. **The typed plan is testable:** the FDE can write a test set of (goal → expected plan) and assert the planner produces the expected plan. The typed plan is also debuggable: the audit log shows the plan + the actual outcomes + any replans.

## The pattern

The plan-and-execute agent, in 50 lines:

```python
@dataclass
class Plan:
    steps: list  # list of {"tool": str, "args": dict, "expected": str}

@dataclass
class Step:
    tool: str
    args: dict
    expected: str
    actual: any = None
    status: str = "pending"  # pending | success | failed | replanned

def planner(goal: str, tools: dict, llm) -> Plan:
    """Generate a plan from a goal. 1 LLM call."""
    response = llm([{
        "role": "user",
        "content": f"Goal: {goal}\n"
                   f"Available tools: {list(tools.keys())}\n"
                   f"Generate a JSON plan: [{{'tool': ..., 'args': ..., 'expected': ...}}]"
    }])
    return Plan(steps=parse_json_plan(response))

def executor(plan: Plan, tools: dict) -> Plan:
    """Execute the plan step-by-step. No replanning in basic PaE."""
    for step in plan.steps:
        try:
            step.actual = tools[step.tool](step.args)
            step.status = "success"
        except Exception as e:
            step.actual = {"error": str(e)}
            step.status = "failed"
    return plan

def synthesizer(plan: Plan, goal: str, llm) -> str:
    """Combine the plan's actual outcomes into a final answer. 1 LLM call."""
    return llm([{
        "role": "user",
        "content": f"Goal: {goal}\n"
                   f"Plan outcomes: {plan.steps}\n"
                   f"Generate the final answer."
    }])

def plan_and_execute(goal: str, tools: dict, llm) -> str:
    plan = planner(goal, tools, llm)
    executed_plan = executor(plan, tools)
    return synthesizer(executed_plan, goal, llm)
```

The plan-and-replan agent:

```python
def plan_and_replan(goal: str, tools: dict, llm, max_replans: int = 2) -> str:
    plan = planner(goal, tools, llm)
    for replan_count in range(max_replans + 1):
        for step in plan.steps:
            step.actual = tools[step.tool](step.args)
            if contradicts_plan(step.actual, step):
                # Replan: regenerate the remaining steps
                remaining_goal = f"Goal: {goal}\nCompleted: {plan.steps[:plan.steps.index(step)+1]}\nFailed step: {step}"
                plan.steps = plan.steps[:plan.steps.index(step)+1] + planner(remaining_goal, tools, llm).steps
                break
        else:
            break  # Plan executed without contradiction
    return synthesizer(plan, goal, llm)
```

The pattern that wins interviews is the "plan is a typed data structure, the executor is deterministic, the synthesizer is a single LLM call" pattern. The candidate who says "I generate the plan once, execute step-by-step, synthesize the final answer; replan only when an observation contradicts the plan; the plan is a typed `Plan` object, not a free-form string" is the candidate who demonstrates the planning-mindset.

## Code or example

The 3-pattern cost-quality comparison for a 10-step CS-drafter task:

```python
# Reflex: 10 LLM calls, no planning. $0.01, 60% accurate.
# Plan-and-execute: 1 plan + 10 execute + 1 synthesize = 12 LLM calls. $0.012, 85% accurate.
# Plan-and-replan: 1 plan + 10 execute (avg 1 replan) + 1 synthesize = 14 LLM calls. $0.014, 90% accurate.
# HTN: 1 top-level plan + 5 sub-plans + 10 execute + 1 synthesize = 17 LLM calls. $0.017, 92% accurate.

# For a CS-drafter: plan-and-execute is the sweet spot.
# - Reflex is too inaccurate (60%).
# - Plan-and-replan is marginal gain (5%) for 17% more cost.
# - HTN is over-engineered (3% gain for 42% more cost).
```

The plan-and-execute CS drafter:

```python
def cs_drafter_pae(email: str, shipment_id: str, llm, tools: dict) -> str:
    """Plan-and-execute CS drafter. 3 steps."""
    # Step 1: planner generates the plan
    plan = planner(
        goal=f"Draft a reply to: {email}\nShipment: {shipment_id}",
        tools=tools,
        llm=llm,
    )
    # The plan is typically: [lookup, classify, draft]

    # Step 2: executor dispatches step-by-step
    for step in plan.steps:
        if step.tool == "tracker.lookup":
            step.actual = tools["tracker.lookup"]({"shipment_id": shipment_id})
        elif step.tool == "classify_intent":
            step.actual = classify_intent(email, llm)
        elif step.tool == "draft_reply":
            step.actual = draft_reply(email, step.actual if plan.steps[0].actual else {}, llm)

    # Step 3: synthesizer combines (or just returns the draft)
    return plan.steps[-1].actual
```

The replan trigger detection:

```python
def contradicts_plan(actual: any, step: Step) -> bool:
    """Detect when an observation contradicts the plan."""
    if step.tool == "tracker.lookup" and actual.get("status") == "unknown":
        return True  # The plan assumed a valid shipment; lookup returned unknown
    if step.tool == "refund.create" and actual.get("error") == "amount_exceeds_value":
        return True  # The plan assumed the refund amount is valid; it isn't
    if step.tool == "translate.to" and actual.get("error") == "unsupported_lang":
        return True  # The plan assumed a supported language; it isn't
    return False
```

## Production addendum

The planning question is the answer to "when do you need explicit planning in the agent." The 60-second script:

> "Three patterns. Plan-and-execute: 1 plan + N execute + 1 synthesize, 12 LLM calls for a 10-step task, 85% accurate. Plan-and-replan: same but replan on contradiction, 14 calls, 90% accurate. HTN: hierarchical plans, 17 calls, 92% accurate. **The default is plan-and-execute: 95% of plan-and-replan's accuracy at 85% of the cost.** The 3-axis rubric: task horizon, error cost, plan reversibility. For most FDE use cases (CS drafter, ops dashboard, cost analyzer), plan-and-execute is the sweet spot. Plan-and-replan for dynamic tasks (where observations often contradict). HTN for the rare cases where the task is fundamentally hierarchical (research projects, multi-document synthesis). The wrong choice is full ReAct for every multi-step task (3× cost, marginal accuracy gain). The wrong choice is reflex for a 10-step task (60% accuracy). The right choice is plan-and-execute as the default."

This is the difference between a candidate who says "I use ReAct" and a candidate who says "plan-and-execute is the default; plan-and-replan when dynamic; HTN when hierarchical; the plan is a typed data structure." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-4-langgraph.py` — the plan-and-execute pattern with conditional replan.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/10-multi-agent-orchestrator.py` — the production PaE with replan.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the planning loop.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the orchestrator as a plan-and-execute agent; each sub-agent as plan-and-replan.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — planning as a system design pattern.

## The 3 questions this lecture preps you for

1. **"When do you need explicit planning in the agent?"** Answer: when the task horizon is > 1 step and the plan is not trivially obvious from the goal. 1 step wants no plan; 3-10 steps wants plan-and-execute; 5-10 steps with dynamic environments wants plan-and-replan; 10+ steps with hierarchical structure wants HTN.
2. **"What is plan-and-execute?"** Answer: generate a plan once (1 LLM call), execute the plan step-by-step (1 call per step, with the plan as context), synthesize the final answer (1 LLM call). The plan is a typed `Plan` object, not a free-form string. 12 LLM calls for a 10-step task, 85% accurate, 3× cheaper than ReAct.
3. **"What is the difference between PaE and plan-and-replan?"** Answer: PaE plans once and executes; plan-and-replan regenerates the remaining steps when an observation contradicts the plan. PaE is 12 LLM calls, 85% accurate; plan-and-replan is 14 calls (avg 1 replan), 90% accurate. The 5% accuracy gain costs 17% more — worth it when the task is dynamic and contradictions are common.

## Read next

`L3-8-picking-the-right-topology.md` — the eighth and final lecture of Section 3. The 4-axis topology rubric (tool count, plan depth, agent count, latency budget) tells the FDE which topology to pick for which task. The right topology is the simplest one that satisfies the rubric.