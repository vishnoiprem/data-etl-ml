# Lesson 1 — Function Calling, End-to-End

> **Type:** Article + Worked Example · Course 5
> Let the model call your code — the contract, the patterns, the safety rails. A complete "ops assistant" worked example.

---

## What "function calling" actually is

Function calling is a **structured-output contract** between the LLM and your code. The model returns a JSON object describing a function call; you execute it; you feed the result back. The model is not executing code — it is **requesting** to.

```
   ┌────────────────────────────────────────────────────────────┐
   │  FUNCTION CALLING (the actual flow)                         │
   │                                                            │
   │   USER: "What's the p99 latency for the auth service       │
   │          in the last hour?"                                │
   │                                                            │
   │   LLM (thinking):                                          │
   │     → I need to call get_metric(service="auth",            │
   │                                 metric="p99",              │
   │                                 window="1h")               │
   │   LLM (output): {                                          │
   │     "tool": "get_metric",                                  │
   │     "args": {"service": "auth", "metric": "p99", ...}      │
   │   }                                                        │
   │                                                            │
   │   YOUR CODE:                                               │
   │     args = validate(model_input_args, schema)             │
   │     result = get_metric(**args)                            │
   │     return ToolMessage(content=result, tool_call_id=...)  │
   │                                                            │
   │   LLM (next turn):                                         │
   │     → "The p99 latency for the auth service in the last   │
   │        hour was 142ms, up from 98ms yesterday."            │
   │                                                            │
   └────────────────────────────────────────────────────────────┘
```

The model is the planner. Your code is the executor. The contract is JSON.

---

## The two API shapes: OpenAI vs Anthropic

Both APIs do the same thing; the surface differs:

| | OpenAI tools | Anthropic tools |
|---|---|---|
| Tool definition | `{"type": "function", "function": {"name", "description", "parameters"}}` | `{"name", "description", "input_schema"}` |
| Model output | `tool_calls=[{"id", "function": {"name", "arguments"}}]` | `content=[{"type": "tool_use", "id", "name", "input"}]` |
| Result format | `{"role": "tool", "tool_call_id": "...", "content": "..."}` | `{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "...", "content": "..."}]}` |
| Parallel calls | One message, multiple `tool_calls` | One message, multiple `tool_use` blocks |
| Forced tool | `tool_choice={"type": "function", "function": {"name": "X"}}` | `tool_choice={"type": "tool", "name": "X"}` |

LangChain normalizes both behind `BaseTool`. The differences matter when you're reading raw API traces.

---

## Tool design — the two patterns

```
   PATTERN A: one tool per action                  PATTERN B: one tool per resource
   ──────────────────────────────                  ────────────────────────────────

   get_metric(service, metric, window)             query(service="auth", question=...)
   get_logs(service, level, since)                 "p99 latency last hour"
   create_ticket(title, body, priority)            → returns logs / metrics / tickets
   page_oncall(team, severity)

   Pros:                                         Pros:
   - Easy for the model to pick                   - Easy to add new query types
   - Clear contract per call                       - One tool scales to many use cases
   - Easy to validate args                        - More flexible for the model

   Cons:                                         Cons:
   - Tool explosion (10+ tools → bad pick rate)   - Tool has to be smart about routing
   - Brittle when adding new actions              - Hard to validate "what query means"
```

**Use Pattern A** for well-defined actions with clear arguments (read metrics, create ticket). **Use Pattern B** for exploratory queries where the model needs flexibility. The worked example below uses Pattern A.

---

## The three things you MUST handle

1. **Argument validation.** The model hallucinates. Pydantic catches it.
2. **Execution failures.** Network blips, timeouts, "service down." Retry with backoff.
3. **Side-effect audit.** Anything that mutates state (create ticket, page oncall) goes through an explicit allowlist and an audit log.

If you skip any of these, you'll regret it the first time the model calls `page_oncall` at 3am with the wrong team.

---

## Worked Example — ops assistant with 5 tools

> **Goal:** Let an SRE ask natural-language questions and have the LLM call real tools: `get_metric`, `query_logs`, `get_deployment_status`, `create_ticket`, `page_oncall`. Production-grade: argument validation, timeouts, retries, audit log, eval harness.

