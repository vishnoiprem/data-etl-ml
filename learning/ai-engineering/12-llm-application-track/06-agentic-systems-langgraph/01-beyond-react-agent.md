# Lesson 1 — The Agent Loop, Beyond ReAct

> **Type:** Article + Worked Example · Course 6
> Why ReAct is the demo, not the system. And how LangGraph's stateful graphs let you build agents that actually ship.

---

## The ReAct ceiling

ReAct (Course 5) is the canonical agent loop:
```
   reason → act → observe → reason → act → observe → ... → answer
```

It works for demos. It breaks in production for four reasons:

| Failure | Why ReAct fails |
|---|---|
| **Long-running workflows** | ReAct agents are stateless — they can't resume after a crash |
| **Cycles with planning** | ReAct interleaves thinking and acting; no clean "plan first, then act" |
| **Human approval gates** | ReAct has no pause-and-wait primitive |
| **Multi-step state** | ReAct passes strings around; real systems need typed state |

LangGraph fixes all four by treating the agent as a **stateful graph**.

---

## The mental model shift

```
   REACT (chain-shaped)                          LANGGRAPH (graph-shaped)
   ────────────────────                          ────────────────────────
   messages: [user, ai, tool, ai, tool, ...]      state: {messages, plan, artifacts, ...}
   loop: max_iterations                           loop: cycle until should_continue()
   no persistence                                  persistence: checkpoint at every node
   no HIL                                          HIL: interrupt + resume
   no cycles-with-planning                         plan node → action nodes → reflection node
   error = exception                               error = routed to error_handler node
```

The **state** is the key abstraction. Every node reads the state, mutates it, and returns it. The graph routes on state. Cycles are explicit. Persistence is built in.

---

## The state graph in one diagram

```
   ┌────────────────────────────────────────────────────────────────┐
   │  RESEARCH AGENT (LangGraph)                                     │
   │                                                                │
   │           ┌──────────────┐                                      │
   │     ┌────►│   PLANNER    │  decompose query into steps        │
   │     │     └──────┬───────┘                                      │
   │     │            │                                              │
   │     │            ▼                                              │
   │     │     ┌──────────────┐                                      │
   │     │     │  RETRIEVER   │  search knowledge base              │
   │     │     └──────┬───────┘                                      │
   │     │            │                                              │
   │     │            ▼                                              │
   │     │     ┌──────────────┐                                      │
   │     │     │  SYNTHESIZER │  draft answer from retrieved docs   │
   │     │     └──────┬───────┘                                      │
   │     │            │                                              │
   │     │            ▼                                              │
   │     │     ┌──────────────┐                                      │
   │     │     │  CRITIC      │  is the answer good enough?         │
   │     │     └──────┬───────┘                                      │
   │     │            │                                              │
   │     │   ┌────────┼─────────┐                                    │
   │     │   │ good   │ needs   │                                    │
   │     │   │        │ work    │                                    │
   │     │   ▼        ▼         │                                    │
   │     │ ┌──────┐ ┌────────┐  │                                    │
   │     │ │ DONE │ │ RETRY  │──┘ (loop back to RETRIEVER)          │
   │     │ └──────┘ └────────┘                                      │
   │     │                                                           │
   │     └────── all steps done → loop back to PLANNER              │
   │                                                                │
   └────────────────────────────────────────────────────────────────┘
```

