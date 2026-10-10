# L5.5: The hierarchical task network (HTN) pattern

> **FDE framing in one line:** the HTN pattern is for tasks where the plan is a tree, not a list. Recursive sub-plans for hierarchical tasks like "research a topic" (which decomposes into "search, read, summarize" each of which is itself a sub-plan). The right pattern when the task naturally decomposes into recursive structure.

## The 3 things you'll learn

1. The 3 components of the HTN pattern: compound tasks (decomposable), primitive tasks (executable), methods (decomposition rules).
2. The 4-axis HTN-vs-plan-and-execute rubric: recursion depth, plan dynamism, plan interpretability, plan generation cost.
3. The "HTN for hierarchical research, PaE for linear workflows" rule of thumb.

## Concept

The HTN pattern is the most expressive planning pattern. The plan is a tree, not a list. Each node in the tree is either a compound task (decomposable into sub-tasks) or a primitive task (executable directly). The planner generates the tree top-down; the executor dispatches bottom-up (leaves first, then internal nodes). **The HTN is the right pattern when the task naturally decomposes into recursive structure — "research a topic" decomposes into "search, read, summarize" where "read" may itself decompose into "fetch, parse, extract."**

The 3 components of the HTN pattern:

1. **Compound tasks (decomposable).** A task that can be broken down into sub-tasks. Examples: "research a topic", "write a report", "plan a trip". A compound task is not directly executable; the planner must decompose it.
2. **Primitive tasks (executable).** A task that can be executed directly by a tool call. Examples: "search the web", "fetch a URL", "send an email". A primitive task is a leaf in the plan tree.
3. **Methods (decomposition rules).** A rule that says "to accomplish compound task X, decompose into sub-tasks [Y1, Y2, ..., Yn]". Methods are the planner's knowledge base; the planner selects a method for each compound task based on the current state.

The 4-axis HTN-vs-plan-and-execute rubric:

1. **Recursion depth.** How deep does the task hierarchy go? 1 level → PaE. 2-3 levels → HTN. 4+ levels → HTN with explicit method library.
2. **Plan dynamism.** Does the plan change based on intermediate results? No → PaE (plan once). Yes → HTN (replan at each level).
3. **Plan interpretability.** Does the customer need to see the plan? Yes → HTN (the tree is human-readable). No → PaE (the list is enough).
4. **Plan generation cost.** How expensive is it to generate the plan? Cheap (1 LLM call) → PaE. Expensive (multiple LLM calls per level) → HTN with method library (cached methods reduce cost).

The "HTN for hierarchical research, PaE for linear workflows" rule of thumb is the FDE's primary design heuristic. Hierarchical research (multi-document synthesis, recursive summarization) is HTN-shaped; the plan is a tree. Linear workflows (book a flight, file a tax return) are PaE-shaped; the plan is a list. **The wrong choice is HTN for a linear workflow (over-engineering, 3× plan generation cost). The wrong choice is PaE for a hierarchical task (the plan is too rigid to capture the recursion).**

## The pattern

The HTN pattern, as a class:

```python
from typing import Union

@dataclass
class CompoundTask:
    """A task that decomposes into sub-tasks."""
    name: str
    methods: list  # list of decomposition methods

@dataclass
class PrimitiveTask:
    """A task that executes directly."""
    name: str
    tool: str
    args: dict

@dataclass
class Method:
    """A decomposition rule: compound task -> sub-tasks."""
    name: str
    preconditions: list  # conditions for this method to apply
    sub_tasks: list  # list of CompoundTask or PrimitiveTask

class HTNPlanner:
    """HTN planner: decomposes compound tasks into primitive tasks."""

    def __init__(self, methods: list[Method], tools: dict):
        self.methods = methods
        self.tools = tools

    def plan(self, task: CompoundTask, state: dict) -> list[PrimitiveTask]:
        """Recursively decompose a compound task into primitive tasks."""
        if isinstance(task, PrimitiveTask):
            return [task]
        # Find a method that applies to this task in the current state
        method = self._select_method(task, state)
        if not method:
            raise ValueError(f"No method applies to {task.name} in state {state}")
        # Recursively decompose each sub-task
        primitive_tasks = []
        for sub_task in method.sub_tasks:
            primitive_tasks.extend(self.plan(sub_task, state))
        return primitive_tasks

    def _select_method(self, task: CompoundTask, state: dict) -> Method:
        for method in self.methods:
            if method.name != task.name:
                continue
            if all(check_precondition(p, state) for p in method.preconditions):
                return method
        return None
```

