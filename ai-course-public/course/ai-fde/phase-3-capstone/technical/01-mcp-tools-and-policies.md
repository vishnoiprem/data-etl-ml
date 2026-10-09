# Lesson T1 — MCP tools, policies, and the YAML contract

> **Phase 4, Technical Track, Lesson 1.** Why a YAML file is the
> contract for tool access, and how the cost ceiling extends from
> LLM tokens to tool calls.

## 🎯 Outcome

By the end of this lesson you can:

- **Explain** why the policy file is the contract, not the drafter's code.
- **Add a new role** to a YAML policy file without changing a single
  line of Python.
- **Add a new tool** to the MCP server in 30 lines of code + 1
  paragraph in the YAML.
- **Reason about** the unified credit budget as the cap on tool-call
  impact, not just LLM token usage.

## 🧠 Mindset

The Phase 3 drafter is a single-purpose LLM call: it takes an email
and produces a reply. It's correct 95% of the time, but it can't:
- Look up a shipment status
- Issue a refund
- Translate the reply to Vietnamese
- Page a human when the customer is upset

The Phase 4 MCP lift turns the drafter into a **tool-using agent.**
But "tool-using" is the easy part — the hard part is **governing**
which CS user can call which tool, with what rate limit, at what cost.

**The lesson:** governance is data, not code. A new role is a 1-line
addition to `mcp_policies.yaml`. A new tool is 30 lines of code + 1
paragraph in the YAML. The drafter doesn't change. The eval set
doesn't change. The 13/13 tests don't change.

If your policy is hard-coded in Python, every role change is a
deploy. If your policy is in YAML, every role change is a PR review
and a config push. **YAML is the right level for "human-editable,
machine-readable, code-reviewable."**

## 🛠️ Practice

You are extending the PacificFreight MCP server to add a 5th tool:
`label.print`. The warehouse team needs to print a shipping label for
a shipment. They have these constraints:

- The tool is **allowed only for the `warehouse` and `it` roles.**
- The rate limit is **30 calls/min/user.**
- The cost is **2 credits per call** (less than a `refund.create`'s 10
  because the warehouse impact is smaller than the finance impact).
- The input schema is `{ "shipment_id": "PF-XXXX" }` (the same regex
  as `tracker.lookup`).

You do this in 3 steps:

### Step 1 — Implement the tool in Python

Open `course/ai-fde/phase-3-capstone/projects/01-mcp-drafter/service/mcp_server.py`
and add:

```python
def _tool_label_print(args: dict) -> dict:
    sid = args.get("shipment_id", "")
    if not re.match(r"^PF-\d{4,5}$", sid):
        return {"ok": False, "error": f"invalid shipment_id: {sid!r}"}
    return {
        "ok": True,
        "label": {
            "shipment_id": sid,
            "printed_at": time.time(),
            "label_url": f"https://labels.pf.com/{sid}",
        },
    }

TOOL_REGISTRY["label.print"] = (_tool_label_print, {
    "name": "label.print",
    "description": "Print a shipping label for a PacificFreight shipment",
    "input_schema": {"type": "object",
                     "properties": {"shipment_id": {"type": "string"}},
                     "required": ["shipment_id"]},
})
```

That's 30 lines.

### Step 2 — Update the YAML policy

Open `service/mcp_policies.yaml` and add:

```yaml
roles:
  warehouse:
    description: "Warehouse team — prints labels, reads tracker"
    can_call: [label.print, tracker.lookup]
  # (cs_senior, cs_junior, ops, it, system unchanged)

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

That's ~15 lines.

### Step 3 — Test

```bash
cd course/ai-fde/phase-3-capstone/projects/01-mcp-drafter
python3 -m pytest service/tests/test_mcp.py -v
```

The 4 existing tests still pass (the YAML change is backwards
compatible). To verify the new tool:

```python
import sys
sys.path.insert(0, "service")
import mcp_server

server = mcp_server.MCPServer()

# Mei (cs_junior) cannot call label.print → 403
r = server.call_tool("label.print", {"shipment_id": "PF-1003"},
                     user_id="mei@pf.com", role="cs_junior")
assert r.status_code == 403

# Warehouse can call label.print → 200
r = server.call_tool("label.print", {"shipment_id": "PF-1003"},
                     user_id="worker1@pf.com", role="warehouse")
