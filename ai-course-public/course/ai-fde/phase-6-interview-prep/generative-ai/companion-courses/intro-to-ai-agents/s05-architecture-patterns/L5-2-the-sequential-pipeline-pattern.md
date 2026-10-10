# L5.2: The sequential pipeline pattern

> **FDE framing in one line:** the sequential pipeline is agent A's output is agent B's input. For workflows with clear handoffs (research → summarize → translate), the pipeline is simpler than the orchestrator but more rigid. The FDE picks pipeline when the handoffs are deterministic and the data flow is unidirectional.

## The 3 things you'll learn

1. The 3 properties of the pipeline pattern: unidirectional data flow, deterministic handoffs, no shared state.
2. The 4-axis pipeline-vs-orchestrator rubric: dynamism, parallelism, handoff determinism, error recovery.
3. The "pipeline for ETL-shaped work, orchestrator for control-shaped work" rule of thumb.

## Concept

The sequential pipeline is the simplest multi-agent pattern. Agent A processes the input, produces an output; Agent B receives that output, processes it, produces the next output; Agent C receives that output, and so on. The data flows in one direction; the handoffs are deterministic; the agents do not share state. **The pipeline is the right pattern when the workflow is ETL-shaped (extract → transform → load) and the handoffs are predictable.**

The 3 properties of the pipeline pattern:

1. **Unidirectional data flow.** Agent A's output is Agent B's input. The data flows left-to-right; there is no feedback loop. This makes the pipeline easy to reason about: each agent's input is well-defined; each agent's output is well-defined; the composition is a function composition.
2. **Deterministic handoffs.** The handoff from A to B is triggered by A completing its task, not by B deciding to ask A. This means the workflow is predictable: A always runs first, B always runs second, C always runs third. There is no orchestrator deciding the order.
3. **No shared state.** Each agent has its own memory, its own tool list, its own cost ceiling. The only data passed between agents is the output of the previous agent. This means agents cannot see each other's context; they cannot correct each other's errors; they cannot collaborate beyond the data handoff.

The 4-axis pipeline-vs-orchestrator rubric:

1. **Dynamism.** Does the workflow change based on intermediate results? No → pipeline. Yes → orchestrator.
2. **Parallelism.** Can sub-tasks run concurrently? No (sequential dependency) → pipeline. Yes → parallel fan-out (L5.4) or orchestrator.
3. **Handoff determinism.** Is the next agent always known? Yes → pipeline. No (depends on the previous output) → orchestrator.
4. **Error recovery.** Can a downstream agent recover from an upstream error? No → pipeline (the error propagates). Yes → orchestrator (the orchestrator can replan).

The "pipeline for ETL-shaped work, orchestrator for control-shaped work" rule of thumb is the FDE's primary design heuristic. ETL-shaped work (extract data, transform it, load it) is sequential, deterministic, and unidirectional; the pipeline is the right pattern. Control-shaped work (decide what to do based on intermediate results, dispatch to the right sub-agent, replan on errors) is dynamic, parallel, and feedback-driven; the orchestrator is the right pattern.

## The pattern

The sequential pipeline, as a class:

```python
from typing import Callable

class Pipeline:
    """Sequential pipeline: agent A's output is agent B's input."""

    def __init__(self, agents: list[Callable]):
        """agents: [agent_a, agent_b, agent_c, ...]"""
        self.agents = agents

    def run(self, input: any) -> any:
        """Run the pipeline. Each agent transforms the previous output."""
        data = input
        trace = []
        for i, agent in enumerate(self.agents):
            try:
                data = agent(data)
                trace.append({"agent": i, "input_size": len(str(input)), "output_size": len(str(data)), "status": "success"})
            except Exception as e:
                trace.append({"agent": i, "status": "failed", "error": str(e)})
                raise  # Pipeline fails fast on error
        return {"result": data, "trace": trace}
```

The canonical research-summarize-translate pipeline:

```python
def research_agent(query: str) -> dict:
    """Extract: search the web for the query, return top 5 results."""
    return {"query": query, "results": web_search(query, top_k=5)}

def summarize_agent(research: dict) -> dict:
    """Transform: summarize the research into 3 bullet points."""
    summary = llm(f"Summarize these results in 3 bullets: {research['results']}")
    return {"query": research["query"], "summary": summary}

def translate_agent(summary: dict, lang: str = "vi") -> dict:
    """Load: translate the summary to Vietnamese."""
    translation = llm(f"Translate to {lang}: {summary['summary']}")
    return {"query": summary["query"], "summary": summary["summary"], "translation": translation}

PIPELINE = Pipeline([research_agent, summarize_agent, translate_agent])
result = PIPELINE.run("PacificFreight Q3 2026 revenue")
# Result: {query, summary, translation}
```

The pattern that wins interviews is the "pipeline for ETL-shaped work" pattern. The candidate who says "I use a pipeline when the workflow is sequential, deterministic, and unidirectional — research → summarize → translate. I use an orchestrator when the workflow is dynamic, parallel, and feedback-driven — multi-role dispatch with replanning. The wrong choice is an orchestrator for a 3-step ETL (over-engineering). The wrong choice is a pipeline for a multi-role workflow (rigid, no error recovery). The right choice is pipeline for ETL, orchestrator for control" is the candidate who demonstrates the architecture-mindset.