The canonical "research a topic" HTN:

```python
RESEARCH_METHODS = [
    Method(
        name="research_topic",
        preconditions=[],
        sub_tasks=[
            CompoundTask("identify_sources", methods=[
                Method("identify_sources", [], [
                    PrimitiveTask("web_search", "web_search", {"query": "<topic>"}),
                    PrimitiveTask("db_query", "db_query", {"query": "<topic>"}),
                ]),
            ]),
            CompoundTask("read_sources", methods=[
                Method("read_sources", [], [
                    CompoundTask("read_each", methods=[
                        Method("read_each", [], [
                            PrimitiveTask("fetch_url", "fetch_url", {"url": "<source.url>"}),
                            PrimitiveTask("extract_text", "extract_text", {"html": "<fetch_url.result>"}),
                        ]),
                    ]),
                ]),
            ]),
            CompoundTask("synthesize", methods=[
                Method("synthesize", [], [
                    PrimitiveTask("summarize", "llm", {"prompt": "Synthesize: <all_extracted_text>"}),
                ]),
            ]),
        ],
    ),
]

HTN = HTNPlanner(methods=RESEARCH_METHODS, tools=TOOLS)
plan = HTN.plan(CompoundTask("research_topic", []), state={})
# Result: a flat list of primitive tasks in execution order:
# [web_search(topic), db_query(topic), fetch_url(source1), extract_text(html1), fetch_url(source2), extract_text(html2), ..., summarize(all_text)]
```

The pattern that wins interviews is the "HTN for hierarchical tasks" pattern. The candidate who says "I use HTN when the task naturally decomposes into recursive structure — research a topic is a tree (search, read, summarize), each of which is a sub-tree. I use PaE when the task is linear — book a flight is a list (search, compare, book). The plan tree is human-readable, which is valuable for customer-facing explanations. The wrong choice is HTN for a linear workflow (3× plan generation cost). The wrong choice is PaE for a hierarchical task (too rigid). The right choice is HTN when the task is recursive" is the candidate who demonstrates the planning-mindset.

## Code or example

The HTN vs PaE decision rubric:

```python
def pick_planning_pattern(task: dict) -> str:
    """Pick HTN or PaE based on the task's structure."""
    recursion_depth = task.get("recursion_depth", 1)
    plan_dynamism = task.get("plan_dynamism", "low")  # low | medium | high
    plan_interpretability = task.get("plan_interpretable", False)
    plan_generation_cost_tolerance = task.get("plan_cost_tolerance", "low")  # low | medium | high

    if recursion_depth >= 2 and plan_interpretability:
        return "htn"
    if plan_dynamism == "high" and plan_generation_cost_tolerance == "high":
        return "htn_with_replanning"
    if recursion_depth == 1 and plan_dynamism == "low":
        return "plan_and_execute"
    return "plan_and_execute"  # default
```

The HTN use cases (where HTN fits):

