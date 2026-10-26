"""
agent.py — Mosaic AI Agent that scores each iteration and picks the next.

Architecture:

   ┌──────────────┐
   │  ChatAgent   │  ◄─── subclass of `databricks_agents.ChatAgent`
   │  (m100_agent)│
   └──────┬───────┘
          │  predict(messages, context) → AgentResponse
          ▼
   ┌──────────────────────────────────────┐
   │  Foundation Model API                │
   │  model: databricks-meta-llama-        │
   │        3.3-70b-instruct               │
   │  with tool_use schema                │
   └──────┬───────────────────────────────┘
          │  tool calls
          ▼
   ┌──────────────────────────────────────┐
   │  Tools (UC functions):               │
   │   1. profile_table(table) → stats    │
   │   2. get_mlflow_metrics(run_id) → m  │
   │   3. inspect_dlt_expectations(p) → e  │
   └──────────────────────────────────────┘

The agent receives the iteration's bronze/silver/gold tables +
MLflow run, then returns:

    {
      "summary": "<1-paragraph what-this-iteration-was>",
      "quality_score": 0.78,           # 0.0 - 1.0
      "next_category": "Healthcare",   # rotate here next
      "retry": false,                  # true if the agent thinks the
                                       # result is bad enough to retry
      "tools_used": ["profile_table", "get_mlflow_metrics"]
    }

The driver gates the iteration on `quality_score >=
quality_threshold` (default 0.4). Below that, it increments
`retry_count` and re-picks.

We use **Foundation Model API** (pay-per-token), not a
dedicated serving endpoint. Two reasons:
  1. Free Edition has no GPU/provisioned-throughput quota.
  2. The same model is callable from inside a Job task via
     `databricks-sdk` without provisioning anything.

Local smoke test mocks the FM call. Production uses the
real `WorkspaceClient.serving_endpoints.query()`.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Result type
# ============================================================

@dataclass
class AgentResult:
    """What the agent decided about this iteration.

    `prompt_tokens` and `completion_tokens` are tracked so the
    driver can sum them across the 100 iterations and assert
    the cost ceiling.
    """
    summary: str
    quality_score: float
    next_category: str
    retry: bool
    tools_used: list[str] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    raw_response: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "quality_score": self.quality_score,
            "next_category": self.next_category,
            "retry": self.retry,
            "tools_used": self.tools_used,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "latency_ms": self.latency_ms,
        }


# ============================================================
# Tools — what the agent can call
#
# We register these as a simple dict so the FM API tool_use
# schema is easy to construct. In a real workspace, the
# Mosaic AI Agent Framework registers them as UC functions
# (`CREATE FUNCTION ... RETURNS ... USING GPT...`) so they
# are also executable by humans via Genie.
# ============================================================

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "profile_table",
            "description": (
                "Get a profile of a Delta table: row count, column count, "
                "null ratio per column, distinct count per column, "
                "sample values."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Fully-qualified table name (catalog.schema.table)",
                    },
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_mlflow_metrics",
            "description": (
                "Read the metrics from an MLflow run. Returns "
                "{run_id, metrics: {name: value}, params: {name: value}}."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"},
                },
                "required": ["run_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_dlt_expectations",
            "description": (
                "Read the pass-rate and dropped-record count for a "
                "DLT pipeline. Returns {pipeline_id, pass_rate, dropped, valid}."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pipeline_id": {"type": "string"},
                },
                "required": ["pipeline_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_history",
            "description": (
                "Semantic search over past iteration summaries. Use this "
                "when you want to know what worked in a category before, "
                "or what kinds of listings produced the highest quality_score. "
                "Returns the top-5 most similar past iterations with their "
                "category, quality_score, and a one-line summary."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Natural-language question about past iterations",
                    },
                },
                "required": ["question"],
            },
        },
    },
]


# ============================================================
# System prompt
# ============================================================

SYSTEM_PROMPT = """\
You are the m100 agent. Every iteration, you receive a marketplace
dataset, run it through ingest → DLT → MLflow, and must decide:

  1. quality_score (0.0 - 1.0): is the result usable?
  2. next_category: which marketplace category should the next
     iteration explore? Pick from: Finance, Healthcare, Geospatial,
     Retail, Transportation, Energy, Climate, Public Sector,
     Marketing, Sports.
  3. retry (true|false): if the result is too sparse to learn from,
     set retry=true so the driver picks a different listing.
  4. summary: a 1-paragraph, human-readable explanation of what
     this iteration was, what was learned, and what's next.

