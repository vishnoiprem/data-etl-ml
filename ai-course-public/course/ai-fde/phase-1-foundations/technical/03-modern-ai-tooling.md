# Lesson 03 — Modern AI Tooling

> **The minimum you need to call an LLM from Python.** 30 minutes. One file, two real SDKs, one mock.

By the end of this lesson you have a **unified LLM client** that:

- Calls **OpenAI** (`gpt-4o-mini`) when `PF_LLM_PROVIDER=openai` and an API key is set
- Calls **Anthropic** (`claude-3-5-haiku`) when `PF_LLM_PROVIDER=anthropic` and an API key is set
- Returns a **deterministic mock** when nothing is set, so the tool demos today even without a key
- Tracks **cost and token usage** so the customer can budget
- Has **retry with backoff** because the API will fail at 2am on demo day

This is the smallest possible "real AI" wrapper. The capstone (lesson 04) is just this client + a prompt + `pf-lookup` from lesson 01.

---

## 🎯 You will build

A 100-line `llm_client.py` that exposes a single function `complete(prompt, system) -> str`. You can swap providers via env vars without changing any caller code.

```python
from llm_client import complete

reply = complete(
    system="You are a logistics CS assistant. Be concise.",
    user="Where is PF-1003?",
)
```

The rest of the lesson is just plumbing.

## 🧠 Concept (5 min)

There are three LLM providers you will realistically use in 2026: **OpenAI**, **Anthropic**, and **Google** (Gemini). Each has its own SDK with a different shape. You have three choices for how to use them:

1. **Vendor lock-in.** Use the OpenAI SDK for everything. Fastest to start, dead-end the day the customer wants Claude.
2. **LiteLLM.** A wrapper that gives you one API and routes to all providers. Great for prototypes. Adds a dependency the customer may not want to maintain.
3. **Your own thin wrapper.** Write 100 lines that call each SDK directly. Boring, no extra dependency, total control, easy to debug.

For an FDE Phase 1 tool, **option 3 is the right call**. The customer does not want to read LiteLLM source code when something breaks at 9am. They want to read your 100 lines.

The wrapper has four responsibilities, in order:

1. **Pick the provider** from env vars. Fail clearly if the customer forgot to set an API key.
2. **Format the request** in that provider's specific way (OpenAI uses `messages`, Anthropic uses `system + messages`).
3. **Call the SDK** with retry. APIs fail. The first thing you should add to any LLM call is `tenacity` retry.
4. **Track cost.** `prompt_tokens * input_price + completion_tokens * output_price`. Append to a `usage.jsonl` file the customer can `tail -f`.

That is the whole lesson. The rest is code.

## 🛠️ Build It (20 min)

### Step 1 — Add the dependencies

```bash
source .venv/bin/activate
python3 -m pip install openai anthropic tenacity python-dotenv
```

Add to a `requirements.txt` so the customer can install on their machine:

```
# Phase 1 — PacificFreight tool
python-dotenv>=1.0
openai>=1.40
anthropic>=0.34
tenacity>=8.2
```

### Step 2 — Pricing table (so cost tracking is honest)

Put this in `technical/03-modern-ai-tooling.py` as a module-level constant. Pricing changes every quarter — this is the 2026 baseline.

```python
PRICING = {
    "gpt-4o-mini":       {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "gpt-4o":            {"input": 5.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "claude-3-5-haiku":  {"input": 0.80 / 1_000_000, "output": 4.00  / 1_000_000},
    "claude-3-5-sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
}
```

When pricing changes, the customer updates this one dict. Not a hidden config file, not a billing dashboard, not a database.

### Step 3 — The unified client

Full file: `technical/03-modern-ai-tooling.py`. It exposes:

```python
def complete(
    *,
    system: str,
    user: str,
    model: str | None = None,        # default from env
    max_tokens: int = 500,
    temperature: float = 0.2,        # low — we want deterministic-ish drafts
) -> CompletionResult: ...
```

`CompletionResult` is a small dataclass:

```python
@dataclass(frozen=True)
class CompletionResult:
    text: str
    model: str
    provider: str            # "openai" | "anthropic" | "mock"
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    is_mock: bool
```

The CS person can `print(result)` and see everything. When the customer asks "how much did this cost us?" the answer is in the dataclass.

### Step 4 — Provider selection

```python
def _select_provider() -> tuple[str, str]:
    """Returns (provider, model). Falls back to mock if nothing is configured."""
    provider = os.getenv("PF_LLM_PROVIDER", "").lower().strip()
    if provider == "openai" and os.getenv("PF_OPENAI_API_KEY"):
        return "openai", os.getenv("PF_MODEL", "gpt-4o-mini")
    if provider == "anthropic" and os.getenv("PF_ANTHROPIC_API_KEY"):
        return "anthropic", os.getenv("PF_MODEL", "claude-3-5-haiku")
    return "mock", os.getenv("PF_MODEL", "mock-deterministic-v1")
```

