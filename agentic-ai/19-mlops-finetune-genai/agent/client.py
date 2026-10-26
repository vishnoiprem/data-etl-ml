"""agent.client — OpenAI-compat client with retries + per-task cost.

Thin wrapper over the OpenAI SDK (which already speaks to vLLM's
OpenAI-compat server). We add:

  - exponential-backoff retries, capped at `gates.max_retry`
  - per-call latency timing
  - per-call cost attribution
  - p50 / p95 / mean / total summary at the end of a batch

The cost column in the README comes from this client, not vibes.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Any

from agent.config import load_settings
from agent.gates import per_request_cost_usd, retry_policy


try:  # pragma: no cover
    from openai import OpenAI  # type: ignore
    HAVE_OPENAI = True
except ImportError:  # pragma: no cover
    HAVE_OPENAI = False


@dataclass
class CallRecord:
    prompt: str
    response: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    cost_usd: float
    status: str
    attempt: int


@dataclass
class BatchSummary:
    records: list[CallRecord] = field(default_factory=list)

    def add(self, r: CallRecord) -> None:
        self.records.append(r)

    def report(self) -> dict[str, Any]:
        if not self.records:
            return {"n": 0}
        lat = sorted(r.latency_s for r in self.records)
        p50 = lat[len(lat) // 2]
        p95 = lat[max(0, int(0.95 * len(lat)) - 1)]
        return {
            "n": len(self.records),
            "latency_p50_s": round(p50, 4),
            "latency_p95_s": round(p95, 4),
            "latency_mean_s": round(statistics.mean(lat), 4),
            "cost_total_usd": round(sum(r.cost_usd for r in self.records), 6),
            "cost_per_call_usd": round(
                sum(r.cost_usd for r in self.records) / len(self.records), 6
            ),
            "tokens_in": sum(r.input_tokens for r in self.records),
            "tokens_out": sum(r.output_tokens for r in self.records),
            "errors": sum(1 for r in self.records if r.status != "ok"),
        }


def chat_once(client: "OpenAI", prompt: str, settings, attempt: int) -> CallRecord:  # type: ignore[name-defined]
    """A single chat call with retry + cost attribution.

    On 429 / 5xx we sleep with exponential backoff. On 400 we stop — the
    client made a bad request, no retry helps.
    """
    started = time.perf_counter()
    status = "ok"
    text = ""
    in_t = 0
    out_t = 0
    try:
        resp = client.chat.completions.create(
            model=settings.serve.adapter_alias,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.0,
        )
        text = resp.choices[0].message.content or ""
        out_t = (resp.usage.completion_tokens if resp.usage else 0) or 0
        in_t = (resp.usage.prompt_tokens if resp.usage else 0) or 0
    except Exception as e:
        status = f"error:{type(e).__name__}"
        allowed, _ = retry_policy(attempt, settings.gate.max_retry, str(e))
        if allowed:
            time.sleep(2 ** attempt * 0.25)
            return chat_once(client, prompt, settings, attempt + 1)
        text = ""

    elapsed = time.perf_counter() - started
    cost = per_request_cost_usd(
        input_tokens=in_t,
        output_tokens=out_t,
        input_per_1m=settings.monitor.cost_input_usd_per_1m,
        output_per_1m=settings.monitor.cost_output_usd_per_1m,
    )
    return CallRecord(
        prompt=prompt,
        response=text,
        input_tokens=in_t,
        output_tokens=out_t,
        latency_s=elapsed,
        cost_usd=cost,
        status=status,
        attempt=attempt,
    )


def run(prompts: list[str], base_url: str | None = None, api_key: str | None = None) -> BatchSummary:
    """Public entrypoint. Builds the OpenAI client, executes the batch, and
    returns a summary that the bash side prints.
    """
    settings = load_settings()
    if not HAVE_OPENAI:
        # Degraded mode — keep the call shape but skip the HTTP call.
        summary = BatchSummary()
        for p in prompts:
            summary.add(CallRecord(prompt=p, response="", input_tokens=0, output_tokens=0,
                                    latency_s=0.0, cost_usd=0.0, status="openai_missing", attempt=0))
        return summary

    client = OpenAI(
        base_url=base_url or settings.serve.base_url,
        api_key=api_key or settings.serve.api_key,
        timeout=30.0,
        max_retries=0,  # we own retry policy through `gates.retry_policy`
    )

    summary = BatchSummary()
    for p in prompts:
        summary.add(chat_once(client, p, settings, attempt=0))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a batch of chat requests against the served adapter.")
    parser.add_argument("--prompts", nargs="*", default=[
        "What is the capital of France?",
        "Translate 'good morning' to Spanish.",
        "What is 17 * 23?",
    ])
    args = parser.parse_args(argv)

    summary = run(args.prompts)
    print(json.dumps(summary.report(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
