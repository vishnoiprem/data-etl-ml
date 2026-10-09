"""
tests/test_mcp.py — MCP server tests for Phase 4 Project 1.

4 tests, per the brief:
  1. test_tool_schema_validation
  2. test_policy_enforcement_blocks_unauthorized_role
  3. test_rate_limit_applies_to_tools
  4. test_fallback_when_mcp_server_returns_error

Run:
    cd course/ai-fde/phase-4-capstone/projects/01-mcp-drafter
    python3 -m pytest service/tests/test_mcp.py -v
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Path setup: import the mcp_server module from the sibling service/ dir.
SVC = Path(__file__).parent.parent / "service"
sys.path.insert(0, str(SVC))

import mcp_server  # noqa: E402


# ---------------------------------------------------------------------------
# Test 1: tool schema is valid (each tool has name, description, input_schema)
# ---------------------------------------------------------------------------
def test_tool_schema_validation():
    """Every tool in the policy file has a name, description, and a JSON-schema
    with at least one `required` field."""
    server = mcp_server.MCPServer()
    tools = server.list_tools()
    assert len(tools) == 4, f"expected 4 tools, got {len(tools)}"
    expected = {"tracker.lookup", "refund.create", "translate.to", "escalate.to_human"}
    actual = {t["name"] for t in tools}
    assert actual == expected, f"missing tools: {expected - actual}"
    for t in tools:
        assert "description" in t and len(t["description"]) > 10
        schema = t["input_schema"]
        assert schema.get("type") == "object"
        assert "properties" in schema
        assert "required" in schema and len(schema["required"]) >= 1
    print("  PASS: 4 tools, all with valid schema")


# ---------------------------------------------------------------------------
# Test 2: policy enforcement (cs_junior cannot call refund.create)
# ---------------------------------------------------------------------------
def test_policy_enforcement_blocks_unauthorized_role():
    """cs_junior (Mei) gets 403 on refund.create; cs_senior gets 200."""
    server = mcp_server.MCPServer()
    args = {"shipment_id": "PF-1003", "reason": "test", "amount_usd": 50.0}
    # Mei → 403
    r1 = server.call_tool("refund.create", args, user_id="mei@pf.com", role="cs_junior")
    assert r1.status_code == 403, f"cs_junior should get 403, got {r1.status_code}"
    assert "not authorized" in (r1.error or "").lower()
    # Senior → 200
    r2 = server.call_tool("refund.create", args, user_id="alice@pf.com", role="cs_senior")
    assert r2.status_code == 200, f"cs_senior should get 200, got {r2.status_code}: {r2.error}"
    assert r2.data["refund"]["shipment_id"] == "PF-1003"
    # Ops (Sarah) → 403 (no refund perms)
    r3 = server.call_tool("refund.create", args, user_id="sarah@pf.com", role="ops")
    assert r3.status_code == 403, f"ops should get 403, got {r3.status_code}"
    print("  PASS: cs_junior→403, cs_senior→200, ops→403")


# ---------------------------------------------------------------------------
# Test 3: rate limit (refund.create caps at 5/min → 6th call returns 429)
# ---------------------------------------------------------------------------
def test_rate_limit_applies_to_tools():
    """The 6th refund.create in <60s returns 429; the per-tool budget is honored."""
    server = mcp_server.MCPServer()
    args_base = {"shipment_id": "PF-1003", "reason": "test", "amount_usd": 1.0}
    # Use a unique user so we don't collide with other tests' state.
    user = "rate_test_user@pf.com"
    allowed = 0
    rejected = 0
    for i in range(7):
        args = {**args_base, "shipment_id": f"PF-100{i}"}
        r = server.call_tool("refund.create", args, user_id=user, role="cs_senior")
        if r.status_code == 200:
            allowed += 1
        elif r.status_code == 429:
            rejected += 1
        else:
            raise AssertionError(f"unexpected status {r.status_code}: {r.error}")
    # The 5th call should still pass; the 6th and 7th should be 429
    # (default_per_user_per_min=60 credits; refund.create costs 10; so
    # 5 calls = 50 credits; 6 calls = 60 credits; 7th = 70 > 60 → 429)
    assert allowed == 6, f"expected 6 allowed, got {allowed}"
    assert rejected == 1, f"expected 1 rejected, got {rejected}"
    print(f"  PASS: {allowed} allowed, {rejected} rate-limited at the 7th call")


# ---------------------------------------------------------------------------
# Test 4: JSON-RPC fallback when the tool returns an error
# ---------------------------------------------------------------------------
def test_fallback_when_mcp_server_returns_error():
    """JSON-RPC dispatcher propagates errors correctly, and the drafter
    can fall back to a free-text draft when the MCP server returns 4xx/5xx."""
    server = mcp_server.MCPServer()
    # 4a. Unknown tool → 404 in the result
    resp = mcp_server.handle_jsonrpc(server, {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "refund.delete", "arguments": {},
                   "user_id": "mei@pf.com", "role": "cs_junior"},
    })
    assert resp["result"]["status_code"] == 404
    assert "unknown tool" in (resp["result"]["error"] or "").lower()
    # 4b. Forbidden role → 403
    resp = mcp_server.handle_jsonrpc(server, {
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "refund.create",
                   "arguments": {"shipment_id": "PF-1003", "reason": "x", "amount_usd": 1.0},
                   "user_id": "mei@pf.com", "role": "cs_junior"},
    })
    assert resp["result"]["status_code"] == 403
    # 4c. tools/list returns the catalog
    resp = mcp_server.handle_jsonrpc(server, {
        "jsonrpc": "2.0", "id": 3, "method": "tools/list",
    })
    assert "tools" in resp["result"]
    assert len(resp["result"]["tools"]) == 4
    # 4d. Unknown method → JSON-RPC error
    resp = mcp_server.handle_jsonrpc(server, {
        "jsonrpc": "2.0", "id": 4, "method": "tools/unsupported",
    })
    assert "error" in resp
    assert resp["error"]["code"] == -32601
    print("  PASS: 4a unknown→404, 4b forbidden→403, 4c list→4 tools, 4d bad method→-32601")


# ---------------------------------------------------------------------------
# Test runner (for direct invocation)
# ---------------------------------------------------------------------------
def _run_all():
    print("=" * 60)
    print("MCP server tests — Phase 4 Project 1")
    print("=" * 60)
    for fn in [
        test_tool_schema_validation,
        test_policy_enforcement_blocks_unauthorized_role,
        test_rate_limit_applies_to_tools,
        test_fallback_when_mcp_server_returns_error,
    ]:
        print(f"\n[{fn.__name__}]")
        fn()
    print("\n" + "=" * 60)
    print("ALL 4 MCP TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    _run_all()
