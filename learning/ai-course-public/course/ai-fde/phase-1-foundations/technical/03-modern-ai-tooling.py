"""
Lesson 03 — Unified LLM client for the PacificFreight tool.

What you should be able to explain to a client after this lesson:
- Why we have a mock backend that always works, even without an API key.
- Why every call is retried with exponential backoff + jitter.
- Why cost is tracked on every call (the customer will ask).

How to run:
    # Mock mode (no API key needed)
    python3 technical/03-modern-ai-tooling.py

    # Real OpenAI
    export PF_LLM_PROVIDER=openai
    export PF_OPENAI_API_KEY=sk-...
    python3 technical/03-modern-ai-tooling.py

    # Real Anthropic
    export PF_LLM_PROVIDER=anthropic
    export PF_ANTHROPIC_API_KEY=sk-ant-...
    export PF_MODEL=claude-3-5-haiku
    python3 technical/03-modern-ai-tooling.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

load_dotenv()

# Lazy SDK imports — only the provider the customer chose is loaded.
try:
    import openai  # type: ignore
except ImportError:  # pragma: no cover
    openai = None  # type: ignore

try:
    import anthropic  # type: ignore
except ImportError:  # pragma: no cover
    anthropic = None  # type: ignore


# ---------------------------------------------------------------------------
# Pricing (USD per token, 2026 baseline). Update this when vendors change.
# ---------------------------------------------------------------------------
PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-mini":       {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "gpt-4o":            {"input": 5.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "claude-3-5-haiku":  {"input": 0.80 / 1_000_000, "output": 4.00  / 1_000_000},
    "claude-3-5-sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
}


# ---------------------------------------------------------------------------
# Result type — one struct the customer can print, log, or budget against.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CompletionResult:
    text: str
    model: str
    provider: str           # "openai" | "anthropic" | "mock"
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    is_mock: bool


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------
def _select_provider() -> tuple[str, str]:
    provider = os.getenv("PF_LLM_PROVIDER", "").lower().strip()
    if provider == "openai" and os.getenv("PF_OPENAI_API_KEY"):
        return "openai", os.getenv("PF_MODEL", "gpt-4o-mini")
    if provider == "anthropic" and os.getenv("PF_ANTHROPIC_API_KEY"):
        return "anthropic", os.getenv("PF_MODEL", "claude-3-5-haiku")
    return "mock", os.getenv("PF_MODEL", "mock-deterministic-v1")


# ---------------------------------------------------------------------------
# Cost calculation
# ---------------------------------------------------------------------------
def _cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING.get(model)
    if not p:
        return 0.0
    return round(p["input"] * input_tokens + p["output"] * output_tokens, 6)


# ---------------------------------------------------------------------------
# Mock backend — deterministic, runs without an API key.
# In a real demo this is what you show when you want to control the output.
# ---------------------------------------------------------------------------
MOCK_RESPONSES: dict[str, str] = {
    "PF-1001": (
        "Hi Aisha,\n\n"
        "Your shipment PF-1001 was delivered on 7 October 2026 at 14:23, "
        "signed for by Nguyen V. B.\n\n"
        "No further action is needed. If anything looks off, just reply and "
        "we will investigate.\n\n"
        "— Linh at PacificFreight"
    ),
    "PF-1003": (
        "Hi Mei Lin,\n\n"
        "Your shipment PF-1003 is currently held at Singapore customs because "
        "an import duty invoice has been issued and is awaiting payment.\n\n"
        "To release it, please pay the SGD 42.50 import duty via the link in "
        "the SMS sent on 6 October. Once we receive it, clearance usually "
        "takes 1-2 business days.\n\n"
        "— Linh at PacificFreight"
    ),
    "PF-1004": (
        "Hi Carlos,\n\n"
        "I am sorry for the delay on PF-1004. Our records show two delivery "
        "attempts were made but the address was unreachable, and we have not "
        "been able to reach you by phone. We will re-attempt delivery on "
        "10 October. If that does not work, please reply with a better time "
        "and a number we can call you on.\n\n"
        "I would like to talk to you directly about this — a manager from our "
        "team will call you within the next business day.\n\n"
        "— Linh at PacificFreight"
    ),
    "PF-1008": (
        "Hi Sarah,\n\n"
        "I want to flag a problem with PF-1008: a damaged carton was noted "
        "on arrival at our Sydney hub. The team has photos on file and has "
        "already contacted the sender for instructions.\n\n"
        "We will follow up with you by end of day tomorrow with the sender's "
        "decision (re-ship, refund, or partial credit). No action needed "
        "from you yet.\n\n"
        "— Linh at PacificFreight"
    ),
}

MOCK_FALLBACK = (
    "[mock] I would draft a reply here based on the shipment status, but no "
    "shipment ID was found in the email. Set PF_LLM_PROVIDER and an API key "
    "to get a real response, or ensure the email contains a PF-XXXX reference."
)


def _mock_complete(system: str, user: str) -> tuple[str, int, int]:
    """Deterministic mock — picks the shipment ID from the "Shipment in tracker:
    ID: PF-XXXX" line in the user prompt and returns a canned reply for that
    specific shipment. This is robust to the customer's email containing
    multiple unrelated PF references.

    If no known shipment ID is found, returns a generic fallback.
    """
    # Look ONLY at the "Shipment in tracker: ID: PF-XXXX" line.
    import re
    m = re.search(r"^[-•]\s*ID:\s*(PF-\d{4,5})\b", user, re.MULTILINE)
    if m:
        target = m.group(1).upper()
        if target in MOCK_RESPONSES:
            reply = MOCK_RESPONSES[target]
            return reply, len(user.split()), len(reply.split())
    return MOCK_FALLBACK, len(user.split()), len(MOCK_FALLBACK.split())


# ---------------------------------------------------------------------------
# OpenAI call — with retry, jitter, cost tracking.
# ---------------------------------------------------------------------------
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_openai(system: str, user: str, model: str) -> tuple[str, int, int]:
    if openai is None:
        raise RuntimeError("openai SDK not installed. Run: pip install openai")
    client = openai.OpenAI(api_key=os.environ["PF_OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=500,
        temperature=0.2,
    )
    text = resp.choices[0].message.content or ""
    usage = resp.usage
    return text, (usage.prompt_tokens or 0), (usage.completion_tokens or 0)


# ---------------------------------------------------------------------------
# Anthropic call — with retry, jitter, cost tracking.
# ---------------------------------------------------------------------------
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_anthropic(system: str, user: str, model: str) -> tuple[str, int, int]:
    if anthropic is None:
        raise RuntimeError("anthropic SDK not installed. Run: pip install anthropic")
    client = anthropic.Anthropic(api_key=os.environ["PF_ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=model,
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = ""
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            text += block.text
    return text, resp.usage.input_tokens, resp.usage.output_tokens


# ---------------------------------------------------------------------------
# Usage log — append one JSON line per call. Customer can `tail -f`.
# ---------------------------------------------------------------------------
def _log_usage(result: CompletionResult) -> None:
    path = Path(os.getenv("PF_USAGE_LOG", "usage.jsonl"))
    with path.open("a") as fh:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            **{k: v for k, v in asdict(result).items() if k != "text"},
        }
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Public API — the one function every caller in Phase 1 uses.
# ---------------------------------------------------------------------------
def complete(
    *,
    system: str,
    user: str,
    max_tokens: int = 500,         # noqa: ARG001 — wired in for future callers
    temperature: float = 0.2,      # noqa: ARG001
) -> CompletionResult:
    """Call the configured LLM provider. Falls back to mock if unconfigured."""
    provider, model = _select_provider()
    start = time.monotonic()

    if provider == "openai":
        text, in_t, out_t = _call_openai(system, user, model)
    elif provider == "anthropic":
        text, in_t, out_t = _call_anthropic(system, user, model)
    else:
        text, in_t, out_t = _mock_complete(system, user)

    latency_ms = int((time.monotonic() - start) * 1000)
    result = CompletionResult(
        text=text,
        model=model,
        provider=provider,
        input_tokens=in_t,
        output_tokens=out_t,
        cost_usd=_cost(model, in_t, out_t),
        latency_ms=latency_ms,
        is_mock=(provider == "mock"),
    )
    _log_usage(result)
    return result


# ---------------------------------------------------------------------------
# Demo / smoke test
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a customer-service assistant for PacificFreight Co., a "
    "cross-border logistics SMB. You draft concise, factual replies in the "
    "customer's language. You never invent a status you weren't given."
)
USER_PROMPT = (
    "Customer email:\n"
    "Hi, can you check on my shipment PF-1003? I was told it would arrive "
    "last week but I haven't received anything. — Mei Lin\n\n"
    "Current tracker status: held_customs, last event 'Held at Singapore "
    "customs — import duty invoice issued, awaiting payment.' "
    "Action required: customer to pay SGD 42.50 import duty.\n\n"
    "Draft a reply."
)


def main() -> int:
    result = complete(system=SYSTEM_PROMPT, user=USER_PROMPT)
    print("=" * 70)
    print(f"provider : {result.provider}  ({'MOCK' if result.is_mock else 'REAL'})")
    print(f"model    : {result.model}")
    print(f"tokens   : in={result.input_tokens}  out={result.output_tokens}")
    print(f"cost     : ${result.cost_usd:.6f}")
    print(f"latency  : {result.latency_ms} ms")
    print("=" * 70)
    print(result.text)
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
