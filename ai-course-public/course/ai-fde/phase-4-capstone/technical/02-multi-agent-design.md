# Lesson T2 — Multi-agent design: when to split, how to share state

> **Phase 4, Technical Track, Lesson 2.** When a single-agent
> drafter breaks down, and how to design a multi-agent
> orchestrator that respects the same operational boundaries
> (rate limit, breaker, redaction) as the underlying agents.

## 🎯 Outcome

By the end of this lesson you can:

- **Recognize** when a single-agent design has hit its limits (the
  signs are: copy/paste between tools, the user clicking 5 buttons
  per case, the prompt growing past 2k tokens).
- **Decompose** a multi-step workflow into sub-agents with disjoint
  output fields and a shared state object.
- **Wire** the agents together with a hand-rolled state machine
  (~50 lines) and per-agent circuit breakers.
- **Decide** when LangGraph adds value (graph cycles, parallel
  branches, human-in-the-loop) and when it doesn't (a simple
  linear pipeline).

## 🧠 Mindset

A single-agent design works for **simple, well-bounded tasks**:
- "Take this email and draft a reply."
- "Take this question and write a SQL query."
- "Take this code and explain it."

A single-agent design **breaks down** when:
- The task has **multiple audiences** (CS, ops, IT) that need
  different output formats.
- The task has **multi-step reasoning** that doesn't fit in one
  prompt.
- The task has **multi-modal outputs** (a draft AND a summary
  AND a cost note).
- The user is **copy-pasting between tools** to complete a
  single case.

The PacificFreight CS team hit all four in Week 11. Mei was
handling a 3-shipment email that required:
1. Looking up each shipment's status (3 calls to the tracker)
2. Drafting a reply that mentioned each status
3. Noting that 2 of 3 were held at customs (an ops concern)
4. Estimating the cost of this exchange (an IT concern)

The single-agent drafter could do step 1-2. Steps 3-4 required Mei
to **manually copy the results into a separate document** and
**manually compute the cost from the LLM logs.** The 5-button
workflow is the symptom. The fix is a multi-agent orchestrator.

**The lesson:** a multi-agent design is a *decomposition* of the
task into 3-4 sub-tasks, each with a clear input, a clear output,
and a clear "I failed" signal. The orchestrator's job is to call
them in order and to share the state. The interesting code is in
the agents, not the orchestrator.

## 🛠️ Practice

You are extending the PacificFreight multi-agent dispatcher with a
4th agent: `LegalAgent`. Mei has noticed that some customer
emails mention GDPR (European customers) or PIPL (Chinese
customers), and the team's policy is to escalate these to the
legal team for review. You do this in 3 steps:

### Step 1 — Subclass `Agent`

Open `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/service/agents.py`
and add:

```python
class LegalAgent(Agent):
    """Legal lane — flags GDPR/PIPL mentions and produces a compliance note."""
    name = "legal"

    def execute(self, state: DispatcherState) -> DispatcherState:
        # Check for compliance triggers
        triggers = []
        if re.search(r"\bGDPR\b|\bEurope(an)?\b", state.email_body, re.I):
            triggers.append("GDPR")
        if re.search(r"\bPIPL\b|\bChina|Chinese\b", state.email_body, re.I):
            triggers.append("PIPL")
        if triggers:
            state.legal_check = (
                f"⚖️  compliance review needed: {', '.join(triggers)}. "
                f"Forwarded to legal@pf.com for sign-off before sending the reply."
            )
            state.risk_level = "high"
            state.append_trace(self.name, ok=True, triggers=triggers)
        else:
            state.legal_check = "(no compliance triggers)"
            state.append_trace(self.name, ok=True, triggers=[])
        state.agent_path.append(self.name)
        return state
```

That's ~20 lines.

### Step 2 — Add a field to the shared state

Open `service/agents_state.py` and add one line to the dataclass:

```python
@dataclass
class DispatcherState:
    # ... existing fields ...
    legal_check: Optional[str] = None   # ← add this
```

That's 1 line.

### Step 3 — Add a routing rule in the orchestrator

Open `service/agents.py` and add a routing rule in `Dispatcher.dispatch()`:

```python
def dispatch(self, email, ...):
    state = ...
    state = self.breaker.call(self._run_mei, state)

    # NEW: run LegalAgent if the email mentions GDPR or PIPL
    if not state.error and re.search(r"\bGDPR\b|\bPIPL\b", email, re.I):
        state = self.breaker.call(self._run_legal, state)

    if not state.error and len(state.shipment_ids) > 1:
        state = self.breaker.call(self._run_sarah, state)
    if not state.error:
        state = self.breaker.call(self._run_daniel, state)
    # ...
```

And add the per-agent runner:

```python
def _run_legal(self, state: DispatcherState) -> DispatcherState:
    return self.legal.run(state)
```

That's 6 lines (2 if you count only the new logic).

### Step 4 — Test

The 3 existing tests still pass (the change is additive). To verify
the new agent:

```python
import sys
sys.path.insert(0, "course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/service")
sys.path.insert(0, "course/ai-fde/phase-3-capstone/projects/01-mcp-drafter/service")
import agents

d = agents.Dispatcher()
state = d.dispatch(
    "I'm a European customer. Can you tell me what data you hold about me? (GDPR request)",
    user_id="alice@pf.com", role="cs_senior",
)
assert "legal" in state.agent_path
assert state.legal_check is not None
assert "GDPR" in state.legal_check
assert state.risk_level == "high"
```

The 3 existing agents didn't change. The orchestrator added 4 lines.
The state added 1 line. The LegalAgent is a 20-line subclass. **That's
the lesson:** new behavior enters the system through the routing
rules, not through the existing agents.

## 🏛️ FDE Lens

**Why a hand-rolled state machine, not LangGraph?** The Project 2
orchestrator is ~50 lines: 3 agents, 1 shared state, and 3 routing
rules. LangGraph would add 200+ lines of framework code for a
problem that's "call A, then maybe B, then always C." The
hand-rolled version is easier to read, easier to test, and easier
to extend.

**When does LangGraph add value?** When you need:
- **Graph cycles** (the agent can re-try a step based on a result)
- **Parallel branches** (run A and B in parallel, then merge)
- **Human-in-the-loop** (pause for a human to approve before continuing)
- **Persistent state across calls** (the state survives between API calls)

None of these apply to the PacificFreight multi-shipment case. The
agents run in a fixed order; the state is in-process and short-lived;
no human approval is needed. **Use LangGraph when the orchestration
topology is the interesting part of the problem. Use a hand-rolled
state machine when the agents are the interesting part.**

**Why per-agent circuit breakers?** The orchestrator has a parent
breaker; each agent has its own. If Mei's breaker trips (because
the LLM is down), Daniel still runs and emits the cost/risk note.
If Daniel's breaker trips (because something in his code raises),
Mei and Sarah's output is still in `state.mei_draft` and
`state.sarah_summary`. The parent breaker only trips if the
orchestrator itself fails (e.g., a bug in the routing rules).

**The pattern is:** every layer has its own breaker. The LLM has
one (Phase 3's `CircuitBreaker` in `service/circuit.py`). The MCP
server has one (the rate limiter, which is a degenerate breaker).
Each agent has one. The orchestrator has one. A failure at one
layer doesn't cascade.

**Why is the state object a dataclass, not a dict?** A dict has
no schema. The first time an agent writes `state["meiDraft"]` (camelCase)
instead of `state["mei_draft"]` (snake_case), the orchestrator
silently drops the data. A dataclass catches that at the moment
of assignment (AttributeError on a missing field), not deep in a
prompt construction. The state is the **contract between agents**;
a typed contract is more enforceable than an untyped one.

**What about shared state across calls?** Phase 4 has no Redis.
The state is in-process and short-lived. In Phase 5 (production),
the state would be a Redis hash keyed on `request_id`, with a
TTL of 1 hour (so a stuck orchestrator doesn't accumulate
state forever). The `agents_state.py::DispatcherState` dataclass
stays the same; only the storage layer changes.

**Why an audit log (the `trace` field)?** Every append to
`state.trace` is one event in the orchestrator's lifecycle. The
log goes into `usage.jsonl` (Phase 3's audit log) and feeds the
on-call dashboard. When Mei asks "why did this email take 8
seconds?", the trace shows: `mei (3.2s) → sarah (1.8s) → daniel
(0.4s)` — 3 tool calls, 1 risk escalation, 0 errors. The trace
is the **first thing you look at when something goes wrong.**

## 🌙 Reflect

- **What's the difference between an agent and a function?** A
  function is a transformation. An agent is a transformation that
  has its own state, its own breaker, and its own audit trail. In
  the PacificFreight case, the `tracker.lookup` tool is a function
  (no state, no audit beyond the tool result); the `MeiAgent` is
  an agent (state, breaker, trace).
- **When is a single agent better than 3?** When the task is
  simple and the cost of a multi-agent design (3× the LLM
  calls, 3× the test surface) outweighs the benefit. The
  PacificFreight drafter is single-agent for the 80% case
  (one email, one draft, no ops or IT concern). The dispatcher
  is multi-agent for the 20% case (multi-shipment, multi-audience).
- **How do you debug a multi-agent system?** Read the trace. The
  trace shows: which agents ran, in what order, with what
  latency, with what outcome. The `usage.jsonl` log line includes
  the `agent_path` field. When something goes wrong, the trace
  is the first place to look.

## 📦 Artifacts

- `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/service/agents.py` — the 3 agents + the orchestrator
- `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/service/agents_state.py` — the shared state
- `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/service/tests/test_agents.py` — the 3 tests

## 🔗 Related lessons

- [T1 — MCP tools and policies](./01-mcp-tools-and-policies.md) — the
  agents in Project 2 use the MCP server from Project 1 as their
  tool layer
- [T3 — Fine-tuning and serving an SLM](./03-fine-tuning-and-serving-slm.md) — the SLM in
  Project 3 is a future replacement for the LLM call in the agents
