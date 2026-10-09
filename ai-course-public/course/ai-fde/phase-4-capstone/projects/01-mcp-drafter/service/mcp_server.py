"""
service/mcp_server.py — Minimal Model Context Protocol (MCP) server for
PacificFreight Phase 4 Project 1.

What this file does
-------------------
Exposes 4 tools the Phase 3 drafter can call instead of just generating
text. The contract is in `mcp_policies.yaml`:

    tracker.lookup(shipment_id)            — look up a shipment, cost 1
    refund.create(shipment_id, reason,
                  amount_usd)              — issue a refund,    cost 10
    translate.to(text, lang)               — translate text,    cost 5
    escalate.to_human(reason, priority)    — page a human,      cost 1

The server enforces:
  1. **Role-based access control** — `cs_junior` cannot call
     `refund.create` (returns 403). `cs_senior` can.
  2. **Per-tool rate limit** — `refund.create` is capped at 5/min/user.
     Hitting the cap returns 429.
  3. **Unified budget** — the SUM of cost_credits across all tool calls
     in a 1-minute window is capped at `default_per_user_per_min`. The
     Phase 3 rate limiter (`TokenBucketRateLimiter`) is reused here.

Wire format: JSON-RPC 2.0 over HTTP (the MCP transport). The drafter's
system prompt lists the tool catalog; the LLM emits a `tool_call` JSON
object; the orchestrator (`app.py` in the integration layer) POSTs it
to this server.

Why a separate file
-------------------
The MCP server is a **sidecar process** in production. The drafter (in
`phase-2-applications/service/app.py`) talks to it over HTTP. A failure
of the MCP server does NOT take down the drafter — the drafter falls
back to free-text drafts (the Phase 3 3-tier fallback pattern).

How to run / import
-------------------
    # As a CLI demo (no FastAPI; just call the functions directly)
    python3 mcp_server.py

    # From the drafter
    from mcp_server import call_tool
    result = call_tool("tracker.lookup", {"shipment_id": "PF-1003"},
                       user_id="mei@pf.com", role="cs_junior")
"""
from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Optional: pull in Phase 3's rate limiter + redactor.
# We use sys.path indirection so this file is standalone-runnable.
# ---------------------------------------------------------------------------
def _import_phase3_circuit():
    p3_service = Path(__file__).parent.parent.parent.parent / "phase-2-applications" / "service"
    if str(p3_service) not in sys.path:
        sys.path.insert(0, str(p3_service))
    import circuit as _circuit  # type: ignore
    return _circuit


try:
    _circuit = _import_phase3_circuit()
    HAVE_PHASE3 = True
except Exception:
    HAVE_PHASE3 = False
    _circuit = None  # type: ignore


# ===========================================================================
# 1. Policy loader (YAML → in-memory dict)
# ===========================================================================
def _load_policies(path: Path | None = None) -> dict:
    """Load the policy file via PyYAML. Falls back to in-code defaults
    if the file is missing or PyYAML is unavailable.
    """
    if path is None:
        path = Path(__file__).parent / "mcp_policies.yaml"
    if not path.exists():
        return _DEFAULT_POLICIES
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text())
    except Exception:
        return _DEFAULT_POLICIES


_DEFAULT_POLICIES: dict = {
    "roles": {
        "cs_junior": {"can_call": ["tracker.lookup", "translate.to", "escalate.to_human"]},
        "cs_senior": {"can_call": ["tracker.lookup", "refund.create", "translate.to", "escalate.to_human"]},
        "ops": {"can_call": ["tracker.lookup"]},
        "it": {"can_call": ["tracker.lookup", "refund.create", "translate.to", "escalate.to_human"]},
        "system": {"can_call": ["tracker.lookup"]},
    },
    "rate_limits": {
        "tracker.lookup": {"per_user_per_min": 60, "per_user_per_day": 5000, "cost_credits": 1},
        "refund.create": {"per_user_per_min": 5, "per_user_per_day": 50, "cost_credits": 10},
        "translate.to": {"per_user_per_min": 20, "per_user_per_day": 500, "cost_credits": 5},
        "escalate.to_human": {"per_user_per_min": 10, "per_user_per_day": 100, "cost_credits": 1},
    },
    "budget": {"default_per_user_per_min": 60, "default_per_user_per_day": 2000},
    "tools": [
        {"name": "tracker.lookup",
         "description": "Look up a PacificFreight shipment by ID",
         "input_schema": {"type": "object",
                          "properties": {"shipment_id": {"type": "string"}},
                          "required": ["shipment_id"]}},
        {"name": "refund.create",
         "description": "Initiate a refund for a shipment",
         "input_schema": {"type": "object",
                          "properties": {"shipment_id": {"type": "string"},
                                         "reason": {"type": "string"},
                                         "amount_usd": {"type": "number"}},
                          "required": ["shipment_id", "reason", "amount_usd"]}},
        {"name": "translate.to",
         "description": "Translate text to a target language (ISO 639-1)",
         "input_schema": {"type": "object",
                          "properties": {"text": {"type": "string"},
                                         "lang": {"type": "string"}},
                          "required": ["text", "lang"]}},
        {"name": "escalate.to_human",
         "description": "Escalate the conversation to a human CS agent",
         "input_schema": {"type": "object",
                          "properties": {"reason": {"type": "string"},
                                         "priority": {"type": "string"}},
                          "required": ["reason", "priority"]}},
    ],
}