assert r.status_code == 200
assert r.data["label"]["shipment_id"] == "PF-1003"
```

Both checks pass. The drafter's code didn't change. The eval set
didn't change. The 13/13 tests didn't change. **The policy file is
the only thing that changed.**

## 🏛️ FDE Lens

**Why the YAML file, not the database?** Three reasons:

1. **Code-reviewable.** A change to `mcp_policies.yaml` is a 5-line
   PR. A change to a database row is invisible to the next person who
   reads the repo.
2. **Versioned.** The policy file is in git. Every change has an
   author, a timestamp, a commit message, and a reviewer. A database
   row has none of these.
3. **Auditable.** When Mei asks "who changed the rate limit for
   `refund.create` last Tuesday?", the answer is in `git log`. A
   database change is in a migration file (or nowhere).

The cost is that the policy file is **read at startup**, not
hot-reloaded. A role change requires a service restart. That's the
right tradeoff for a 12-person SMB: the rate of change is low, the
cost of "I forgot to restart" is bounded by the next deploy.

**Why the cost_credits abstraction?** The Phase 3 rate limiter
treats the SUM of cost_credits across all tool calls in a 1-minute
window as the budget. A `cs_senior` user calling `refund.create` (10
credits) + `translate.to` (5 credits) + `tracker.lookup` (1 credit)
= 16 credits/min — well under the default of 60 credits/min.

But if the same user calls `refund.create` six times in a minute,
they hit the 60-credit ceiling and get a 429. The ceiling is **a
single number to reason about** — 60 credits/min — and the cost of
each tool is encoded in the YAML. A new tool is a new cost; the
ceiling doesn't change.

**Why JSON-RPC 2.0?** Because that's the wire format MCP uses. The
MCP standard is a transport spec, not a tool spec — the tools
themselves are described by the policy file. We could have used
REST, gRPC, or even in-process function calls, but using JSON-RPC
means **the drafter's wire format is the same as the production
deployment's wire format.** A future production migration to a
managed MCP service is a config change, not a rewrite.

**What's the production deployment story?** In Phase 4 the MCP
server is a sidecar process in the same VM as the drafter. In Phase 5
(production) it would be a separate service with:
- **Redis** instead of in-process dicts (for the rate limiter)
- **An auth layer** (OAuth, mTLS) for the user_id and role
- **A real finance-system integration** for `refund.create` (the
  mock returns a ticket ID; the real thing calls the ledger)
- **A Slack webhook** for `escalate.to_human` (the mock returns a
  ticket ID; the real thing posts to `#pf-cs-escalations`)

The contract is the YAML. The drafter doesn't change.

## 🌙 Reflect

- **What's the difference between RBAC and rate limiting?** RBAC
  says "this user can call this tool." Rate limiting says "this
  user can call this tool at most N times per minute." The MCP
  server enforces both. RBAC failures return 403; rate-limit
  failures return 429. A 403 means "you're not allowed" (permanent
  for this user/role); a 429 means "you're allowed but you've
  exhausted your budget" (temporary, try again in 60s).
- **What happens when a tool returns 5xx?** The drafter catches
  it and falls back to a free-text draft. The Phase 3 3-tier
  fallback pattern (`cache → cheaper LLM → stub`) extends
  naturally: when the tool layer fails, the drafter uses the
  cache (the previous draft) → the cheaper LLM (a smaller model
  that can produce text but can't call tools) → the stub (the
  Phase 1 deterministic stub). The user still gets a reply.
- **What's the relationship between cost_credits and dollars?**
  In the YAML, `cost_credits` is a unitless number that controls
  the rate limit. The dollar cost is separate (in `ARCHITECTURE.md`).
  The 60 credits/min ceiling is the **operational** limit; the
  $0.55/week cost is the **financial** limit. The two are linked
  (a `refund.create` is more expensive because it touches the
  finance system), but they're not the same number. The
  `cost_credits` field is the lever; the dollar cost is the
  observed value.

## 📦 Artifacts

- `course/ai-fde/phase-3-capstone/projects/01-mcp-drafter/service/mcp_server.py` — the MCP server (4 tools, RBAC, rate limit, JSON-RPC 2.0)
- `course/ai-fde/phase-3-capstone/projects/01-mcp-drafter/service/mcp_policies.yaml` — the policy file
- `course/ai-fde/phase-3-capstone/projects/01-mcp-drafter/service/tests/test_mcp.py` — the 4 tests
- `course/ai-fde/phase-3-capstone/projects/01-mcp-drafter/ARCHITECTURE.md` — the design doc

## 🔗 Related lessons

- [T2 — Multi-agent design](./02-multi-agent-design.md) — the agents
  in Project 2 use the MCP server as their tool layer
- [T3 — Fine-tuning and serving an SLM](./03-fine-tuning-and-serving-slm.md) — the SLM in Project 3 is a
  future replacement for the LLM call in the drafter; the MCP
  contract is unchanged