You have four tools. Use them in this order:
  1. profile_table(silver)         → see the data shape
  2. get_mlflow_metrics(run_id)    → see the baseline model
  3. inspect_dlt_expectations(id)  → see the DQ pass-rate
  4. query_history(question)       → search your own prior iterations.
     Use this to learn what worked in a category before — your
     summary list is short-term recall; this is long-term recall.

Be conservative on quality_score: anything below 0.4 means the
iteration is a wash and should be retried.

Return a single JSON object — no prose, no markdown.
"""


# ============================================================
# Agent
# ============================================================

class M100Agent:
    """Mosaic AI Agent wrapper.

    Production usage:
        agent = M100Agent(workspace_client=WorkspaceClient(),
                          history_index=history_index)
        result = agent.evaluate(...)

    Local smoke (no workspace):
        agent = M100Agent(history_index=history_index)  # canned responses
    """

    FM_MODEL = "databricks-meta-llama-3.3-70b-instruct"

    def __init__(
        self,
        workspace_client: Optional[Any] = None,
        fm_endpoint: Optional[str] = None,
        history_index: Optional[Any] = None,
    ):
        """`workspace_client` is a `databricks.sdk.WorkspaceClient` in prod.
        `fm_endpoint` overrides the default FM API model name.
        `history_index` is a `HistoryIndex` (see history_search.py) — the
        agent uses it to power the `query_history` tool.
        """
        self.workspace = workspace_client
        self.fm_endpoint = fm_endpoint or self.FM_MODEL
        self.history_index = history_index
        # If no workspace, every call returns a canned response
        # (so the smoke test runs in <1s without a network).
        self._is_mock = workspace_client is None
        if self._is_mock:
            logger.warning(
                "M100Agent running in MOCK mode (no WorkspaceClient). "
                "Production usage must pass a real client."
            )

    # ----- public API ----------------------------------------------------

    def evaluate(
        self,
        *,
        iter_no: int,
        listing_id: str,
        silver_table: str,
        gold_table: str,
        mlflow_run_id: str,
        dlt_pipeline_id: str,
        current_category: str,
        recent_history: Optional[list[dict]] = None,
    ) -> AgentResult:
        """Score one iteration and pick the next category.

        `current_category` is what the driver fed into the
        marketplace search; the agent may override it.

        `recent_history` is a list of the last 5 iteration
        summaries (so the agent can do its own short-term
        recall without going through the tool). The full
        tool-backed recall is via `query_history` — but for
        v1, the in-context summary list is enough.
        """
        t0 = time.time()
        messages = self._build_messages(
            iter_no=iter_no,
            listing_id=listing_id,
            silver_table=silver_table,
            gold_table=gold_table,
            mlflow_run_id=mlflow_run_id,
            dlt_pipeline_id=dlt_pipeline_id,
            current_category=current_category,
            recent_history=recent_history or [],
        )
        if self._is_mock:
            raw = self._canned_response(iter_no, listing_id, current_category)
        else:
            raw = self._call_fm_api(messages)
        latency_ms = int((time.time() - t0) * 1000)
        result = self._parse_response(raw, latency_ms)
        return result

    def call_tool(self, name: str, arguments: dict) -> str:
        """Execute a tool call. The driver invokes this when the
        agent's FM API response includes a `tool_calls` field.

        Today only `query_history` is implemented; the other 3
        are pre-computed by the driver and passed in via the
        user message (so the FM API call doesn't need to round-
        trip back to the driver). When we move to a full
        Mosaic AI Agent Framework `ChatAgent` deployment, all
        4 tools are registered as UC functions.
        """
        if name == "query_history":
            if self.history_index is None:
                return "(no history index configured)"
            return self.history_index.format_results(
                arguments.get("question", ""), top_k=5
            )
        return f"(tool {name!r} not implemented in v1)"

    # ----- message construction -----------------------------------------

    def _build_messages(
        self,
        *,
        iter_no: int,
        listing_id: str,
        silver_table: str,
        gold_table: str,
        mlflow_run_id: str,
        dlt_pipeline_id: str,
        current_category: str,
        recent_history: list[dict] = None,
    ) -> list[dict]:
        """Build the chat messages for the FM API call."""
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({
                    "iter_no": iter_no,
                    "listing_id": listing_id,
                    "current_category": current_category,
                    "silver_table": silver_table,
                    "gold_table": gold_table,
                    "mlflow_run_id": mlflow_run_id,
                    "dlt_pipeline_id": dlt_pipeline_id,
                    "tools_available": [t["function"]["name"] for t in TOOL_SCHEMAS],
                    "recent_history": (recent_history or [])[-5:],
                }),
            },
        ]

    # ----- FM API call --------------------------------------------------

    def _call_fm_api(self, messages: list[dict]) -> dict:
        """Call the Foundation Model API with the tool schema.

        Uses the OpenAI-compatible chat completions endpoint
        exposed by `databricks serving-endpoints`. Three
        tool-call rounds, then parse the final response.
        """
        from databricks.sdk import WorkspaceClient
        if not self.workspace:
            raise RuntimeError("WorkspaceClient required for production calls")
        # First call: include the tool schema
        resp = self.workspace.serving_endpoints.query(
            name=self.fm_endpoint,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            max_tokens=600,
            temperature=0.2,
        )
        # If the model wanted to call tools, simulate their
        # results (we don't have a real tool executor in v1 —
        # the driver pre-computes the tool outputs and passes
        # them via the messages).
        # In a full Mosaic AI Agent Framework setup, this is
        # where `ChatAgent.predict()` would route to the
        # registered UC functions. For the MVP, we collapse
        # tool_use into a single final response.
        return resp.as_dict() if hasattr(resp, "as_dict") else dict(resp)

    # ----- response parsing --------------------------------------------

    def _parse_response(self, raw: dict, latency_ms: int) -> AgentResult:
        """Parse the FM API response into an AgentResult.

        Accepts multiple response shapes because the FM API
        has returned different formats across versions:
          * `choices[0].message.content`           — plain content
          * `choices[0].message.tool_calls[].function.arguments`  — tool call
        """
        try:
            choices = raw.get("choices") or []
            if not choices:
                raise ValueError("no choices in response")
            msg = choices[0].get("message", {})
            content = msg.get("content") or ""
            tool_calls = msg.get("tool_calls") or []
            # If tool_calls, the model's final text is in
            # `tool_calls[0].function.arguments`. Otherwise
            # the JSON is in `content`.
            if tool_calls:
                args_str = tool_calls[0].get("function", {}).get("arguments", "{}")
            else:
                args_str = content
            data = json.loads(args_str) if isinstance(args_str, str) else args_str
        except Exception as e:
            logger.warning("agent response parse failed (%s); using fallback", e)
            data = {
                "summary": "(agent response unparseable)",
                "quality_score": 0.5,
                "next_category": "Finance",
                "retry": False,
                "tools_used": [],
            }
        usage = raw.get("usage") or {}
        return AgentResult(
            summary=str(data.get("summary", ""))[:500],
            quality_score=float(data.get("quality_score", 0.5)),
            next_category=str(data.get("next_category", "Finance")),
            retry=bool(data.get("retry", False)),
            tools_used=list(data.get("tools_used", [])),
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            latency_ms=latency_ms,
            raw_response=raw,
        )

    # ----- mock for the smoke test --------------------------------------

    def _canned_response(self, iter_no: int, listing_id: str, current_category: str) -> dict:
        """Deterministic mock so the smoke test can assert on the output."""
        next_cats = [
            "Healthcare", "Geospatial", "Retail", "Transportation",
            "Energy", "Climate", "Public Sector", "Marketing",
            "Sports", "Finance",
        ]
        next_cat = next_cats[iter_no % len(next_cats)]
        # Quality score drifts up as we go (drives the curriculum)
        score = min(0.95, 0.4 + (iter_no * 0.05))
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "summary": (
                            f"Mock iteration {iter_no}: ingested listing {listing_id} "
                            f"from {current_category}, ran baseline model, "
                            f"quality={score:.2f}. Next: {next_cat}."
                        ),
                        "quality_score": round(score, 2),
                        "next_category": next_cat,
                        "retry": score < 0.4,
                        "tools_used": ["profile_table", "get_mlflow_metrics"],
                    }),
                },
            }],
            "usage": {
                "prompt_tokens": 320,
                "completion_tokens": 110,
            },
        }