The fallback to mock is **deliberate**. The customer can run the tool on a plane, on a fresh laptop, in a demo to a regulator — and it always works. The mock returns realistic-shaped text from a small lookup table (e.g., for shipment statuses, returns the right template).

### Step 5 — Retry with backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10),
    retry=retry_if_exception_type((openai.APIError, anthropic.APIError)),
    reraise=True,
)
def _call_openai(system: str, user: str, model: str) -> tuple[str, int, int]:
    ...
```

`wait_exponential_jitter` is the key. Plain exponential backoff causes the entire fleet to retry at the same instant when the API hiccups. Jitter spreads them out.

### Step 6 — Usage logging

Every call appends a JSON line to `usage.jsonl`:

```json
{"ts": "2026-10-09T10:14:23Z", "provider": "openai", "model": "gpt-4o-mini", "input_tokens": 412, "output_tokens": 87, "cost_usd": 0.000114, "latency_ms": 832, "is_mock": false}
```

The customer can `tail -f usage.jsonl` and watch the cost. The FDE can grep for anomalies.

### Step 7 — The mock backend

```python
MOCK_RESPONSES = {
    "PF-1001": "Hi Aisha,\n\nYour shipment PF-1001 was delivered on 7 October 2026 at 14:23, signed for by Nguyen V. B.\n\n— Linh at PacificFreight",
    "PF-1003": "Hi Mei Lin,\n\nYour shipment PF-1003 is currently held at Singapore customs. To release it, we need the import duty payment of SGD 42.50 — please use the link in the SMS sent on 6 October.\n\n— Linh at PacificFreight",
    # ... one per known shipment ID, plus a generic fallback
}

def _mock_complete(system: str, user: str, model: str) -> tuple[str, int, int]:
    """Return a deterministic reply based on a shipment ID in the user prompt."""
    for shipment_id, reply in MOCK_RESPONSES.items():
        if shipment_id in user:
            return reply, len(user.split()), len(reply.split())
    # Generic fallback — realistic but useless for actual sending.
    return ("(mock) I would draft a reply here, but I have no shipment to reference. "
            "Set PF_LLM_PROVIDER and an API key to get a real response."), 10, 25
```

The mock is **deterministic and inspectable**. When you demo to the customer, the same input always produces the same output. You can show them the reply and say "this is what the model produced — if you don't like the wording, we change the prompt, not the code."

### Step 8 — Run it

```bash
# Mock mode (no API key)
python3 technical/03-modern-ai-tooling.py

# Real OpenAI mode
export PF_LLM_PROVIDER=openai
export PF_OPENAI_API_KEY=sk-...
python3 technical/03-modern-ai-tooling.py

# Real Anthropic mode
export PF_LLM_PROVIDER=anthropic
export PF_ANTHROPIC_API_KEY=sk-ant-...
export PF_MODEL=claude-3-5-haiku
python3 technical/03-modern-ai-tooling.py
```

Each run prints:
- the chosen provider + model
- the input/output text
- token counts
- cost in USD
- latency in ms
- one JSON line appended to `usage.jsonl`

## 🏛️ FDE Lens — the one question to ask the client

> *"Do you have an existing relationship with OpenAI, Anthropic, or another LLM provider — and is there a procurement constraint on which one I should use?"*

Some customers (financial, government) have pre-negotiated contracts. Some have a strict no-data-leaves-region rule that rules out US providers. Some are fine with whatever is cheapest. The answer determines `PF_LLM_PROVIDER` for the whole engagement.

A second question, often missed:

> *"What is the monthly ceiling I should alert you at?"*

Set a daily cost cap in the code (`PF_DAILY_BUDGET_USD=5.00`). When the tool hits it, it switches to the mock and writes a warning to the log. The customer never gets a surprise $4,000 OpenAI bill because a CS person accidentally pasted 10,000 emails into the tool.

## 🌙 Reflect

Write 3-5 sentences:

1. Why do we use `tenacity` with jitter, not just a `while` loop with `time.sleep(2**attempt)`?
2. The mock backend is deterministic. Why is that a feature, not a limitation, in a customer demo?
3. The pricing table is a Python constant in the source file. Why is that better than reading it from a config file or environment variable?
4. When would you call `_call_openai` directly instead of going through `complete()`?

**What's next** — Lesson 04 puts the lookup from lesson 01 and the LLM client from lesson 03 together. You will read an email, extract the shipment ID, look it up, and draft a reply — all in one CLI. That is the **first working AI tool** that is the deliverable of Phase 1.