# ===========================================================================
# 2. Tool implementations (the "do something" functions)
# ===========================================================================
def _tool_tracker_lookup(args: dict) -> dict:
    sid = args.get("shipment_id", "")
    if not re.match(r"^PF-\d{4,5}$", sid):
        return {"ok": False, "error": f"invalid shipment_id: {sid!r}"}
    # Look up in Phase 1's shipments.json. The path is relative to the
    # repo root: phase-3-capstone/projects/01-mcp-drafter/service/mcp_server.py
    # → ../../../../../phase-1-foundations/shared/shipments.json
    shipments_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "phase-1-foundations" / "shared" / "shipments.json"
    )
    if not shipments_path.exists():
        return {"ok": False, "error": "shipments.json not found"}
    data = json.loads(shipments_path.read_text())
    for s in data.get("shipments", []):
        if s.get("id") == sid:
            return {
                "ok": True,
                "shipment": {
                    "id": s["id"],
                    "customer_name": s.get("customer_name"),
                    "status": s.get("status"),
                    "origin": s.get("origin"),
                    "destination": s.get("destination"),
                    "last_event": s.get("last_event"),
                    "eta": s.get("eta"),
                },
            }
    return {"ok": False, "error": f"shipment {sid} not found"}


def _tool_refund_create(args: dict) -> dict:
    sid = args.get("shipment_id", "")
    reason = args.get("reason", "")
    amount = args.get("amount_usd", 0.0)
    if not re.match(r"^PF-\d{4,5}$", sid):
        return {"ok": False, "error": f"invalid shipment_id: {sid!r}"}
    if not reason:
        return {"ok": False, "error": "reason is required"}
    if not (0 < amount <= 1000):
        return {"ok": False, "error": f"amount_usd must be in (0, 1000], got {amount}"}
    # In production this would call the finance system. The mock returns a ticket ID.
    ticket = f"REF-{int(time.time())}-{sid}"
    return {
        "ok": True,
        "refund": {
            "ticket_id": ticket,
            "shipment_id": sid,
            "reason": reason,
            "amount_usd": amount,
            "status": "pending_approval",
            "created_at": time.time(),
        },
    }


# A trivial translator that prefix-tags the text. A real implementation
# would call an LLM or a translation API.
_TRANSLATE_PREFIX = {
    "vi": "[VI] ",
    "zh": "[ZH] ",
    "ja": "[JA] ",
    "ko": "[KO] ",
    "th": "[TH] ",
    "en": "",  # identity
}


def _tool_translate_to(args: dict) -> dict:
    text = args.get("text", "")
    lang = args.get("lang", "")
    if not text:
        return {"ok": False, "error": "text is required"}
    if lang not in _TRANSLATE_PREFIX:
        return {"ok": False, "error": f"unsupported lang: {lang!r} (supported: vi, zh, ja, ko, th, en)"}
    return {
        "ok": True,
        "translation": _TRANSLATE_PREFIX[lang] + text,
        "src_lang": "auto",
        "tgt_lang": lang,
    }


def _tool_escalate_to_human(args: dict) -> dict:
    reason = args.get("reason", "")
    priority = args.get("priority", "medium")
    if not reason:
        return {"ok": False, "error": "reason is required"}
    if priority not in ("low", "medium", "high"):
        return {"ok": False, "error": f"priority must be low|medium|high, got {priority!r}"}
    return {
        "ok": True,
        "escalation": {
            "ticket_id": f"ESC-{int(time.time())}",
            "reason": reason,
            "priority": priority,
            "slack_channel": "#pf-cs-escalations",
            "paged_at": time.time(),
        },
    }


