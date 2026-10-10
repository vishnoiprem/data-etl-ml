# L3.3: Reflex vs. deliberative agents

> **FDE framing in one line:** a reflex agent just acts (no planning); a deliberative agent plans-then-act; a reflective agent plan-act-observe-replan. The right level of planning is the minimum that achieves the target accuracy; over-planning is 3× cost waste.

## The 3 things you'll learn

1. The three levels of agent planning: reflex (0), deliberative (1 plan), reflective (replan on observation).
2. The 3-axis planning rubric: task horizon, error cost, plan reversibility — and which axis dominates for which task.
3. The "plan-and-execute" pattern: generate a plan once, execute it step-by-step, replan only when an observation contradicts the plan.

## Concept

The level of planning is the third topology axis. A reflex agent emits an action based on the current observation, with no planning and no memory of past actions. A deliberative agent generates a plan first, then executes the plan step-by-step. A reflective agent generates a plan, executes a step, observes the result, and may replan if the observation contradicts the plan. **The three levels compose: most production agents are reflective on the outer loop (replan when needed) and reflex on the inner steps (act without thinking about the next step).**

The three levels of planning:

1. **Reflex (0).** The agent emits an action based on the current observation. No planning, no memory, no replanning. The canonical example: a single LLM call that selects a tool and emits the args. The reflex agent is fast (one step), but cannot handle multi-step tasks because it cannot reason about the future.
2. **Deliberative (1 plan).** The agent generates a plan first ("I will do A, then B, then C"), then executes the plan step-by-step. The canonical example: plan-and-execute (PaE). The deliberative agent is accurate on well-bounded tasks, but cannot recover when an observation contradicts the plan.
3. **Reflective (replan).** The agent generates a plan, executes a step, observes the result, and may replan if the observation contradicts the plan. The canonical example: ReAct (Reason + Act). The reflective agent is accurate on dynamic tasks, but pays the cost of replanning on every step.

The 3-axis planning rubric:

1. **Task horizon.** How many steps does the task typically take? Single-step tasks want reflex; 3-5 step tasks want deliberative; 5-10 step tasks want reflective.
2. **Error cost.** How expensive is a wrong step? Low error cost (a wrong tool call that returns an error) wants reflex or deliberative; high error cost (a wrong tool call that moves money) wants reflective.
3. **Plan reversibility.** Can the agent undo a wrong step? Reversible plans (a wrong file read can be re-read) want deliberative; irreversible plans (a sent email, a moved payment) want reflective.

The "plan-and-execute" pattern is the canonical 2026 production shape for multi-step agents. The agent generates a plan once (1 LLM call), executes the plan step-by-step (1 LLM call per step, but with the plan as context), and replans only when an observation contradicts the plan. **The plan-and-execute agent is 3× cheaper than the fully reflective ReAct agent on well-bounded tasks, and 95% as accurate.**

## The pattern

The reflex agent, in 5 lines:

```python
def reflex_agent(observation: str, tools: dict, llm) -> str:
    """Reflex: act based on current observation, no planning, no memory."""
    return llm([{"role": "user", "content": f"Observation: {observation}\nAction:"}]).choices[0].message.content
```

The deliberative agent, in 30 lines:

```python
def deliberative_agent(goal: str, tools: dict, llm) -> str:
    """Deliberative: plan first, then execute. No replanning."""
    plan = llm([{"role": "user", "content": f"Goal: {goal}\nGenerate a step-by-step plan."}])
    for step in parse_plan(plan):
        obs = tools[step.tool](step.args)
        # No replanning: just continue to the next step
    return llm([{"role": "user", "content": f"Plan: {plan}\nObservations: ...\nFinal answer:"}])
```

The reflective agent (ReAct), in 40 lines:

```python
def reflective_agent(goal: str, tools: dict, llm, max_turns: int = 10) -> str:
    """Reflective: plan, act, observe, replan. The ReAct pattern."""
    messages = [{"role": "user", "content": goal}]
    for turn in range(max_turns):
        output = llm(messages)  # Plan + action in one step
        step = parse_step(output)
        if step.type == "final": return step.answer
        obs = tools[step.tool](step.args)
        messages.append({"role": "tool", "content": str(obs)})
        # The next turn's LLM call replans based on the observation
```

The plan-and-execute agent, in 50 lines:

```python
def plan_and_execute_agent(goal: str, tools: dict, llm, max_replans: int = 2) -> str:
    """Plan once, execute, replan only when observation contradicts plan."""
    plan = llm([{"role": "user", "content": f"Goal: {goal}\nGenerate a JSON plan: [{{step, tool, args}}]"}])
    plan = parse_plan(plan)
    observations = []
    for replan_count in range(max_replans + 1):
        for step in plan:
            obs = tools[step.tool](step.args)
            observations.append(obs)
            if contradicts_plan(obs, step):
                # Replan: regenerate the remaining steps
                plan = replan(goal, observations, llm)
                break
        else:
            break  # Plan executed without contradiction
    return synthesize(observations, llm)
```

