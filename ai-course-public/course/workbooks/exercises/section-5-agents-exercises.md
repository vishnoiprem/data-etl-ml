# Codebook Exercises — Section 5: Agent Patterns

> **Paired exercises for [`../ai-engineer-codebook.md` § 5](../ai-engineer-codebook.md#section-5-agent-patterns).**
> These turn reference snippets into active practice. For each reference snippet in the codebook, here are 3-5 challenges that force you to modify, extend, and break the code.

---

## How to use these

1. Open the reference snippet in [`../ai-engineer-codebook.md`](../ai-engineer-codebook.md) — Section 5 (Agent Patterns)
2. Read the snippet once
3. Do the exercises below IN ORDER — each builds on the previous
4. For each exercise, build the agent component, run it, note what you learned

**Time per exercise:** 25-40 min.
**Total time for this section:** 6-8 hours.

---

## Snippet 5.1 — ReAct Agent (Full Implementation)

**Reference:** [`../ai-engineer-codebook.md#51-react-agent-full-implementation`](../ai-engineer-codebook.md#51-react-agent-full-implementation)

### Exercise 5.1.1: Add a max-iteration guard

```python
# TODO: ReAct agents can loop forever. Add:
# - max_iterations (e.g., 10)
# - same-action detection: if same tool+args appear 3 times in a row, abort
# - logging of every iteration
# Test: give the agent a tool that always returns empty. Verify it doesn't loop.
```

### Exercise 5.1.2: Tool budget per session

```python
# TODO: Each session gets a budget (e.g., 20 tool calls).
# Decrement per call. If budget hits 0, return best-effort final answer.
# Useful for cost control. Track: average tool calls per task.
```

### Exercise 5.1.3: Parallel tool calls

```python
# TODO: When the agent decides to call 2+ tools that don't depend on each other, call them in parallel.
# Use asyncio.gather. Verify: total time = max(tool_times), not sum.
# This is what GPT-4o does natively with parallel function calls.
```

### Exercise 5.1.4: Human-in-the-loop

```python
# TODO: Before executing a "destructive" tool (delete, send, pay), pause and ask a human.
# Use the input() prompt or a web UI approval.
# Test: agent tries to call send_email(). Verify it waits.
```

---

## Snippet 5.2 — Multi-Agent with CrewAI

**Reference:** [`../ai-engineer-codebook.md#52-multi-agent-with-crewai`](../ai-engineer-codebook.md#52-multi-agent-with-crewai)

### Exercise 5.2.1: 2-agent writer + critic

```python
# TODO: Build a CrewAI workflow with:
# - Agent 1: Writer (writes a blog post on a topic)
# - Agent 2: Critic (reviews the post, suggests 3 improvements)
# - Loop 3 times: writer revises based on critic feedback
# Compare: 1-shot vs 3-iteration. Quality? Cost?
```

### Exercise 5.2.2: Researcher + writer + editor

```python
# TODO: 3 agents in sequence:
# - Researcher: searches the web, gathers facts
# - Writer: drafts an article from research
# - Editor: refines for tone, clarity, length
# Each agent has a different role and goal. Define the handoff clearly.
```

### Exercise 5.2.3: When to use multi-agent vs single agent

```python
# TODO: Same task with both architectures. Measure:
# - Quality (LLM-as-judge)
# - Cost (total tokens)
# - Latency (sequential vs parallel)
# Multi-agent is NOT always better. It adds orchestration overhead.
```

---

## Snippet 5.3 — LangGraph Workflow

**Reference:** [`../ai-engineer-codebook.md#53-langgraph-workflow`](../ai-engineer-codebook.md#53-langgraph-workflow)

### Exercise 5.3.1: Add conditional routing

```python
# TODO: Build a graph:
# - Node A: classify the query
# - If simple -> Node B (cheap model)
# - If complex -> Node C (expensive model)
# - Both -> Node D (return answer)
# LangGraph's add_conditional_edges makes this trivial.
```

### Exercise 5.3.2: Add a loop with a counter

```python
# TODO: "Refine until good" pattern:
# - Node A: generate draft
# - Node B: evaluate (LLM-as-judge)
# - If score < 8/10, go back to A with feedback
# - Max 3 iterations
# - Either way, return the best draft seen
# This is how you build self-refining agents.
```

### Exercise 5.3.3: Human-in-the-loop node

```python
# TODO: Add a node that calls interrupt() to pause for human approval.
# After approval, resume from the next node.
# Use LangGraph's persistence (checkpoints) so the state survives the pause.
```

### Exercise 5.3.4: Sub-graphs

```python
# TODO: Build a "research sub-graph" (search + scrape + summarize) as a single node.
# Then the main graph uses it. Like composing functions.
# This is how you build complex agents from simple ones.
```

### Exercise 5.3.5: Streaming a LangGraph run

```python
# TODO: Stream events from a running graph:
# - "node_started", "node_completed", "token", "done"
# Subscribe to the event stream. Useful for progress UIs.
```

---

## Cross-cutting challenges (Mid+)

### Challenge A: Plan-and-execute vs ReAct

```python
# TODO: Build the same research task with two architectures:
# 1. ReAct: think-act-observe loop
# 2. Plan-and-execute: plan all sub-tasks first, then execute sequentially
# Measure: quality, cost, latency, debug-ability.
# Plan-and-execute is usually cheaper and more debuggable, but less flexible.
```

### Challenge B: Build a tool registry

```python
# TODO: Centralize tool definitions:
# - Each tool has: name, description, schema, executor, cost_estimate
# - Tools are registered dynamically (e.g., load from a config file)
# - The agent discovers available tools via the registry
# - Adding a new tool = one entry, no agent code change
```

### Challenge C: Agent observability

```python
# TODO: For every agent run, log:
# - the full trace (every LLM call, every tool call, every state transition)
# - the final outcome
# - cost, latency, tool count
# Visualize in a UI (LangSmith, Helicone, or your own).
# This is non-negotiable for production agents.
```

---

## Architect-level reflections (Senior+)

After completing these exercises, write a 1-page design doc answering:

1. **ReAct vs plan-and-execute?** (when to use which)
2. **Multi-agent: when does it pay off?** (rule of thumb: >3 distinct roles, or quality > 1.5x with cost ignored)
3. **LangGraph vs raw ReAct?** (state graph vs imperative loop)
4. **Tool budget per task?** (cost cap, latency cap, or both)
5. **Max iterations per agent?** (5? 10? 20?)
6. **How do you detect agent loops?** (same tool+args N times, or wall-clock timeout)
7. **When do you add human-in-the-loop?** (destructive actions, low confidence, $$$)
8. **How do you test agents?** (deterministic fixtures? recorded traces? LLM-as-judge?)
9. **How do you observe them in prod?** (LangSmith, Helicone, custom logging)
10. **When do you switch from agent to pipeline?** (if the steps are known and stable, hard-code them)

Save these answers. Agents are the most powerful AND most error-prone AI pattern. Treat them with respect.

---

## What's next

- Pair with [`../../practice/level-5-agents/`](../../practice/level-5-agents/) for the deeper labs
- Move to `section-6-vector-db-exercises.md` for vector DB patterns
- See [`../../PRACTICE-GUIDE.md`](../../PRACTICE-GUIDE.md) for the full learning path