```python
# Use case 1: Multi-document research
# Task: "Research the impact of AI on logistics in 2026"
# Tree: research_topic -> [identify_sources -> [web_search, db_query], read_sources -> [read_each -> [fetch, extract]], synthesize -> [summarize]]
# Plan: 7+ primitive tasks in a tree structure. PaE would force a flat list; HTN captures the recursion.

# Use case 2: Multi-week project planning
# Task: "Plan a 4-week customer onboarding engagement"
# Tree: plan_engagement -> [week_1 -> [...], week_2 -> [...], week_3 -> [...], week_4 -> [...]]
# Plan: 20+ primitive tasks in a tree structure.

# Use case 3: NOT HTN: Book a flight
# Task: "Book a flight from SFO to HKG on 2026-11-01"
# List: [search_flights, compare_prices, select_flight, enter_passenger_info, pay, confirm]
# Plan: 6 primitive tasks in a flat list. PaE is sufficient; HTN is over-engineering.
```

The HTN execution trace (for debugging):

```python
def execute_htn_plan(plan: list[PrimitiveTask], tools: dict, state: dict) -> dict:
    """Execute the primitive tasks in order. Returns the trace."""
    trace = []
    for i, task in enumerate(plan):
        trace.append({"step": i, "task": task.name, "tool": task.tool, "args": task.args})
        try:
            result = tools[task.tool](task.args)
            trace[-1]["result"] = result
            trace[-1]["status"] = "success"
            state[task.name + "_result"] = result
        except Exception as e:
            trace[-1]["status"] = "failed"
            trace[-1]["error"] = str(e)
            raise  # HTN fails fast
    return {"trace": trace, "final_state": state}
```

## Production addendum

The HTN question is the answer to "when do you need a hierarchical plan." The 60-second script:

> "HTN for hierarchical tasks where the plan is a tree, not a list. Recursive sub-plans for tasks like multi-document research (research → search + read + summarize, where read → fetch + extract). **The 4 axes: recursion depth, plan dynamism, plan interpretability, plan generation cost.** Use HTN when recursion depth ≥ 2 and the plan needs to be human-readable (customer-facing explanations). Use PaE when the task is linear (book a flight, file a tax return). The wrong choice is HTN for a linear workflow (3× plan generation cost). The wrong choice is PaE for a hierarchical task (too rigid to capture the recursion). The right choice is HTN when the task is recursive and the plan needs to be interpretable."

This is the difference between a candidate who says "I planned the task" and a candidate who says "HTN for hierarchical tasks (research, multi-week projects); PaE for linear workflows (book a flight, file a tax return); the plan tree is human-readable, valuable for customer-facing explanations." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/hardcode/level-5-agentic-workflows/10-multi-agent-orchestrator.py` — the production HTN pattern.
- **Reference implementation**: `course/practice/level-5-agents/lesson-9-4-langgraph.py` — the LangGraph StateGraph with hierarchical nodes.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the planning loop.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the orchestrator uses HTN-like decomposition for complex cases.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — HTN as a system design pattern.

## The 3 questions this lecture preps you for

1. **"When do you need a hierarchical plan?"** Answer: when the task naturally decomposes into recursive structure — research a topic is a tree (search, read, summarize), each of which is a sub-tree. Use HTN when recursion depth ≥ 2 and the plan needs to be human-readable.
2. **"What are the 3 components of the HTN pattern?"** Answer: (1) compound tasks (decomposable into sub-tasks), (2) primitive tasks (executable directly by a tool call), (3) methods (decomposition rules that say "to accomplish X, decompose into [Y1, Y2, ...]"). The planner selects a method for each compound task based on the current state; the executor dispatches primitive tasks.
3. **"What is the difference between HTN and plan-and-execute?"** Answer: HTN is a tree; PaE is a list. HTN captures recursive sub-plans; PaE is a flat sequence. HTN is more expressive (3× plan generation cost); PaE is simpler and cheaper. Use HTN for hierarchical research and multi-week projects; use PaE for linear workflows like book-a-flight or file-a-tax-return.

## Read next

`L5-6-the-human-in-the-loop-pattern.md` — the sixth and final pattern. The human-in-the-loop pattern is the safety net for irreversible side effects. The agent pauses for approval before sending an email, moving money, or deleting data. The right pattern when the cost of a wrong action exceeds the cost of a human review.