## Code or example

The pipeline vs orchestrator decision rubric:

```python
def pick_pattern(workflow: dict) -> str:
    """Pick pipeline or orchestrator based on the workflow's structure."""
    dynamism = workflow.get("dynamism", "low")  # low | medium | high
    parallelism = workflow.get("parallelism", False)
    handoff_determinism = workflow.get("handoff_deterministic", True)
    error_recovery = workflow.get("error_recovery_needed", False)

    if dynamism == "low" and not parallelism and handoff_determinism and not error_recovery:
        return "pipeline"
    if parallelism:
        return "parallel_fanout"  # L5.4
    if dynamism in ("medium", "high") or not handoff_determinism or error_recovery:
        return "orchestrator"  # L5.3
    return "pipeline"  # default
```

The PacificFreight pipeline use cases (where pipeline fits):

```python
# Use case 1: Email → Intent classification → Route to the right queue
PIPELINE_1 = Pipeline([
    lambda email: parse_email(email),  # Extract: parse the email into structured fields
    lambda parsed: classify_intent(parsed),  # Transform: classify the intent
    lambda intent: route_to_queue(intent),  # Load: route to the CS, ops, or cost queue
])
# Workflow: 3 steps, sequential, deterministic, no parallelism, no error recovery needed.

# Use case 2: Shipment data → Status report → Customer-friendly email
PIPELINE_2 = Pipeline([
    lambda shipment_id: fetch_shipment(shipment_id),  # Extract
    lambda shipment: generate_status_report(shipment),  # Transform
    lambda report: render_customer_email(report),  # Load
])
# Workflow: 3 steps, sequential, deterministic. The output of each step is the input to the next.

# Use case 3: Multi-shipment case → NOT a pipeline
# Why: the orchestrator decides which sub-agents to dispatch based on the case structure.
# A pipeline would force a fixed order; the orchestrator allows dynamic dispatch.
```

The pipeline failure mode (the FDE's anti-pattern):

```python
# Anti-pattern: pipeline with feedback
PIPELINE_WITH_FEEDBACK = Pipeline([
    agent_a,
    lambda x: agent_b(x) if check_quality(x) else agent_a(x),  # BAD: feedback loop in a pipeline
])
# The pipeline is no longer deterministic. The handoff depends on the intermediate result.
# This is an orchestrator in disguise; use the orchestrator pattern instead.
```

## Production addendum

The pipeline question is the answer to "when do you use a pipeline vs a loop." The 60-second script:

> "Pipeline for ETL-shaped work: sequential, deterministic, unidirectional. Orchestrator for control-shaped work: dynamic, parallel, feedback-driven. **The pipeline is 3 properties: unidirectional data flow, deterministic handoffs, no shared state.** Use the pipeline for research → summarize → translate; for email → classify → route; for data fetch → report → render. Use the orchestrator for multi-role dispatch with replanning. The wrong choice is an orchestrator for a 3-step ETL (over-engineering, 3× cost). The wrong choice is a pipeline for a multi-role workflow (rigid, no error recovery). The right choice is pipeline for ETL, orchestrator for control. The pipeline is implemented as a list of callables; the orchestrator is a state machine with conditional branches."

This is the difference between a candidate who says "I chained some agents" and a candidate who says "pipeline for ETL-shaped work (unidirectional, deterministic, no shared state); orchestrator for control-shaped work (dynamic, parallel, feedback-driven)." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-2-crewai.py` — the sequential pipeline pattern.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/10-multi-agent-orchestrator.py` — the production pipeline with error handling.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the pipeline as a control-flow primitive.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the orchestrator is the more flexible pattern when the pipeline is too rigid.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — pipeline as a system design pattern.

## The 3 questions this lecture preps you for

1. **"When do you use a pipeline vs a loop?"** Answer: pipeline for sequential, deterministic, unidirectional workflows (ETL-shaped: research → summarize → translate). Loop for dynamic, feedback-driven workflows (control-shaped: investigate → decide → act → observe). The pipeline is implemented as a list of callables; the loop is the single-agent pattern from L5.1.
2. **"What are the 3 properties of the pipeline pattern?"** Answer: (1) unidirectional data flow (agent A's output is agent B's input), (2) deterministic handoffs (the next agent is always known), (3) no shared state (each agent has its own memory and tool list). The pipeline is easy to reason about; the orchestrator is more flexible.
3. **"When do you escalate from pipeline to orchestrator?"** Answer: when the workflow becomes dynamic (the next agent depends on the previous output), parallel (sub-tasks can run concurrently), or error-recovery (a downstream agent needs to recover from an upstream error). The pipeline is too rigid for these cases; the orchestrator is the more flexible pattern.

## Read next

`L5-3-the-orchestrator-pattern.md` — the third pattern. The orchestrator + sub-agents is the FDE's default multi-agent pattern. The supervisor dispatches; the workers execute; the orchestrator synthesizes. Per-agent circuit breakers mean a Mei failure does not block Daniel.