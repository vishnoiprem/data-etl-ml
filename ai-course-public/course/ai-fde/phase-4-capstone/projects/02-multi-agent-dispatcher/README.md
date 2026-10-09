# Project 2 — Multi-agent PacificFreight dispatcher

> **Phase 4, Project 2.** A 3-agent orchestrator that handles multi-shipment
> cases end-to-end without the CS user (Mei) clicking 5 buttons. Each agent
> has its own circuit breaker; the agents share a single state object;
> the agents call tools via the MCP server from Project 1.

## What's in this directory

```
02-multi-agent-dispatcher/
├── README.md
└── service/
    ├── agents.py            # The 3 agents + the orchestrator
    ├── agents_state.py      # The shared state (the "bus" between agents)
    └── tests/
        ├── conftest.py      # Adds 02/, 01-mcp-drafter/, and phase-2-core-build/ to sys.path
        └── test_agents.py   # 3 tests (routing, shared state, risk escalation)
```

## What this project proves

The 3-audience stakeholder map (Mei = CS, Sarah = ops, Daniel = infra)
becomes **3 agents that talk to each other**. The runbook's escalation
tiers become **agent escalation rules**. Mei's CS lane, Sarah's ops
lane, Daniel's infra lane are encoded as agent boundaries, not just
human ones.

The lesson is: **the shared state is the contract.** A new agent is
a new field on the state and a new node in the graph. The orchestrator
doesn't change. The 3 existing agents don't change.

## The 3 agents

| Agent | Lane | When it runs | What it does |
|---|---|---|---|
| `MeiAgent` | CS | always first | Looks up each shipment via `tracker.lookup`; produces the customer reply. If the email asks for a refund, attempts `refund.create` (RBAC enforced at the MCP server). |
| `SarahAgent` | Ops | only when `len(shipment_ids) > 1` | Produces a cross-shipment summary. If 2+ are held at customs, escalates `risk_level` to `high`. |
| `DanielAgent` | Infra | always last | Emits a one-paragraph cost/risk/audit note that Daniel (the IT owner) can paste into the on-call log. |

Each agent has its own `CircuitBreaker` so a Mei failure doesn't block
Daniel. The orchestrator's breaker is the parent and gates the whole
pipeline.

## The shared state

`agents_state.DispatcherState` is a single dataclass that flows through
the orchestrator. Fields are partitioned by writer:

| Field | Written by | Read by |
|---|---|---|
| `mei_draft` | `MeiAgent` | orchestrator response |
| `sarah_summary` | `SarahAgent` | orchestrator response |
| `daniel_note` | `DanielAgent` | orchestrator response |
| `agent_path` | every agent (append) | audit log |
| `tool_calls` | every agent (append) | audit log + cost rollup |
| `risk_level` | `MeiAgent`, `SarahAgent` | `DanielAgent` |
| `trace` | every agent (append-only) | audit log |

The `trace` list is append-only. Rewriting it would lose data; the
dispatcher enforces this by giving every writer a `state.append_trace(...)`
method instead of a `state.trace = [...]` assignment.

## How to run

### 1. CLI demo (3 canned cases)

```bash
cd course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher
python3 service/agents.py
```

Runs 3 cases:

1. **single_shipment** — Mei (cs_junior) asks about PF-1003. Agents: Mei, Daniel.
2. **multi_shipment** — Alice (cs_senior) asks about PF-1001, PF-1002, PF-1003. Agents: Mei, Sarah, Daniel.
3. **refund_request_junior** — Mei (cs_junior) asks for a $50 refund on PF-1002. Agents: Mei, Daniel. Mei's draft mentions "refund not authorized for this role — escalating to senior" and `risk_level` is set to `medium`.

### 2. Run a single case (JSON output)

```bash
python3 service/agents.py --case multi_shipment
```

Emits a JSON blob with all 3 agent outputs + the tool calls + the cost rollup.

### 3. Run the 3 tests

```bash
cd course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher
python3 -m pytest service/tests/test_agents.py -v
```

Expected: **3 passed in 0.4s**

The tests cover:
1. `test_orchestrator_routes_single_vs_multi_shipment` — single shipment runs Mei+Daniel, multi runs Mei+Sarah+Daniel
2. `test_agents_share_state_via_dispatcher_state` — all 3 agents wrote to disjoint fields; the trace grew monotonically; `to_dict()` roundtrips
3. `test_daniel_agent_escalates_on_high_risk` — Daniel's note always mentions the risk level

### 4. Call the dispatcher from your code

