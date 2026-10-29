# Lesson 1 — The LangChain Mental Model

> **Type:** Article + Worked Example · Course 1
> What LangChain is, what it does for you, what it costs you, and a full production-grade chain to anchor the mental model.

---

## What LangChain actually is

Strip away the marketing and LangChain is three things:

1. **A standard interface for LLMs.** `ChatModel.invoke(messages) → AIMessage`. Same call works on Claude, GPT, Gemini, OSS, local.
2. **A composition language (LCEL).** The `|` operator composes `Runnable`s. `prompt | model | parser` is the canonical pattern.
3. **An ecosystem of integrations.** Loaders, retrievers, vector stores, toolkits, evaluators, callbacks, tracers.

Everything else is decoration on top.

```
   LangChain = (Standard Interfaces) + (Composition) + (Integrations)
                  ▲                       ▲                ▲
                  │                       │                │
              ChatModel               Runnable         600+ integrations
              Embeddings              LCEL |          (loaders, retrievers,
              VectorStore             RunnablePassthrough    vector DBs, ...)
              Retriever
              Tool
```

If you understand these three, you understand 80% of LangChain.

---

## The Runnable contract

`Runnable` is the type every chain component implements. Six methods, six behaviors:

```
   ┌────────────────────────────────────────────────────────────┐
   │  Runnable (the contract)                                    │
   │                                                            │
   │   invoke(input)        ──► output         one-shot call   │
   │   batch([inputs])      ──► [outputs]      bulk call       │
   │   stream(input)        ──► yield chunks   token stream    │
   │   ainvoke / abatch / astream                                          │
   │                       ──► same shape, async variants         │
   │   astream_events(input)──► yield events  token + lifecycle │
   │   with_config({...})   ──► Runnable     attach metadata   │
   └────────────────────────────────────────────────────────────┘
```

`prompt | model | parser` produces a `Runnable[Dict, ParsedType]`. Every component obeys the same contract. That's why composition works.

---

## LCEL — the `|` operator

LCEL is **not magic**. It is `Runnable.bind` + `Runnable.__or__`. The expression

```python
chain = prompt | model | parser
```

is shorthand for

```python
chain = RunnableSequence(
    first=prompt,
    middle=[model],
    last=parser,
)
```

`invoke` walks the sequence. `stream` streams from the last `Runnable` that supports streaming (usually the model) and runs the rest in parallel.

| LCEL idiom | What it does |
|---|---|
| `prompt \| model \| parser` | Linear chain, three components |
| `prompt \| model.bind(stop="...") \| parser` | Bind kwargs at runtime |
| `prompt \| RunnableParallel({"a": chain_a, "b": chain_b})` | Fan-out, then merge |
| `RunnablePassthrough.assign(x=chain_x)` | Pass input through, add a derived field |
| `chain.with_fallbacks([chain_b, chain_c])` | Try alternatives on failure |
| `chain.with_retry(stop_after_attempt=3)` | Retry on transient errors |
| `chain.with_config({"run_name": "..."})` | Attach metadata for tracing |

These seven idioms cover 90% of production chains.

---

## The "LangChain tax"

LangChain's promise is **velocity**. The cost is **abstraction leakage**.

| Stage | What LangChain saves you | What it costs you |
|---|---|---|
| Prototype | 2 days of glue code | Indirection you can't debug without reading source |
| First 100 users | Standard interfaces across providers | Hidden costs (callbacks add latency) |
| First 10K users | Tracing, callbacks, retries built-in | Bizarre errors from version mismatches |
| First 100K users | "Just swap providers" | Migrating off is 2 weeks of pain |

**The mitigation:** treat LangChain as a **thin standard interface**, not a framework. Use the integrations; keep the chains you write to 3–4 components. Resist the urge to nest 8 RunnableLambdas.

---

## The mental model in one diagram