Notice:
- The **CRITIC → RETRY** edge is a cycle (ReAct can't express this cleanly).
- The **plan → retrieve → synthesize → critic** is a typed pipeline.
- Each node has a single responsibility and a typed input/output.

---

## The three primitives every LangGraph app uses

```
   1. STATE        — TypedDict (or Pydantic) describing the workflow state
   2. NODES        — Functions that take state and return partial state
   3. EDGES        — Routes between nodes, can be conditional
```

That's it. Build a graph by defining state, nodes, and edges. Compile. Run.

---

## Worked Example — research agent with cycles, HIL, persistence

> **Goal:** A research agent that takes a question, plans sub-questions, retrieves docs for each, synthesizes an answer, critiques it, and (if not good enough) iterates. With human approval for high-stakes queries and checkpoint persistence for resumability.

### Step 1 — Define state

```python
# agent/state.py
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class ResearchState(TypedDict):
    # Conversation
    messages: Annotated[list, add_messages]

    # Plan
    original_query: str
    sub_questions: list[str]
    current_step: int

    # Retrieved evidence
    sources: dict[str, list[dict]]   # {step_idx: [docs]}

    # Draft + critique
    draft_answer: str
    critique: str
    iteration_count: int

    # Approval
    needs_human_approval: bool
    approved: bool

    # Final
    final_answer: str
```

`add_messages` is a reducer that appends new messages to the existing list. Other fields are replaced on each node return.

### Step 2 — Define nodes

```python
# agent/nodes.py
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

model = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)

def planner_node(state: ResearchState) -> dict:
    """Decompose the query into 3-5 sub-questions."""
    if not state.get("sub_questions"):
        response = model.invoke([
            SystemMessage(content="Decompose the user's research question into 3-5 sub-questions. Return a JSON list."),
            HumanMessage(content=state["original_query"]),
        ])
        sub_questions = json.loads(response.content)
        return {
            "sub_questions": sub_questions,
            "current_step": 0,
        }
    return {}

def retriever_node(state: ResearchState) -> dict:
    """Retrieve docs for the current sub-question."""
    step = state["current_step"]
    sub_q = state["sub_questions"][step]
    docs = retriever.invoke(sub_q)         # Course 4 retriever
    sources = state.get("sources", {})
    sources[str(step)] = [d.dict() for d in docs]
    return {"sources": sources}

def synthesizer_node(state: ResearchState) -> dict:
    """Draft an answer from the retrieved sources."""
    all_sources = state.get("sources", {})
    context = format_sources(all_sources)
    response = model.invoke([
        SystemMessage(content="Synthesize an answer using ONLY the sources. Cite each claim."),
        HumanMessage(content=f"Question: {state['original_query']}\n\nSources: {context}"),
    ])
    return {"draft_answer": response.content}

def critic_node(state: ResearchState) -> dict:
    """Critique the draft; decide if it's good enough or needs another iteration."""
    response = model.invoke([
        SystemMessage(content="""Critique this draft. Identify:
1. Unsupported claims
2. Missing important angles
3. Over-confidence

Return JSON: {"good_enough": <bool>, "critique": "<text>", "missing_step": <int or null>}
"""),
        HumanMessage(content=f"Draft: {state['draft_answer']}\n\nOriginal query: {state['original_query']}"),
    ])
    parsed = json.loads(response.content)
    new_count = state.get("iteration_count", 0) + 1
    return {
        "critique": parsed["critique"],
        "iteration_count": new_count,
    }

def approval_node(state: ResearchState) -> dict:
    """Decide if this query needs human approval (e.g., it's about a sensitive topic)."""
    sensitive = check_sensitivity(state["original_query"])
    return {"needs_human_approval": sensitive}

def finalize_node(state: ResearchState) -> dict:
    """Mark the answer as final."""
    return {"final_answer": state["draft_answer"]}
```

Each node is a function: takes state, returns a partial state. Pure-ish (side effects limited to retriever calls).

### Step 3 — Define the graph

```python
# agent/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

from .state import ResearchState
from .nodes import (
    planner_node, retriever_node, synthesizer_node,
    critic_node, approval_node, finalize_node,
)

workflow = StateGraph(ResearchState)

# Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("synthesizer", synthesizer_node)
workflow.add_node("critic", critic_node)
workflow.add_node("approval", approval_node)
workflow.add_node("finalize", finalize_node)

# Entry
workflow.set_entry_point("planner")

# Edges — planner fans out, each sub-question goes through retrieve → synthesize
workflow.add_edge("planner", "approval")

def approval_router(state: ResearchState) -> str:
    return "human_review" if state["needs_human_approval"] else "retriever"

workflow.add_conditional_edges(
    "approval",
    approval_router,
    {"human_review": "human_review", "retriever": "retriever"},
)

workflow.add_edge("retriever", "synthesizer")
workflow.add_edge("synthesizer", "critic")

def critic_router(state: ResearchState) -> str:
    """Decide: retry (cycle back) or finalize."""
    if state["iteration_count"] >= 3:
        return "finalize"           # give up after 3 iterations
    if "good_enough" in state.get("critique", "").lower() or state["iteration_count"] >= 1:
        # Check if critic's JSON said good_enough
        return "finalize"
    return "retriever"              # cycle back

workflow.add_conditional_edges(
    "critic",
    critic_router,
    {"retriever": "retriever", "finalize": "finalize"},
)

workflow.add_edge("finalize", END)

# Persistence — checkpoint at every node
memory = MemorySaver()
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_review"],   # HIL gate
)
```

Three things to notice:

1. **Cycles are explicit.** `critic_router` returns `"retriever"` to loop back.
2. **`interrupt_before=["human_review"]`** pauses the graph before that node for human approval.
3. **`checkpointer=memory`** saves state at every node. Resume by passing the same `thread_id`.

### Step 4 — Human-in-the-loop approval

```python
# agent/run_with_hil.py
from agent.graph import app

# Start the research
config = {"configurable": {"thread_id": "research-42"}}
result = app.invoke(
    {"messages": [{"role": "user", "content": "What were the causes of the 2025 Stripe outage?"}],
     "original_query": "What were the causes of the 2025 Stripe outage?",
     "iteration_count": 0},
    config=config,
)

# Graph pauses at human_review. Check the state.
snapshot = app.get_state(config)
print(f"Paused at: {snapshot.next}")
print(f"Needs approval: {snapshot.values['needs_human_approval']}")

# Human approves (or doesn't)
human_approved = input("Approve this research? (y/n): ").strip().lower() == "y"

# Resume
if human_approved:
    app.invoke(None, config=config)        # continue
else:
    app.invoke({"approved": False}, config=config)   # abort
```

The graph pauses. A human reviews. The graph resumes. **This is impossible in ReAct.**

### Step 5 — Persistence and resume

```python
# agent/resume.py
# Suppose the agent crashed mid-run. To resume:

# Look up the thread
config = {"configurable": {"thread_id": "research-42"}}
snapshot = app.get_state(config)
print(f"Last completed node: {snapshot.metadata['step']}")
print(f"Current state: {snapshot.values}")

# Resume from where it stopped
result = app.invoke(None, config=config)
```

State is checkpointed at every node. The graph can be paused, resumed, replayed, or forked — exactly like a database transaction.

### Step 6 — Streaming events

```python
# agent/stream.py
async for event in app.astream_events(
    {"messages": [{"role": "user", "content": "What's the p99 for auth?"}],
     "original_query": "What's the p99 for auth?",
     "iteration_count": 0},
    config={"configurable": {"thread_id": "stream-1"}},
    version="v2",
):
    if event["event"] == "on_chain_start":
        print(f"Entering node: {event['name']}")
    elif event["event"] == "on_llm_stream":
        print(f"  Token: {event['data']['chunk'].content}", end="")
    elif event["event"] == "on_chain_end":
        print(f"Finished node: {event['name']}")
```

Every node entry, every LLM token, every tool call is emitted as an event. The UI gets real-time visibility into what the agent is doing.

### Step 7 — Eval harness

```python
# eval/run_eval.py
from langsmith import evaluate
from agent.graph import app

DATASET = "research-agent.v1"

def completed_in_budget(run, example):
    """Did the agent finish within the iteration budget?"""
    iterations = run.outputs.get("iteration_count", 0)
    return {"key": "within_budget", "score": 1.0 if iterations <= 3 else 0.0}

def has_citations(run, example):
    """Does the final answer cite sources?"""
    final = run.outputs.get("final_answer", "")
    return {"key": "has_citations", "score": 1.0 if "[Source" in final else 0.0}

def answer_quality(run, example):
    """LLM-as-judge on the final answer."""
    return LangChainStringEvaluator(
        "labeled_score_string",
        config={"criteria": {"answer": "Is the answer accurate, complete, and well-sourced?"}, "normalize_by": 5},
    )(run, example)

def critique_usefulness(run, example):
    """Did the critique actually identify a real issue?"""
    return LangChainStringEvaluator(
        "labeled_score_string",
        config={"criteria": {"critique": "Is the critique specific and actionable?"}, "normalize_by": 5},
    )(run, example)

results = evaluate(
    lambda inputs: app.invoke(inputs, config={"configurable": {"thread_id": f"eval-{hash(inputs['original_query'])"}}}),
    data=DATASET,
    evaluators=[completed_in_budget, has_citations, answer_quality, critique_usefulness],
    experiment_prefix="research-agent-v1",
)

assert results["within_budget"]["mean"] >= 0.95, "agent loops too often"
assert results["answer_quality"]["mean"] >= 4.0, "answer quality regressed"
```

Four evaluators cover the four failure modes: runaway loops, missing citations, low quality, useless critiques.

### Step 8 — The supervisor pattern (multi-agent)

For tasks that span multiple domains, swap single-agent for supervisor:

```python
# agent/multi_agent.py
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

# Three specialist agents
research_agent = create_react_agent(model, [search_tool, fetch_tool])
code_agent = create_react_agent(model, [python_repl_tool])
writing_agent = create_react_agent(model, [], state_modifier="You write final reports.")

# Supervisor picks which one to call
supervisor_prompt = """You are a supervisor managing three workers:
1. research_agent: searches the web and fetches documents
2. code_agent: runs Python code
3. writing_agent: writes the final report

Given the user's request, decide which worker to call next, or FINISH.

Return JSON: {"next": "research_agent" | "code_agent" | "writing_agent" | "FINISH", "task": "<description>"}"""

class SupervisorState(TypedDict):
    messages: Annotated[list, add_messages]
    next_worker: str
    task: str
    result: str

def supervisor_node(state: SupervisorState) -> dict:
    response = model.invoke([
        SystemMessage(content=supervisor_prompt),
        HumanMessage(content=json.dumps(state["messages"][-3:])),
    ])
    parsed = json.loads(response.content)
    return {"next_worker": parsed["next"], "task": parsed["task"]}

def worker_dispatch(state: SupervisorState):
    if state["next_worker"] == "research_agent":
        return research_agent.invoke({"messages": [{"role": "user", "content": state["task"]}]})
    elif state["next_worker"] == "code_agent":
        return code_agent.invoke({"messages": [{"role": "user", "content": state["task"]}]})
    elif state["next_worker"] == "writing_agent":
        return writing_agent.invoke({"messages": [{"role": "user", "content": state["task"]}]})
    return {"result": state.get("result", "")}

# Build the supervisor graph
supervisor_graph = StateGraph(SupervisorState)
supervisor_graph.add_node("supervisor", supervisor_node)
supervisor_graph.add_node("worker", worker_dispatch)
supervisor_graph.add_edge("supervisor", "worker")

def should_continue(state: SupervisorState) -> str:
    return END if state["next_worker"] == "FINISH" else "supervisor"

supervisor_graph.add_conditional_edges("worker", should_continue, {END: END, "supervisor": "supervisor"})
supervisor_graph.set_entry_point("supervisor")

multi_agent_app = supervisor_graph.compile(checkpointer=MemorySaver())
```

The supervisor pattern is **the** way to scale beyond a single agent. Each worker is specialized; the supervisor routes.

### Step 9 — When to use what

```
   ┌───────────────────────────────────────────────────────────────┐
   │  DECISION TREE: what orchestration primitive?                │
   │                                                               │
   │  Q: Is the task a single LLM call?                           │
   │  └─► No orchestration needed.                                │
   │                                                               │
   │  Q: Does the task have 2-3 sequential steps?                 │
   │  └─► LCEL chain (Course 1).                                   │
   │                                                               │
   │  Q: Does the task need the model to choose tools?            │
   │  └─► ReAct agent (Course 5).                                  │
   │                                                               │
   │  Q: Does the task have cycles, persistence, or HIL?          │
   │  └─► LangGraph (this course).                                 │
   │                                                               │
   │  Q: Does the task span multiple specialized domains?         │
   │  └─► LangGraph supervisor (this course).                      │
   │                                                               │
   │  Q: Does the task involve external triggers (webhooks, etc)? │
   │  └─► LangGraph + queue + worker (this course, advanced).    │
   └───────────────────────────────────────────────────────────────┘
```

Reach for LangGraph when **any** of these is true: cycles, persistence, HIL, multiple agents, or long-running workflows. For everything else, simpler is better.

### Step 10 — Cost roll-up

```
   At 100 research queries/day, 3K queries/month:
   ──────────────────────────────────────────────
   Planner:      1 Sonnet call × $0.015    = $45/mo
   Retriever:    3 × Cohere embed × $0.001  = $9/mo
   Synthesizer:  3 × Sonnet call × $0.015  = $135/mo
   Critic:       3 × Sonnet call × $0.015  = $135/mo
   LangSmith:                            $50/mo
   ─────────────────────────────────────
   Total: ~$374/mo for 3K queries = $0.125/query

   vs. hiring an analyst at $5K/mo who can do ~50 queries
   → agent is ~250× cheaper and 24/7.
```

The supervisor pattern is more expensive (multiple agents) but is the only way to handle multi-domain tasks.

### What this example demonstrates

1. **LangGraph is for stateful cycles.** ReAct is the demo; LangGraph is the system.
2. **HIL via `interrupt_before`.** Pause the graph, get approval, resume. Impossible in ReAct.
3. **Persistence via checkpointing.** Long-running workflows that survive crashes.
4. **The supervisor pattern for multi-agent.** Each worker is specialized; the supervisor routes.
5. **Eval catches loop runaway.** The `within_budget` evaluator is the one most teams miss.

Read this example and you understand agentic systems at production scale. Read it twice and you understand how to defend every architectural choice.

---

## What Comes Next

> Lesson 2 — **State & persistence** — checkpointers (Memory, SQLite, Postgres), time-travel debugging, and the queue-backed long-running pattern.
