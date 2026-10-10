"""
Lesson 8.5: Tool Design
====================================
5 production tools with descriptions + tests.

Run:  python lesson-8-5-tool-design.py

No external API keys required -- all LLM/DB calls are mocked.

Builds on lesson-8-2 (the ReAct loop) and lesson-8-4 (parsers).
Lesson 8.5 is about the *tools themselves*: the contract between the
LLM and the outside world. A well-designed tool is named clearly,
takes typed args, returns a structured result, and fails loudly.
"""


# =============================================================================
# CONFIG -- All magic numbers live here
# =============================================================================

LESSON_NUMBER = "8.5"
LESSON_TITLE = "Tool Design"
DEFAULT_MODEL = "gpt-5-mini"  # 2026-current cheap+smart; mock used for the demo

# Pricing per 1M tokens, 2026-current (per OpenAI, Anthropic, Google public pricing, Q4 2026)
PRICING = {
    "gpt-5":              {"input": 2.50,  "output": 10.00},
    "gpt-5-mini":         {"input": 0.15,  "output": 0.60},
    "claude-sonnet-4.5":  {"input": 3.00,  "output": 15.00},
    "claude-haiku-4.5":   {"input": 0.80,  "output": 4.00},
    "gemini-2.5-pro":     {"input": 1.25,  "output": 5.00},
    "gemini-2.5-flash":   {"input": 0.075, "output": 0.30},
    "llama-4-70b-self":   {"input": 0.10,  "output": 0.10},
}

# How much "credit" each tool call costs the rate limiter. The cost
# reflects risk: a refund costs more than a search, an email more than a read.
TOOL_COST_CREDITS = {
    "search_web":     1,
    "get_user":       1,
    "lookup_order":   1,
    "create_ticket":  3,
    "send_email":    10,  # outbound action; double-check before allowing
}


# =============================================================================
# TYPE SYSTEM -- minimal JSON-Schema-like validation
# =============================================================================

# We avoid pulling in `jsonschema` so the lesson runs with stdlib only.
# The schema format is a subset: each arg has {"type": "str"|"int"|"float"|"bool"|"list"|"dict", "required": bool, "default": ...}.
# `required=True` (the default) means the arg must be present.

import re

def _check_type(value, declared: str) -> bool:
    if declared == "str":   return isinstance(value, str)
    if declared == "int":   return isinstance(value, int) and not isinstance(value, bool)
    if declared == "float": return isinstance(value, (int, float)) and not isinstance(value, bool)
    if declared == "bool":  return isinstance(value, bool)
    if declared == "list":  return isinstance(value, list)
    if declared == "dict":  return isinstance(value, dict)
    return False

def validate_args(args: dict, schema: dict) -> tuple[bool, list[str]]:
    """Validate `args` against `schema`. Returns (ok, violations).

    `schema` is `{arg_name: {"type": <type>, "required": bool, "default": ...}}`.
    Extra keys in `args` are flagged as violations (strict mode).
    """
    violations = []
    for key, decl in schema.items():
        present = key in args
        required = decl.get("required", True)
        if not present:
            if required:
                violations.append(f"missing required arg: {key!r}")
            # else: missing optional arg, apply default below
            continue
        value = args[key]
        if not _check_type(value, decl["type"]):
            violations.append(f"arg {key!r}: expected {decl['type']}, got {type(value).__name__}")
    for key in args:
        if key not in schema:
            violations.append(f"unknown arg: {key!r}")
    return (len(violations) == 0, violations)


# =============================================================================
# RESULT ENVELOPES -- tools always return a structured dict
# =============================================================================

def _ok(data) -> dict:
    return {"ok": True, "data": data}

def _err(message: str, *, code: str = "error", **extra) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, **extra}}


# =============================================================================
# IDEMPOTENCY -- every write tool gets a key so retries are safe
# =============================================================================

import hashlib
import time

