# Project 1 — MCP-tooled PacificFreight drafter

> **Phase 4, Project 1.** Extends the Phase 3 PacificFreight drafter with
> 4 MCP-callable tools (tracker, refund, translate, escalate) gated by a
> YAML policy file. The drafter goes from "single-purpose LLM call" to
> "tool-using agent that respects the same operational boundaries as before."

## What's in this directory

```
01-mcp-drafter/
├── ARCHITECTURE.md             # 7-section design doc (system diagram, capacity, cost, failure modes, security)
├── README.md                   # ← you are here
└── service/
    ├── mcp_server.py           # MCP server — 4 tools, RBAC, rate limit, JSON-RPC 2.0
    ├── mcp_policies.yaml       # The contract: roles, rate limits, tool catalog, budget
    └── tests/
        ├── conftest.py         # Adds service/ to sys.path for pytest
        └── test_mcp.py         # 4 tests (schema, RBAC, rate limit, fallback)
```

## What this project proves

Phase 3's drafter is a single-purpose LLM call. The MCP lift turns it into a
**tool-using agent** that respects the same operational boundaries (rate
limit, breaker, redaction) as before. The cost ceiling now applies to tool
calls too, not just LLM tokens.

The lesson is: **the policy file is the contract.** The drafter's behavior
is constrained by what's in the YAML. A new role is a 1-line addition. A
new tool is 30 lines of code + 1 paragraph in the YAML. The drafter
doesn't change.

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full design doc.

## The 4 tools

| Tool | Cost (credits) | Who can call | What it does |
|---|---|---|---|
| `tracker.lookup` | 1 | everyone | Look up a PacificFreight shipment by ID |
| `refund.create` | 10 | cs_senior, it | Initiate a refund in the finance system |
| `translate.to` | 5 | cs_junior, cs_senior, it | Translate text to a target language |
| `escalate.to_human` | 1 | cs_junior, cs_senior, it | Page a human via Slack |

The unified budget is **60 credits/min/user**. A `cs_senior` calling
`refund.create` (10) + `translate.to` (5) + `tracker.lookup` (1) consumes
16 credits — well under the budget.

## How to run

### 1. Standalone demo (no FastAPI needed)

```bash
cd course/ai-fde/phase-4-capstone/projects/01-mcp-drafter
python3 service/mcp_server.py
```

Expected output (6 scenarios):

```
--- 1. tracker.lookup as cs_junior (Mei) ---
  status=200  ok=True  cost=1  latency=0ms
  customer=Mei Lin  status=held_customs

--- 2. refund.create as cs_junior (Mei) — should 403 ---
  status=403  ok=False  error=role 'cs_junior' is not authorized to call 'refund.create'

--- 3. refund.create as cs_senior — should 200 ---
  status=200  ok=True  cost=10
  ticket=REF-1791554622-PF-1003

--- 4. translate.to as cs_junior ---
  status=200  ok=True  cost=5
  translation='[VI] Your shipment is held at customs. Please pay the duty.'

--- 5. rate limit: 6 refund.creates in 1 second as cs_senior ---
  call 1-5: ALLOWED, call 6: REJECTED (429)

--- 6. unknown tool ---
  status=404  error=unknown tool: 'refund.delete'
```

### 2. Run the 4 tests

```bash
cd course/ai-fde/phase-4-capstone/projects/01-mcp-drafter
python3 -m pytest service/tests/test_mcp.py -v
```

Expected: **4 passed in 0.3s**

The tests cover:
1. `test_tool_schema_validation` — every tool in the policy file has a name, description, and a JSON-schema with required fields
2. `test_policy_enforcement_blocks_unauthorized_role` — `cs_junior` → 403, `cs_senior` → 200, `ops` → 403
3. `test_rate_limit_applies_to_tools` — the 6th `refund.create` in <60s returns 429 (60-credit budget, 10 credits/refund)
4. `test_fallback_when_mcp_server_returns_error` — JSON-RPC dispatcher propagates 4xx/5xx and the drafter can fall back to free-text

### 3. Call the MCP server from your code

```python
import sys
sys.path.insert(0, "course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/service")
import mcp_server

server = mcp_server.MCPServer()

# Tracker lookup (allowed for any role)
r = server.call_tool(
    "tracker.lookup",
    {"shipment_id": "PF-1003"},
    user_id="mei@pf.com", role="cs_junior",
)
print(r.status_code, r.data)  # 200, {ok: True, shipment: {...}}

# Refund (denied for cs_junior)
r = server.call_tool(
    "refund.create",
    {"shipment_id": "PF-1003", "reason": "lost in transit", "amount_usd": 50.0},
    user_id="mei@pf.com", role="cs_junior",
)
print(r.status_code, r.error)  # 403, role 'cs_junior' is not authorized...

# JSON-RPC transport (what the drafter uses)
resp = mcp_server.handle_jsonrpc(server, {
    "jsonrpc": "2.0", "id": 1, "method": "tools/call",
    "params": {"name": "tracker.lookup", "arguments": {"shipment_id": "PF-1003"},
               "user_id": "mei@pf.com", "role": "cs_junior"},
})
print(resp["result"]["status_code"])  # 200
```