### Step 1 — Tool definitions (Pydantic schemas)

```python
# tools/schemas.py
from pydantic import BaseModel, Field
from typing import Literal

class GetMetricArgs(BaseModel):
    service: Literal["auth", "billing", "search", "api"] = Field(
        description="The service to query (must be one of the listed options)"
    )
    metric: Literal["p50", "p95", "p99", "error_rate", "rps"] = Field(
        description="The metric name"
    )
    window: Literal["5m", "15m", "1h", "6h", "24h"] = Field(
        description="The time window"
    )

class QueryLogsArgs(BaseModel):
    service: Literal["auth", "billing", "search", "api"]
    level: Literal["error", "warn", "info", "debug"] = "error"
    since: Literal["5m", "15m", "1h", "6h"] = "1h"
    limit: int = Field(default=10, ge=1, le=100)

class GetDeploymentStatusArgs(BaseModel):
    service: Literal["auth", "billing", "search", "api"]
    environment: Literal["prod", "staging", "canary"] = "prod"

class CreateTicketArgs(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    body: str = Field(min_length=10, max_length=5000)
    priority: Literal["p1", "p2", "p3", "p4"]
    team: str = Field(description="Owning team, e.g., 'auth-platform'")

class PageOncallArgs(BaseModel):
    team: Literal["auth-oncall", "billing-oncall", "platform-oncall", "data-oncall"]
    severity: Literal["sev1", "sev2", "sev3"]
    message: str = Field(min_length=20, max_length=500, description="What's wrong and what you've tried")
```

The schemas are the **contract**. The model picks from these; the validation runs before execution.

### Step 2 — Tool implementations

```python
# tools/impl.py
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

PROMETHEUS_URL = "https://prometheus.internal"
LOKI_URL = "https://loki.internal"
JIRA_URL = "https://jira.internal"
PAGERDUTY_URL = "https://pagerduty.internal"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def get_metric(service: str, metric: str, window: str) -> dict:
    """Read a Prometheus metric. Validated args in."""
    response = requests.post(
        f"{PROMETHEUS_URL}/query",
        json={"query": f'{metric}{{service="{service}"}}', "window": window},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def query_logs(service: str, level: str, since: str, limit: int) -> dict:
    """Read Loki logs. Validated args in."""
    response = requests.post(
        f"{LOKI_URL}/loki/api/v1/query",
        json={"query": f'{{service="{service}", level="{level}"}}', "limit": limit, "since": since},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

def get_deployment_status(service: str, environment: str) -> dict:
    """Read the last deploy for a service in an environment."""
    response = requests.get(
        f"{JIRA_URL}/deploys",
        params={"service": service, "environment": environment},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()

def create_ticket(title: str, body: str, priority: str, team: str) -> dict:
    """Create a Jira ticket. SIDE EFFECT — audited."""
    audit_log("create_ticket", {"title": title, "priority": priority, "team": team})
    response = requests.post(
        f"{JIRA_URL}/issue",
        json={"title": title, "body": body, "priority": priority, "team": team},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

def page_oncall(team: str, severity: str, message: str) -> dict:
    """Page the on-call rotation. HIGH-STAKES SIDE EFFECT — extra guardrails."""
    if severity == "sev1" and not is_within_business_hours() and not is_user_authorized():
        raise PermissionError("sev1 pages outside business hours require on-call lead approval")
    audit_log("page_oncall", {"team": team, "severity": severity, "message": message[:100]})
    response = requests.post(
        f"{PAGERDUTY_URL}/incidents",
        json={"team": team, "severity": severity, "message": message},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
```

Notice:
- `get_metric` and `query_logs` are **read-only** — they retry freely.
- `create_ticket` and `page_oncall` are **side-effecting** — they go through `audit_log` and have guardrails.
- `page_oncall` has an extra check: sev1 pages outside business hours require human approval.

### Step 3 — Wrap as LangChain tools