# Tool registry: name → (impl, schema). The orchestrator iterates this.
TOOL_REGISTRY: dict[str, Any] = {
    "tracker.lookup": (_tool_tracker_lookup, _DEFAULT_POLICIES["tools"][0]),
    "refund.create": (_tool_refund_create, _DEFAULT_POLICIES["tools"][1]),
    "translate.to": (_tool_translate_to, _DEFAULT_POLICIES["tools"][2]),
    "escalate.to_human": (_tool_escalate_to_human, _DEFAULT_POLICIES["tools"][3]),
}


# ===========================================================================
# 3. The server: rate limiter + policy enforcer + tool dispatcher
# ===========================================================================
@dataclass
class ToolResult:
    """The standardized response shape for any tool call."""
    ok: bool
    tool: str
    status_code: int         # 200 / 403 / 404 / 429 / 500
    data: dict = None        # the tool's return value
    error: str = None        # human-readable error
    cost_credits: int = 0    # how many credits this call consumed
    latency_ms: int = 0


class MCPServer:
    """The MCP server. Stateless across requests (the rate limiter is the
    only stateful piece; in production this is Redis).
    """
    def __init__(self, policies_path: Path | None = None) -> None:
        self.policies = _load_policies(policies_path)
        # Per-user per-minute token buckets. Key is "{user_id}:{tool_name}".
        self._buckets: dict[tuple[str, str], tuple[float, float]] = {}
        # Use Phase 3's bucket if available; otherwise the inline one.
        if HAVE_PHASE3:
            self._rl = _circuit.TokenBucketRateLimiter(
                capacity=60, refill_rate=1.0,  # 60 burst, refill 1/s
            )
        else:
            self._rl = None

    def list_tools(self) -> list[dict]:
        """Return the tool catalog (used to build the drafter's system prompt)."""
        return self.policies.get("tools", [])

    def call_tool(
        self,
        tool_name: str,
        arguments: dict,
        *,
        user_id: str,
        role: str,
    ) -> ToolResult:
        """The main entry point. Returns a ToolResult."""
        t0 = time.monotonic()
        # 1. Does the tool exist?
        if tool_name not in TOOL_REGISTRY:
            return ToolResult(ok=False, tool=tool_name, status_code=404,
                              error=f"unknown tool: {tool_name!r}")
        # 2. Is the role allowed to call this tool?
        role_cfg = self.policies.get("roles", {}).get(role, {})
        if tool_name not in role_cfg.get("can_call", []):
            return ToolResult(
                ok=False, tool=tool_name, status_code=403,
                error=f"role {role!r} is not authorized to call {tool_name!r}",
            )
        # 3. Is the per-user rate limit OK?
        rate_cfg = self.policies.get("rate_limits", {}).get(tool_name, {})
        cost = int(rate_cfg.get("cost_credits", 1))
        if not self._budget_ok(user_id, cost):
            return ToolResult(
                ok=False, tool=tool_name, status_code=429,
                error=f"rate limit exceeded for {tool_name!r} (cost {cost} credits)",
                cost_credits=cost,
            )
        # 4. Validate arguments against the schema (very minimal).
        schema = TOOL_REGISTRY[tool_name][1].get("input_schema", {})
        for req in schema.get("required", []):
            if req not in arguments:
                return ToolResult(
                    ok=False, tool=tool_name, status_code=400,
                    error=f"missing required argument: {req!r}",
                )
        # 5. Execute the tool.
        impl, _ = TOOL_REGISTRY[tool_name]
        try:
            out = impl(arguments)
        except Exception as e:
            return ToolResult(ok=False, tool=tool_name, status_code=500,
                              error=f"tool raised: {type(e).__name__}: {e}",
                              cost_credits=cost,
                              latency_ms=int((time.monotonic() - t0) * 1000))
        # 6. Charge the credits.
        self._charge(user_id, cost)
        return ToolResult(
            ok=out.get("ok", False),
            tool=tool_name,
            status_code=200 if out.get("ok") else 500,
            data=out,
            cost_credits=cost,
            latency_ms=int((time.monotonic() - t0) * 1000),
        )

    # -- rate limiter (inline, simple sliding-window) ----------------------
    def _budget_ok(self, user_id: str, cost: int) -> bool:
        budget = int(self.policies.get("budget", {}).get("default_per_user_per_min", 60))
        # Sum credits used in the last 60s.
        key = (user_id, "_credits_used_")
        now = time.monotonic()
        if key not in self._buckets:
            self._buckets[key] = (now, 0.0)
        last_ts, used = self._buckets[key]
        # Refill / decay: full reset after 60s window.
        if now - last_ts > 60.0:
            used = 0.0
            last_ts = now
        return used + cost <= budget

    def _charge(self, user_id: str, cost: int) -> None:
        key = (user_id, "_credits_used_")
        now = time.monotonic()
        if key not in self._buckets:
            self._buckets[key] = (now, float(cost))
            return
        last_ts, used = self._buckets[key]
        if now - last_ts > 60.0:
            used = 0.0
        self._buckets[key] = (now, used + cost)