```
   ┌─────────────────────────────────────────────────────────┐
   │                  LANGCHAIN MENTAL MODEL                 │
   │                                                         │
   │   INPUT                                                 │
   │     │                                                   │
   │     ▼                                                   │
   │   ┌─────────────────┐                                   │
   │   │   PROMPT        │  ChatPromptTemplate, messages      │
   │   │   (templates,   │  partials, few-shot               │
   │   │    history)     │                                   │
   │   └────────┬────────┘                                   │
   │            │ PromptValue                                │
   │            ▼                                            │
   │   ┌─────────────────┐                                   │
   │   │   MODEL         │  ChatModel (Claude, GPT, OSS)      │
   │   │                 │  invoke / stream / batch           │
   │   └────────┬────────┘                                   │
   │            │ AIMessage (or chunks)                      │
   │            ▼                                            │
   │   ┌─────────────────┐                                   │
   │   │   PARSER        │  Str / JSON / Pydantic / XML      │
   │   │                 │  OutputFixingParser on fail       │
   │   └────────┬────────┘                                   │
   │            │ typed output                                │
   │            ▼                                            │
   │   OUTPUT                                                │
   │                                                         │
   │   wrapped in:                                            │
   │     .with_config()  ─► metadata for tracing             │
   │     .with_retry()   ─► transient-error handling         │
   │     .with_fallbacks()─► provider failover               │
   │     .with_types()   ─► schema for self-validation       │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
```

That's it. Six components: input, prompt, model, parser, output, wrapper. Every LangChain app reduces to this.

---

## The "do I need LangChain?" test

You probably don't need it if:
- Single LLM call, no chaining
- No retrieval, no tools, no agents
- No streaming required

You probably do need it if:
- Multi-step pipeline (retrieval → rerank → LLM)
- Streaming + structured output + retries
- Multi-provider abstraction (Anthropic, OpenAI, OSS)
- LangSmith tracing
- Production observability

If you need it, use LCEL, not the old `LLMChain` API. The old API is being deprecated.

---

## What you'll build in the worked example

A **support-ticket triage chain** that:

1. Accepts raw ticket text.
2. Extracts structured fields (priority, category, sentiment, summary) as a Pydantic object.
3. Falls back to a smaller, cheaper model on parse failure.
4. Streams tokens to the client.
5. Logs every trace to LangSmith with cost metadata.
6. Has a 200-ticket eval set with both exact-match and LLM-as-judge scoring.

This is the smallest chain that touches every concept in the course. The same pattern scales to retrieval, tool use, and agents in later courses.

---

## Worked Example — Support-ticket triage chain, end-to-end

> **Goal:** Take a raw support ticket (subject + body), extract `{priority, category, sentiment, summary}`, return as a typed Pydantic object. Streaming. Eval-driven. Cost-aware. ~$0.0008/ticket at scale.

### The architecture in one expression

```python
chain = (
    triage_prompt
    | ChatAnthropic(model="claude-3-5-haiku-20241022", temperature=0)
    | PydanticOutputParser(pydantic_object=TriageResult)
).with_fallbacks(
    [fallback_chain]                           # smaller model on parse fail
).with_retry(
    stop_after_attempt(3),
    retry_if_exception_type=(RateLimitError,)
).with_config({
    "run_name": "triage",
    "metadata": {"env": "prod", "version": "1.2"},
})
```

That's the entire chain. The rest of the worked example is **wiring** — prompts, schemas, parsers, fallbacks, eval, and observability.

### Step 1 — Define the output schema (Pydantic is the contract)

```python
# triage/schema.py
from pydantic import BaseModel, Field
from enum import Enum

class Priority(str, Enum):
    p1 = "p1"     # outage / revenue impact
    p2 = "p2"     # degraded but workaround
    p3 = "p3"     # cosmetic / non-urgent

class Category(str, Enum):
    billing = "billing"
    auth = "auth"
    performance = "performance"
    bug = "bug"
    how_to = "how_to"
    other = "other"

class Sentiment(str, Enum):
    angry = "angry"
    frustrated = "frustrated"
    neutral = "neutral"
    happy = "happy"

class TriageResult(BaseModel):
    priority: Priority = Field(description="p1 = outage/revenue, p2 = degraded, p3 = cosmetic")
    category: Category = Field(description="one of the defined buckets")
    sentiment: Sentiment = Field(description="emotional tone of the author")
    summary: str = Field(description="<= 20 words, the user's actual ask")
    confidence: float = Field(ge=0.0, le=1.0, description="model self-rated confidence")
```