## How to extend

### Add a new role

Edit `service/mcp_policies.yaml`:

```yaml
roles:
  finance:
    description: "Finance team — can issue refunds but not call the customer"
    can_call: [refund.create, tracker.lookup]
```

No code change. The drafter picks this up at startup.

### Add a new tool

1. Implement the tool in `service/mcp_server.py` and register it in `TOOL_REGISTRY`
2. Add an entry to the `tools` list in `mcp_policies.yaml`
3. Add a `rate_limits` entry (and a role grant if appropriate)

Example — adding a `label.print` tool for the warehouse team:

```python
# In mcp_server.py
def _tool_label_print(args: dict) -> dict:
    sid = args.get("shipment_id", "")
    return {"ok": True, "label": f"PF-LABEL-{sid}-{int(time.time())}"}

TOOL_REGISTRY["label.print"] = (_tool_label_print, {
    "name": "label.print",
    "description": "Print a shipping label for a PacificFreight shipment",
    "input_schema": {"type": "object",
                     "properties": {"shipment_id": {"type": "string"}},
                     "required": ["shipment_id"]},
})
```

```yaml
# In mcp_policies.yaml
roles:
  warehouse:
    can_call: [label.print, tracker.lookup]
rate_limits:
  label.print:
    per_user_per_min: 30
    per_user_per_day: 2000
    cost_credits: 2
tools:
  - name: label.print
    description: "Print a shipping label for a PacificFreight shipment"
    input_schema:
      type: object
      properties:
        shipment_id: {type: string, pattern: "^PF-\\d{4,5}$"}
      required: [shipment_id]
```

The drafter sees `label.print` in the tool catalog and can call it on Mei's
behalf. The rate limit + cost_credits are enforced at the MCP server, not
at the drafter.

## Dependencies

- **PyYAML** (already installed at the repo level) — policy file parsing
- **Phase 3 `service/circuit.py`** — `TokenBucketRateLimiter` (the budget
  pattern is a minimal reuse; the MCP server has its own in-process
  sliding-window budget for tool calls)
- **Phase 1 `shared/shipments.json`** — the data source for `tracker.lookup`

Install if needed:
```bash
pip install pyyaml
```

## Where this fits in the bigger picture

```
Phase 3 service           Phase 4 lift                Why
─────────────────         ────────────                ────
/draft (LLM only)    →    /draft + /mcp/tools         The drafter can call tools
                          (this project)
/draft (no schema)    →    JSON-Schema for each tool   The LLM knows what to pass
CircuitBreaker         →    + per-tool rate limit      Budget applies to tool calls too
                          (cost_credits)
free-text draft        →    tool result + free-text    The drafter can use a
                          (fallback)                   tracker.lookup result OR
                                                       fall back to a free draft
                                                       if the MCP server is down
```

**The Phase 3 drafter doesn't change.** It gains a new code path: "if the
LLM emits a `tool_call`, POST it to the MCP server and feed the result
back into the prompt." That's the wire-level integration. The drafter's
prompt, its eval set, its 13/13 tests, its runbook — all unchanged.

## Next: integrate with the drafter

To wire this into the Phase 3 service (the `/draft` endpoint that calls
the LLM), see `course/ai-fde/phase-2-core-build/service/app.py` — the
`/draft` handler can be extended to:

1. List tools from `mcp_server.list_tools()` and inject them into the system prompt
2. If the LLM response contains a `tool_call` JSON block, extract it and
   POST it to `mcp_server.handle_jsonrpc(...)`
3. Feed the tool result back into the LLM as a follow-up turn
4. Return the final draft

This project ships the MCP server and the policy file as a standalone
artifact. The `/draft` integration is a separate lift in the Phase 3
service (and is sketched in `ARCHITECTURE.md` § 1).

## Related

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — the design doc
- [`mcp_policies.yaml`](./service/mcp_policies.yaml) — the policy contract
- [`service/mcp_server.py`](./service/mcp_server.py) — the server
- [`service/tests/test_mcp.py`](./service/tests/test_mcp.py) — the 4 tests
- [`../02-multi-agent-dispatcher/`](../02-multi-agent-dispatcher/) — the next project, which uses this MCP server inside a LangGraph orchestrator
- [`../03-distilled-slm/`](../03-distilled-slm/) — the project that fine-tunes a 1.5B model on Mei's drafts
- [`../04-ai-data-analyst/`](../04-ai-data-analyst/) — the fresh-engagement project (different customer, different security model)