The pattern that wins interviews is the "plan-and-execute as the production default" pattern. The candidate who says "I default to plan-and-execute for multi-step tasks; I use reflex for single-step; I use ReAct only when the task is dynamic and the plan is likely to be invalidated. Plan-and-execute is 3× cheaper than ReAct on well-bounded tasks and 95% as accurate" is the candidate who demonstrates the planning-mindset.

## Code or example

The planning-level decision rubric:

```python
def pick_planning_level(task: dict) -> str:
    """Pick reflex, deliberative, or reflective based on the task."""
    horizon = task.get("horizon_steps", 1)
    error_cost = task.get("error_cost_usd", 0)
    reversible = task.get("plan_reversible", True)
    if horizon == 1:
        return "reflex"
    if error_cost > 100 or not reversible:
        return "reflective"
    return "deliberative"  # plan-and-execute
```

The plan-and-execute agent for the CS drafter:

```python
CS_DRAFTER_PLAN = {
    "lookup": "tracker.lookup(shipment_id=...)",
    "classify": "classify_intent(email=...)",  # reactive inner call
    "draft": "draft_reply(email=..., context=...)",  # reactive inner call
}

def cs_drafter_plan_and_execute(email: str, shipment_id: str, llm, tools: dict) -> str:
    """Plan: lookup, classify, draft. Replan if lookup returns 'unknown'."""
    plan = CS_DRAFTER_PLAN
    # Step 1: lookup
    shipment = tools["tracker.lookup"]({"shipment_id": shipment_id})
    if shipment["status"] == "unknown":
        # Replan: ask for clarification
        plan = [{"step": "clarify", "tool": "escalate.to_human", "args": {"reason": "shipment not found"}}]
    # Step 2: classify
    intent = llm([{"role": "user", "content": f"Classify intent: {email}"}])
    # Step 3: draft
    return llm([{"role": "user", "content": f"Draft reply to: {email}\nShipment: {shipment}\nIntent: {intent}"}])
```

The reflective vs deliberative cost comparison:

```python
# A 10-step CS-drafter task
# Reflex: 10 LLM calls, no planning, no replanning. $0.01, 60% accurate.
# Deliberative: 1 plan + 10 execute + 1 synthesize = 12 LLM calls. $0.012, 85% accurate.
# Reflective: 10 turns × (1 think + 1 act) = 20 LLM calls. $0.02, 90% accurate.
# Plan-and-execute: 1 plan + 10 execute (no replan) + 1 synthesize = 12 LLM calls. $0.012, 87% accurate.
# Plan-and-execute wins: 95% of reflective's accuracy at 60% of the cost.
```

## Production addendum

The reflex-vs-deliberative question is the answer to "when do you need planning in the agent." The 60-second script:

> "Three levels. Reflex: act based on current observation, no planning. Deliberative: plan once, execute step-by-step, no replanning. Reflective: plan, act, observe, replan. The default production shape is plan-and-execute: 1 plan + N execute + 1 synthesize. Plan-and-execute is 3× cheaper than fully reflective ReAct on well-bounded tasks and 95% as accurate. Use reflex for single-step; use deliberative (plan-and-execute) for 3-10 step tasks; use reflective (ReAct) only when the plan is likely to be invalidated. The wrong choice is full ReAct for every multi-step task (3× cost waste, marginal accuracy gain). The wrong choice is reflex for a 10-step task (60% accuracy). The right choice is plan-and-execute as the default; escalate to reflective when the task is dynamic."

This is the difference between a candidate who says "I use ReAct" and a candidate who says "I default to plan-and-execute; ReAct is the fallback for dynamic tasks." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-4-langgraph.py` — the plan-and-execute pattern with conditional replan.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/09-react-agent-tools.py` — the reflective ReAct agent.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/02-the-fde-loop.md` — the planning loop.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/` — the orchestrator as a deliberative agent; each sub-agent as reflective.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — planning as a system design pattern.

## The 3 questions this lecture preps you for

1. **"When do you need planning in the agent?"** Answer: when the task horizon is > 1 step. Reflex for 1 step, deliberative (plan-and-execute) for 3-10 steps, reflective (ReAct) for 5-10 steps with dynamic environments.
2. **"What is plan-and-execute?"** Answer: generate a plan once, execute the plan step-by-step, replan only when an observation contradicts the plan. 1 plan + N execute + 1 synthesize. The default production shape: 3× cheaper than ReAct on well-bounded tasks, 95% as accurate.
3. **"What is the difference between ReAct and plan-and-execute?"** Answer: ReAct re-plans on every step (the model emits Thought + Action in every turn); plan-and-execute plans once and replans only on contradiction. ReAct is more accurate on dynamic tasks; plan-and-execute is cheaper and more interpretable.

## Read next

`L3-4-hierarchical-agents.md` — the fourth axis. Hierarchical agents have an orchestrator (the manager) and sub-agents (the workers). The orchestrator delegates; the sub-agents execute. The right level of hierarchy depends on the task's parallelism and the team's expertise.