Why Pydantic:
- The model produces structured output directly. No regex parsing.
- The schema is the spec. Every downstream consumer knows the shape.
- Validation catches drift: if the model says `priority="P0"`, you know it's hallucinating.

### Step 2 — Build the prompt (template + parser instructions)

```python
# triage/prompt.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from .schema import TriageResult

parser = PydanticOutputParser(pydantic_object=TriageResult)

triage_prompt = ChatPromptTemplate.from_messages([
    ("system", """You triage customer support tickets for a SaaS product.

Return JSON that matches the schema below. Use the enum values exactly.
- priority: p1 (revenue-impacting outage), p2 (degraded, workaround), p3 (cosmetic)
- category: pick the closest bucket
- sentiment: angry if hostile language, happy if praising
- summary: ≤ 20 words, the user's actual ask, no filler
- confidence: 0.0-1.0; rate lower if the ticket is ambiguous

{format_instructions}
"""),
    ("human", """Subject: {subject}

Body:
{body}"""),
]).partial(
    format_instructions=parser.get_format_instructions(),
)
```

`{format_instructions}` is a partial variable. LangChain injects the JSON schema the parser expects. The model fills it.

### Step 3 — Compose the chain (LCEL)

```python
# triage/chain.py
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

from .prompt import triage_prompt, parser
from .schema import TriageResult

model = ChatAnthropic(model="claude-3-5-haiku-20241022", temperature=0)

primary = triage_prompt | model | parser

# Fallback: smaller model + retry of JSON extraction
fallback_model = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)
fallback_chain = triage_prompt | fallback_model | parser

chain = (
    primary
    .with_fallbacks([fallback_chain])
    .with_retry(
        stop_after_attempt=3,
        retry_if_exception_type=(RateLimitError,),
    )
    .with_config({"run_name": "triage.v1"})
)
```

`with_fallbacks` runs `primary` first; if it raises (parse failure, schema violation), it runs `fallback_chain`. `with_retry` retries transient errors before falling back.

### Step 4 — Wire tracing (LangSmith is one env var)

```python
# .env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=support-triage
ANTHROPIC_API_KEY=sk-ant-...
```

That's it. Every chain invocation is logged to LangSmith with full prompt, response, latency, tokens, and cost. No code change.

### Step 5 — Streaming variant

```python
# triage/stream.py
async def stream_ticket(subject: str, body: str):
    # For streaming, parse the partial text manually as it arrives.
    # (Pydantic needs the full response.)
    text_chain = triage_prompt | ChatAnthropic(...)

    async for chunk in text_chain.astream({"subject": subject, "body": body}):
        yield chunk       # send to client as Server-Sent Events
```

For UI streaming you typically stream the raw text. For backend processing you want the parsed object (skip streaming). Pick one per call site.

### Step 6 — Eval harness (the part most teams skip)

```python
# eval/run_eval.py
from langsmith import evaluate
from langsmith.evaluation import LangChainStringEvaluator

from triage.chain import chain
from eval.dataset import load_eval_set

# 200 tickets, hand-labeled with the expected TriageResult.
dataset_name = "support-ticket-triage.v1"

# Exact-match scorer
def exact_match(run, example: dict):
    expected = example.outputs["triage"]
    actual = run.outputs["triage"]
    return 1.0 if expected == actual else 0.0

# LLM-as-judge for the free-text summary field
summary_judge = LangChainStringEvaluator(
    "labeled_score_string",
    config={
        "criteria": {
            "summary": "Is the summary accurate, ≤ 20 words, and captures the user's actual ask?"
        },
        "normalize_by": 5,
    },
)

results = evaluate(
    chain,
    data=dataset_name,
    evaluators=[exact_match, summary_judge],
    experiment_prefix="claude-haiku-v1",
)

# CI gate: fail if exact_match < 0.85 OR summary_judge < 4.0
assert results["exact_match"]["mean"] >= 0.85, "exact-match regressed"
assert results["summary_judge"]["mean"] >= 4.0, "summary quality regressed"
```