```python
import sys
sys.path.insert(0, "course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/service")
sys.path.insert(0, "course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/service")
import agents

d = agents.Dispatcher()
state = d.dispatch(
    "Hi, I need an update on PF-1001, PF-1002, and PF-1003. PF-1001 and PF-1003 "
    "are both held at customs — is there a pattern? Also please refund $50 for PF-1003.",
    user_id="alice@pf.com", role="cs_senior",
)
print(state.mei_draft)       # The customer reply
print(state.sarah_summary)   # The cross-shipment summary
print(state.daniel_note)     # The cost/risk/audit note
print(state.cost_usd)        # The total LLM+tool cost for this request
```

## How to extend

### Add a 4th agent (e.g. LegalAgent for compliance)

1. Subclass `Agent` in `service/agents.py`. Implement `execute(self, state)`.
   The agent reads from `state`, mutates its own field (e.g. `state.legal_check`),
   and returns the state.

2. Add a per-agent field to `agents_state.DispatcherState`:
   ```python
   legal_check: Optional[str] = None
   ```

3. In the orchestrator's `dispatch()`, add a routing rule:
   ```python
   if re.search(r"\bGDPR\b|\bPIPL\b", state.email_body, re.I):
       state = self.breaker.call(self._run_legal, state)
   ```

4. (Optional) Add a per-agent breaker in `Dispatcher.__init__`:
   ```python
   self.legal = LegalAgent()
   ```

The 3 existing agents don't change. The orchestrator adds one line. The
state adds one field. That's the lesson: **the routing rules are the only
place new behavior enters the system.**

## Routing rules (the only logic the orchestrator owns)

```python
# Mei always runs first
state = self.breaker.call(self._run_mei, state)

# Sarah runs if multi-shipment
if not state.error and len(state.shipment_ids) > 1:
    state = self.breaker.call(self._run_sarah, state)

# Daniel always runs (he's the auditor)
if not state.error:
    state = self.breaker.call(self._run_daniel, state)
```

The routing rules are dead simple. The interesting code is in each
agent. The orchestrator's job is to call them in order and to wrap each
in a circuit breaker.

## Dependencies

- **Project 1's `mcp_server.py`** — the tool layer. The agents call
  `tracker.lookup` and `refund.create` via the MCP server, NOT directly
  on the data. This means RBAC + rate limit + cost_credits are enforced
  uniformly across all 3 agents.
- **Phase 3's `circuit.py`** — `CircuitBreaker` is reused for per-agent
  isolation and for the parent orchestrator breaker.
- **No LangGraph required** — the orchestrator is a hand-rolled state
  machine (~50 lines). The lesson (`../technical/02-multi-agent-design.md`)
  explains when LangGraph adds value (graph cycles, parallel branches,
  human-in-the-loop) and when it doesn't (this project).

## Where this fits in the bigger picture

```
Phase 3 drafter              Phase 4 lift                     Why
───────────────────         ──────────                       ────
1 email → 1 draft      →    1 email → 1 draft + 1           Multi-shipment cases are
                              ops summary + 1                 common; Mei shouldn't
                              infra note                      have to copy/paste across
                                                              5 tools
1 tool layer (Phase 3)  →   + 4 MCP tools (Project 1)        Same RBAC + rate limit
                                                              apply to all 3 agents
1 circuit breaker       →    + 3 per-agent breakers           A Mei failure doesn't
                                                              block Daniel
                                                               
```

**The drafter's `/draft` endpoint doesn't change.** It gains a sibling
endpoint: `POST /dispatch` for multi-shipment cases. The drafter
auto-routes single-shipment emails to `/draft` and multi-shipment
emails to `/dispatch` based on whether the regex finds ≥ 2 `PF-XXXX`
mentions.

## Related

- [`../01-mcp-drafter/`](../01-mcp-drafter/) — the tool layer this project uses
- [`../../phase-2-core-build/service/circuit.py`](../../../phase-2-core-build/service/circuit.py) — the circuit breaker
- [`../../phase-2-core-build/service/retrieval_v2.py`](../../../phase-2-core-build/service/retrieval_v2.py) — the hybrid retriever the drafter uses (not the dispatcher — the dispatcher uses the MCP server's `tracker.lookup` instead)
- [`../03-distilled-slm/`](../03-distilled-slm/) — the project that fine-tunes a 1.5B model on Mei's drafts (could replace the MeiAgent's mock-LLM behavior in production)
- [`../04-ai-data-analyst/`](../04-ai-data-analyst/) — the fresh-engagement project (different customer, different security model)