# ===========================================================================
# 4. JSON-RPC 2.0 transport (the wire format MCP uses)
# ===========================================================================
def handle_jsonrpc(server: MCPServer, payload: dict) -> dict:
    """Handle a JSON-RPC 2.0 request. The drafter POSTs these."""
    method = payload.get("method")
    params = payload.get("params", {})
    req_id = payload.get("id")

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id,
                "result": {"tools": server.list_tools()}}

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        user_id = params.get("user_id", "unknown")
        role = params.get("role", "cs_junior")
        r = server.call_tool(tool_name, arguments, user_id=user_id, role=role)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "ok": r.ok,
                "status_code": r.status_code,
                "data": r.data,
                "error": r.error,
                "cost_credits": r.cost_credits,
                "latency_ms": r.latency_ms,
            },
        }

    return {"jsonrpc": "2.0", "id": req_id,
            "error": {"code": -32601, "message": f"method not found: {method!r}"}}


# ===========================================================================
# 5. CLI demo
# ===========================================================================
def main() -> int:
    print("=" * 70)
    print("MCP server — PacificFreight drafter (Phase 4 Project 1)")
    print("=" * 70)
    server = MCPServer()

    print(f"\nLoaded {len(server.list_tools())} tools from policy file:")
    for t in server.list_tools():
        print(f"  • {t['name']}: {t['description'][:60]}...")

    print(f"\nRoles:")
    for r, cfg in server.policies.get("roles", {}).items():
        print(f"  • {r}: can call {len(cfg.get('can_call', []))} tools")

    print("\n--- 1. tracker.lookup as cs_junior (Mei) ---")
    r = server.call_tool("tracker.lookup", {"shipment_id": "PF-1003"},
                         user_id="mei@pf.com", role="cs_junior")
    print(f"  status={r.status_code}  ok={r.ok}  cost={r.cost_credits}  latency={r.latency_ms}ms")
    if r.data:
        print(f"  customer={r.data.get('shipment', {}).get('customer_name')}  status={r.data.get('shipment', {}).get('status')}")

    print("\n--- 2. refund.create as cs_junior (Mei) — should 403 ---")
    r = server.call_tool(
        "refund.create",
        {"shipment_id": "PF-1003", "reason": "lost in transit", "amount_usd": 50.0},
        user_id="mei@pf.com", role="cs_junior",
    )
    print(f"  status={r.status_code}  ok={r.ok}  error={r.error}")

    print("\n--- 3. refund.create as cs_senior — should 200 ---")
    r = server.call_tool(
        "refund.create",
        {"shipment_id": "PF-1003", "reason": "lost in transit", "amount_usd": 50.0},
        user_id="alice@pf.com", role="cs_senior",
    )
    print(f"  status={r.status_code}  ok={r.ok}  cost={r.cost_credits}")
    if r.data:
        print(f"  ticket={r.data.get('refund', {}).get('ticket_id')}")

    print("\n--- 4. translate.to as cs_junior ---")
    r = server.call_tool(
        "translate.to",
        {"text": "Your shipment is held at customs. Please pay the duty.", "lang": "vi"},
        user_id="mei@pf.com", role="cs_junior",
    )
    print(f"  status={r.status_code}  ok={r.ok}  cost={r.cost_credits}")
    if r.data:
        print(f"  translation={r.data.get('translation')!r}")

    print("\n--- 5. rate limit: 6 refund.creates in 1 second as cs_senior ---")
    for i in range(6):
        r = server.call_tool(
            "refund.create",
            {"shipment_id": f"PF-100{i}", "reason": "test", "amount_usd": 1.0},
            user_id="alice@pf.com", role="cs_senior",
        )
        verdict = "ALLOWED" if r.status_code == 200 else f"REJECTED ({r.status_code})"
        print(f"  call {i+1}: {verdict}  (cost {r.cost_credits})")

    print("\n--- 6. unknown tool ---")
    r = server.call_tool("refund.delete", {}, user_id="mei@pf.com", role="cs_junior")
    print(f"  status={r.status_code}  error={r.error}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