```python
# tools/langchain_tools.py
from langchain_core.tools import tool

from .schemas import (
    GetMetricArgs, QueryLogsArgs, GetDeploymentStatusArgs,
    CreateTicketArgs, PageOncallArgs,
)
from .impl import (
    get_metric, query_logs, get_deployment_status,
    create_ticket, page_oncall,
)

# Each tool is decorated with @tool, which uses the type hints + docstring to build
# the schema the model sees.

@tool(args_schema=GetMetricArgs)
def get_metric_tool(service: str, metric: str, window: str) -> str:
    """Fetch a Prometheus metric for a service over a time window."""
    result = get_metric(service, metric, window)
    return json.dumps(result)

@tool(args_schema=QueryLogsArgs)
def query_logs_tool(service: str, level: str, since: str, limit: int) -> str:
    """Fetch recent log lines from Loki for a service."""
    result = query_logs(service, level, since, limit)
    return json.dumps([line for line in result["data"]["result"][:limit]])

@tool(args_schema=GetDeploymentStatusArgs)
def get_deployment_status_tool(service: str, environment: str) -> str:
    """Get the most recent deployment for a service in an environment."""
    return json.dumps(get_deployment_status(service, environment))

@tool(args_schema=CreateTicketArgs)
def create_ticket_tool(title: str, body: str, priority: str, team: str) -> str:
    """Create a Jira ticket. Side effect — audited. Use only for real issues."""
    result = create_ticket(title, body, priority, team)
    return f"Created ticket {result['key']}: {result['url']}"

@tool(args_schema=PageOncallArgs)
def page_oncall_tool(team: str, severity: str, message: str) -> str:
    """Page the on-call rotation. HIGH-STAKES — use only for genuine emergencies."""
    result = page_oncall(team, severity, message)
    return f"Paged {team}: incident {result['incident_key']} created"

ALL_TOOLS = [
    get_metric_tool,
    query_logs_tool,
    get_deployment_status_tool,
    create_ticket_tool,
    page_oncall_tool,
]
```

The `@tool` decorator extracts the schema from the Pydantic class. The model sees:
- `name`: the function name
- `description`: from the docstring
- `parameters`: the JSON schema of the Pydantic class

### Step 4 — Bind tools to the model

```python
# chain/ops_chain.py
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage

model = ChatAnthropic(
    model="claude-3-5-sonnet-20240620",
    temperature=0,
).bind_tools(ALL_TOOLS)

SYSTEM = SystemMessage(content="""You are an SRE assistant. Use the available tools to answer
questions about production systems. Always cite the tool calls in your response.
For sev1 pages, confirm the user has on-call lead approval before paging.""")
```

`bind_tools` injects the tool schemas into every model call. The model can choose to call zero, one, or multiple tools per turn.

### Step 5 — The agent loop (tool execution)

```python
# agent/ops_agent.py
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=model,
    tools=ALL_TOOLS,
    state_modifier=SYSTEM,
)

# Run a query
result = agent.invoke({
    "messages": [{"role": "user", "content": "What's the auth service p99 in the last hour?"}],
})

# result["messages"] is the full trace: user → assistant (tool call) → tool result → assistant (answer)
for msg in result["messages"]:
    print(f"{msg.type}: {msg.content[:200] if msg.content else msg.tool_calls}")
```