def make_idempotency_key(tool_name: str, args: dict) -> str:
    """Stable idempotency key for (tool_name, args). Same input -> same key.

    An idempotency key is the contract that says "if I retry this call,
    I will not get a duplicate effect." For reads it's a cache key;
    for writes it's a dedup key. We hash the canonical JSON of args.
    """
    payload = f"{tool_name}|{sorted(args.items())}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]

# In-memory dedup cache. In production this is Redis with a TTL.
_DEDUP: dict[str, dict] = {}

def dedup_or_execute(key: str, fn, *args, **kwargs) -> dict:
    """Return cached result if key has been seen; else execute and cache."""
    if key in _DEDUP:
        return _DEDUP[key]
    result = fn(*args, **kwargs)
    _DEDUP[key] = result
    return result


# =============================================================================
# THE 5 TOOLS
# =============================================================================

def search_web(query: str, top_k: int = 3) -> dict:
    """Search the web for `query`. Returns up to `top_k` mock results.

    Real impl: SerpAPI, Brave, Bing, etc. We return canned results.
    """
    if not query or not query.strip():
        return _err("query must be non-empty", code="invalid_arg")
    if not 1 <= top_k <= 10:
        return _err("top_k must be in [1, 10]", code="invalid_arg")
    canned = [
        {"title": f"Result {i+1} for {query!r}", "url": f"https://example.com/{i+1}", "snippet": f"...{query}..."}
        for i in range(min(top_k, 3))
    ]
    return _ok({"results": canned, "count": len(canned)})


def get_user(user_id: str) -> dict:
    """Look up a user by ID. Returns the user record (mocked)."""
    if not re.match(r"^USR-\d{4,}$", user_id):
        return _err(f"user_id {user_id!r} does not match USR-XXXX", code="invalid_arg")
    return _ok({
        "user_id": user_id,
        "name":    f"User {user_id[-4:]}",
        "email":   f"user{user_id[-4:]}@example.com",
        "tier":    "standard",
    })