This is the gate that **prevents regressions**. Every PR that touches the prompt, the model, or the parser runs this eval. If a "small change" drops exact-match from 0.91 to 0.84, the PR is blocked.

### Step 7 — Eval dataset (200 tickets, hand-labeled)

```python
# eval/dataset.py
TICKETS = [
    {
        "inputs": {
            "subject": "URGENT: Production DB is read-only",
            "body": "All our queries are timing out. This is costing us revenue. NEED HELP NOW.",
        },
        "outputs": {
            "triage": {
                "priority": "p1",
                "category": "performance",
                "sentiment": "angry",
                "summary": "Production database read-only, queries timing out, revenue impact",
                "confidence": 0.95,
            }
        },
    },
    # ... 199 more, hand-labeled over 2 days
]

# Upload once, reuse forever
from langsmith import Client
client = Client()
client.upload_examples(dataset_id=..., examples=TICKETS)
```

**The eval set is the moat.** The prompt is replaceable. The eval set is what makes the system *testable*.

### Step 8 — Cost math

```
   Per ticket (Haiku 4.5, primary model):
   ─────────────────────────────────────
   Input:   ~500 tokens (system + ticket)  = $0.0004
   Output:  ~80 tokens (JSON)              = $0.0004
                                    Total:   ~$0.0008

   Per ticket (Haiku 3, fallback):
   ─────────────────────────────────────
   Input:   ~500 tokens  = $0.000125
   Output:  ~80 tokens   = $0.0001
                                    Total:   ~$0.000225

   At 50K tickets/day:
   ─────────────────────────────────────
   Primary:  50K × $0.0008    = $40/day  = $1,200/mo
   Fallback:  5% × $0.000225   = $0.56/day = $17/mo
   LangSmith traces:                    = $50/mo
                              Total:    ~$1,267/mo
```

That's $25 per million tickets. Cheap enough to run on every inbound ticket, not just "the important ones."

### Step 9 — Failure modes the eval set must catch

| Failure | Symptom | Eval catches it? |
|---|---|---|
| Model returns `"P0"` instead of `"p1"` | Pydantic validation error | Yes — exact_match = 0 |
| Model invents a category not in the enum | Pydantic validation error | Yes |
| Model returns prose instead of JSON | Parser exception → fallback chain | Yes (fallback path) |
| Model is confident-wrong (says `p3` on an outage) | Wrong priority | Yes — exact_match |
| Model's summary is accurate but 40 words long | Violates "≤ 20 words" | Yes — LLM-as-judge |
| Provider outage (Anthropic 5xx) | Exception | Yes — `with_retry` handles transient |
| Prompt change silently lowers quality | Subtle drift | **Only if eval set is run on every PR.** |

The last row is the one that bites teams who treat eval as "we'll add it later."

### Step 10 — Production wiring

```python
# app/main.py — FastAPI
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from triage.chain import chain
from triage.schema import TriageResult
from pydantic import BaseModel

app = FastAPI()

class TicketIn(BaseModel):
    subject: str
    body: str

@app.post("/triage")
def triage(ticket: TicketIn):
    result: TriageResult = chain.invoke({
        "subject": ticket.subject,
        "body": ticket.body,
    })
    return {"priority": result.priority, "summary": result.summary, ...}
```

One POST endpoint. The chain does everything.

### The five things this example teaches

1. **LCEL is just `Runnable.__or__`.** `prompt | model | parser` is the canonical pattern; everything is composition.
2. **Pydantic is the contract.** The model returns JSON; the parser validates it; downstream code consumes a typed object.
3. **`with_fallbacks` + `with_retry` are non-negotiable.** Production chains fail. Plan for it.
4. **LangSmith tracing is one env var.** Don't write your own logging.
5. **The eval set is the moat.** A 200-ticket hand-labeled set with CI gating beats any prompt-engineering technique.

Read this example once and you understand the chain. Read it twice and you understand the system.

---

## What Comes Next

> Lesson 2 — **Models & message types** — the ChatModel contract, message roles (system / human / ai / tool), and the multi-provider abstraction.