`create_react_agent` (LangGraph's prebuilt ReAct loop) handles the loop:
1. Model receives messages, decides whether to call a tool.
2. If yes → tool call is executed → result is appended → model re-invoked.
3. If no → final answer is returned.

This is the **agent pattern**: a loop where the model decides whether to act.

### Step 6 — Parallel tool execution

```python
# agent/parallel.py
result = agent.invoke({
    "messages": [{"role": "user", "content": """
        Compare auth and billing p99 latency in the last hour, and tell me
        if either service has had any errors in the same window.
    """}],
})
# Model calls get_metric(auth, p99, 1h), get_metric(billing, p99, 1h),
# query_logs(auth, error, 1h), query_logs(billing, error, 1h) in parallel.
# All 4 execute simultaneously; the model synthesizes.
```

Modern models emit multiple tool calls in one message. LangGraph runs them in parallel. **Read latency drops from 4 sequential calls to 1 round trip.**

### Step 7 — Eval harness

```python
# eval/run_eval.py
from langsmith import evaluate
from agent.ops_agent import agent

# 100 hand-labeled SRE questions with expected tool calls + expected answers
DATASET = "ops-assistant.v1"

def correct_tools(run, example):
    """Did the model call the right tools with the right args?"""
    expected = set(example.outputs["expected_tool_calls"])
    actual = set(
        (tc["name"], tuple(sorted(tc["args"].items())))
        for msg in run.outputs["messages"]
        for tc in (msg.tool_calls or [])
    )
    return {"key": "correct_tools", "score": 1.0 if expected == actual else 0.0}

def tool_arg_accuracy(run, example):
    """For each tool call, are the args valid per the schema?"""
    failures = 0
    total = 0
    for msg in run.outputs["messages"]:
        for tc in (msg.tool_calls or []):
            total += 1
            try:
                schema_class = TOOL_SCHEMAS[tc["name"]]
                schema_class(**tc["args"])
            except Exception:
                failures += 1
    return {"key": "tool_arg_accuracy",
            "score": (total - failures) / total if total else 1.0}

def answer_quality(run, example):
    """LLM-as-judge on the final answer."""
    return LangChainStringEvaluator(
        "labeled_score_string",
        config={"criteria": {"answer": "Is the final answer correct and complete?"}, "normalize_by": 5},
    )(run, example)

results = evaluate(
    agent.invoke,
    data=DATASET,
    evaluators=[correct_tools, tool_arg_accuracy, answer_quality],
    experiment_prefix="ops-assistant-v1",
)

assert results["correct_tools"]["mean"] >= 0.85, "wrong tool selection regressed"
assert results["tool_arg_accuracy"]["mean"] >= 0.98, "arg validation regressed"
```

Three evaluators. **correct_tools** catches wrong tool selection. **tool_arg_accuracy** catches hallucinated args. **answer_quality** judges the final synthesis.

### Step 8 — Failure modes & safeguards

| Failure | How it happens | Safeguard |
|---|---|---|
| Model invents a tool | Hallucination | `tools_by_name` lookup, reject unknown |
| Wrong arg types | Hallucination | Pydantic validation, exception → retry |
| Tool times out | Network/reliability | `tenacity` retry, max 3 |
| Tool has side effect by accident | Bad code | `audit_log` on mutation, explicit list |
| Model pages sev1 at 3am | Edge case | Business-hours check + on-call lead approval |
| Model loops forever | Hallucination | `max_iterations=10` in agent config |
| Tool result too large | Long logs | Truncate to 10K chars before returning |
| Model leaks PII | Logs may contain secrets | Strip secrets before returning |

Every safeguard has a corresponding test in the eval set.

### Step 9 — Cost roll-up

```
   At 500 SRE queries/day, 15K queries/month:
   ──────────────────────────────────────
   Claude Sonnet input (avg 2K tok w/ tool defs):  $3/M × 30M  = $90/mo
   Claude Sonnet output (avg 200 tok):             $15/M × 3M  = $45/mo
   Tool execution (avg 3 tool calls per query):    ~$0.0001/call in infra
   LangSmith traces:                                $50/mo
   ─────────────────────────────────────────
   Total: ~$185/mo for 15K queries = $0.012/query

   Saved: ~$50K/yr vs. building a custom NLU dashboard tool
```

The model is cheap. The infrastructure is cheap. The **human time saved** is the value.

### What this example demonstrates

1. **Tools are Pydantic-validated JSON-schema contracts.** The model picks; you validate.
2. **Read-only tools retry freely; side-effecting tools audit.** Different safety postures.
3. **Parallel tool calls** are free wins in latency.
4. **The agent loop is finite.** `max_iterations` prevents runaway loops.
5. **Eval covers tool selection AND arg validity.** Both are common failure modes.

Read this example and you understand production function calling. Read it twice and you understand the safety rails.

---

## What Comes Next

> Lesson 2 — **Tool design patterns** — when to use one tool per action vs one tool per resource. The tradeoffs at scale.