def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email. Idempotent on (to, subject, body) -- same triple = same key.

    Real impl: SES, SendGrid, Postmark. We log + return a fake message ID.
    """
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", to):
        return _err(f"to {to!r} is not a valid email", code="invalid_arg")
    if not subject or not subject.strip():
        return _err("subject must be non-empty", code="invalid_arg")
    if not body or not body.strip():
        return _err("body must be non-empty", code="invalid_arg")
    # Idempotency: same (to, subject, body) triple dedupes
    key = make_idempotency_key("send_email", {"to": to, "subject": subject, "body": body})
    def _do_send():
        msg_id = f"MSG-{int(time.time() * 1000)}-{key[:6]}"
        return _ok({"message_id": msg_id, "to": to, "subject": subject, "idempotency_key": key})
    return dedup_or_execute(key, _do_send)


def create_ticket(title: str, body: str, priority: str = "medium") -> dict:
    """Create a support ticket. Idempotent on (title, body)."""
    if not title or not title.strip():
        return _err("title must be non-empty", code="invalid_arg")
    if not body or not body.strip():
        return _err("body must be non-empty", code="invalid_arg")
    if priority not in ("low", "medium", "high", "urgent"):
        return _err(f"priority {priority!r} not in (low, medium, high, urgent)", code="invalid_arg")
    key = make_idempotency_key("create_ticket", {"title": title, "body": body})
    def _do_create():
        ticket_id = f"TKT-{int(time.time() * 1000)}-{key[:6]}"
        return _ok({"ticket_id": ticket_id, "title": title, "priority": priority, "idempotency_key": key})
    return dedup_or_execute(key, _do_create)


def lookup_order(order_id: str) -> dict:
    """Look up an order by ID. Returns order status (mocked)."""
    if not re.match(r"^ORD-\d{4,}$", order_id):
        return _err(f"order_id {order_id!r} does not match ORD-XXXX", code="invalid_arg")
    return _ok({
        "order_id":  order_id,
        "status":    "shipped",
        "eta_days":  2,
        "total_usd": 49.99,
    })


# =============================================================================
# TOOL REGISTRY -- single source of truth for the LLM
# =============================================================================

TOOLS = {
    "search_web": {
        "fn":         search_web,
        "description": "Search the public web for information. Returns up to top_k results.",
        "args_schema": {
            "query":  {"type": "str",  "required": True},
            "top_k":  {"type": "int",  "required": False, "default": 3},
        },
        "returns":     "list of {title, url, snippet}",
        "idempotent":  True,   # read-only
        "side_effects": False,
    },
    "get_user": {
        "fn":         get_user,
        "description": "Look up a user record by user_id (format: USR-XXXX).",
        "args_schema": {
            "user_id": {"type": "str", "required": True},
        },
        "returns":     "{user_id, name, email, tier}",
        "idempotent":  True,
        "side_effects": False,
    },
    "send_email": {
        "fn":         send_email,
        "description": "Send an outbound email. Idempotent on (to, subject, body).",
        "args_schema": {
            "to":      {"type": "str", "required": True},
            "subject": {"type": "str", "required": True},
            "body":    {"type": "str", "required": True},
        },
        "returns":     "{message_id, idempotency_key}",
        "idempotent":  True,
        "side_effects": True,   # writes to the outside world
    },
    "create_ticket": {
        "fn":         create_ticket,
        "description": "Create a support ticket. Idempotent on (title, body).",
        "args_schema": {
            "title":    {"type": "str", "required": True},
            "body":     {"type": "str", "required": True},
            "priority": {"type": "str", "required": False, "default": "medium"},
        },
        "returns":     "{ticket_id, title, priority, idempotency_key}",
        "idempotent":  True,
        "side_effects": True,
    },
    "lookup_order": {
        "fn":         lookup_order,
        "description": "Look up an order by order_id (format: ORD-XXXX). Returns status + ETA.",
        "args_schema": {
            "order_id": {"type": "str", "required": True},
        },
        "returns":     "{order_id, status, eta_days, total_usd}",
        "idempotent":  True,
        "side_effects": False,
    },
}


# =============================================================================
# DISPATCH -- the one entry point the agent calls
# =============================================================================

def call_tool(name: str, args: dict) -> dict:
    """Dispatch a tool call by name. Returns the structured envelope.

    The envelope is always `{"ok": bool, "data": ...}` or `{"ok": False, "error": {...}}`.
    The LLM sees the same shape whether the call succeeded or failed;
    it can branch on `ok` and read `error.message` for self-correction.
    """
    if name not in TOOLS:
        return _err(f"unknown tool: {name!r}", code="unknown_tool",
                    available=list(TOOLS.keys()))
    tool = TOOLS[name]
    ok, violations = validate_args(args, tool["args_schema"])
    if not ok:
        return _err("arg validation failed", code="invalid_args", violations=violations)
    # Apply defaults for missing optional args
    final_args = {}
    for k, decl in tool["args_schema"].items():
        if k in args:
            final_args[k] = args[k]
        elif "default" in decl:
            final_args[k] = decl["default"]
    try:
        result = tool["fn"](**final_args)
        return result
    except Exception as e:
        return _err(f"tool {name!r} raised: {e}", code="tool_exception")


# =============================================================================
# CATALOG -- the prompt the LLM sees
# =============================================================================

def render_tool_catalog_for_llm() -> str:
    """Render the tool registry as a prompt the LLM can read + choose from.

    The format is deliberately close to OpenAI / Anthropic's tool-use spec:
    name, description, parameters (with type + required), returns.
    """
    lines = ["You have access to the following tools:\n"]
    for name, meta in TOOLS.items():
        lines.append(f"### {name}")
        lines.append(f"Description: {meta['description']}")
        lines.append("Parameters:")
        for arg, decl in meta["args_schema"].items():
            req = "required" if decl.get("required", True) else f"optional, default={decl.get('default')!r}"
            lines.append(f"  - {arg} ({decl['type']}, {req})")
        lines.append(f"Returns: {meta['returns']}")
        lines.append(f"Side effects: {meta['side_effects']}")
        lines.append("")
    lines.append("To call a tool, output exactly one line:")
    lines.append('  Action: tool_name({"arg": "value", ...})')
    return "\n".join(lines)


# =============================================================================
# DEMO
# =============================================================================

def demo():
    print("=" * 70)
    print(f"  LESSON {LESSON_NUMBER}: {LESSON_TITLE}")
    print("=" * 70)
    print()
    print("  5 production tools: schema-validated, idempotent, envelope-returning.")
    print()

    # 1. Successful calls
    print("  Successful calls:")
    cases = [
        ("search_web",    {"query": "Qwen 2.5 release", "top_k": 2}),
        ("get_user",      {"user_id": "USR-12345"}),
        ("lookup_order",  {"order_id": "ORD-9001"}),
    ]
    for name, args in cases:
        r = call_tool(name, args)
        flag = "OK " if r["ok"] else "ERR"
        print(f"    [{flag}] {name}({args}) -> {r}")

    # 2. Idempotent writes
    print()
    print("  Idempotent writes (same call twice -> same key):")
    r1 = call_tool("send_email", {"to": "mei@pf.co", "subject": "Hi", "body": "Test"})
    r2 = call_tool("send_email", {"to": "mei@pf.co", "subject": "Hi", "body": "Test"})
    print(f"    1st: {r1}")
    print(f"    2nd: {r2}  (should reuse idempotency key)")
    assert r1["ok"] and r2["ok"]
    assert r1["data"]["idempotency_key"] == r2["data"]["idempotency_key"], "dedup broken"

    # 3. Validation failures
    print()
    print("  Validation failures (good errors, not stack traces):")
    bad_cases = [
        ("get_user",     {"user_id": "bad-format"}),                # regex
        ("send_email",   {"to": "not-an-email", "subject": "x", "body": "y"}),
        ("create_ticket",{"title": "", "body": "ok", "priority": "weird"}),
        ("unknown_tool", {"anything": 1}),
        ("search_web",   {"query": "ok", "top_k": 999}),             # out of range
    ]
    for name, args in bad_cases:
        r = call_tool(name, args)
        flag = "OK " if r["ok"] else "ERR"
        err = r.get("error", {})
        print(f"    [{flag}] {name}({args}) -> code={err.get('code')!r} msg={err.get('message')!r}")

    # 4. The catalog the LLM sees
    print()
    print("  Tool catalog (first 12 lines, the prompt the LLM reads):")
    catalog = render_tool_catalog_for_llm()
    for line in catalog.splitlines()[:12]:
        print(f"    {line}")
    print(f"    ... ({len(catalog.splitlines())} lines total)")
    print()

    # 5. Cost model
    print("  Cost model (per tool, in 'credits' for the rate limiter):")
    for name, c in TOOL_COST_CREDITS.items():
        print(f"    {name:<14} {c:>3} credit(s)")
    print()

    # 6. Pricing for the underlying LLM
    print("  LLM pricing (per 1M tokens, 2026):")
    for model, p in PRICING.items():
        print(f"    {model:<22} in=${p['input']:>6.3f}  out=${p['output']:>6.3f}")
    print()

    # 7. Trade-offs
    print("  Design trade-offs:")
    print("    Schema-strict: catches LLM mistakes early, costs 30 lines of code.")
    print("    Idempotency:    retries are safe; cost is a hash + a dict.")
    print("    Envelopes:      LLM can branch on ok/err without parsing strings.")
    print("    Credit pricing: a refund is 10x a search; the rate limiter reflects risk.")
    print()

    print("=" * 70)


if __name__ == "__main__":
    demo()
