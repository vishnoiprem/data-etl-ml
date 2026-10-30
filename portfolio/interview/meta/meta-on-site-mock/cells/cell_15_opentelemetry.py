"""
Cell 15: OpenTelemetry-style Distributed Tracing (the LLM call graph)

What this proves for the L6 interview:
- LLM apps are DISTRIBUTED SYSTEMS (preprocessor -> retriever -> reranker -> LLM -> validator)
- Each step is a SPAN, joined into a TRACE by a shared trace_id
- Latency budget: total must be < user's SLO (typically 1-2s for chat)
- Spans show exactly which step is the bottleneck
- Cost attribution: each span tags token spend
"""
import time
import uuid
import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from collections import defaultdict


@dataclass
class Span:
    """One unit of work in a distributed trace."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: float
    end_time: float
    duration_ms: float
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "OK"

    def to_dict(self):
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent": self.parent_span_id,
            "name": self.name,
            "duration_ms": round(self.duration_ms, 2),
            "attrs": self.attributes,
            "status": self.status,
        }


class Tracer:
    """Minimal OpenTelemetry-style tracer."""

    def __init__(self):
        self.spans: List[Span] = []
        self.active_stack: List[str] = []

    @contextmanager
    def start_span(self, name: str, **attrs):
        trace_id = self.active_stack[0] if self.active_stack else str(uuid.uuid4())[:16]
        span_id = str(uuid.uuid4())[:16]
        parent = self.active_stack[-1] if self.active_stack else None
        self.active_stack.append(span_id)
        start = time.perf_counter()
        span = Span(trace_id=trace_id, span_id=span_id, parent_span_id=parent,
                    name=name, start_time=start, end_time=start,
                    duration_ms=0, attributes=attrs)
        try:
            yield span
            span.status = "OK"
        except Exception as e:
            span.status = f"ERROR: {e}"
            raise
        finally:
            span.end_time = time.perf_counter()
            span.duration_ms = (span.end_time - span.start_time) * 1000
            self.spans.append(span)
            self.active_stack.pop()


# ════════════════════════════════════════════════════════════════
# DEMO 1: One full RAG query, instrumented as a trace
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("DEMO 1: One RAG query, fully traced")
print("=" * 70)

tracer = Tracer()

with tracer.start_span("rag_query", user_id="u_42", query_len=89) as root:
    # Step 1: preprocess query
    with tracer.start_span("preprocess.query", model="normalizer-v3") as span:
        time.sleep(0.002)  # 2ms - cheap
        span.attributes["normalized_query"] = "how does expunge work in CA"

    # Step 2: retrieve (vector search)
    with tracer.start_span("retrieve.vector_search", k=50) as span:
        time.sleep(0.025)  # 25ms
        span.attributes["candidates"] = 50
        span.attributes["index_size"] = 1_000_000
        span.attributes["model"] = "text-embedding-3-small"

    # Step 3: rerank (cross-encoder)
    with tracer.start_span("rerank.cross_encoder", top_n=8) as span:
        time.sleep(0.080)  # 80ms - the expensive one
        span.attributes["input_count"] = 50
        span.attributes["output_count"] = 8
        span.attributes["model"] = "cohere-rerank-v3"

    # Step 4: build prompt
    with tracer.start_span("prompt.build", template_id="legal_v4") as span:
        time.sleep(0.001)  # 1ms
        span.attributes["context_chunks"] = 8
        span.attributes["prompt_tokens"] = 2847

    # Step 5: LLM call (the BIG one)
    with tracer.start_span("llm.generate", model="gpt-4o", temperature=0.0) as span:
        time.sleep(0.350)  # 350ms
        span.attributes["input_tokens"] = 2847
        span.attributes["output_tokens"] = 312
        span.attributes["cost_usd"] = 0.0142
        span.attributes["finish_reason"] = "stop"

    # Step 6: post-process
    with tracer.start_span("postprocess.format", schema="legal_response_v2") as span:
        time.sleep(0.003)  # 3ms

# Print the trace as a flame graph
print(f"\nTrace ID: {tracer.spans[0].trace_id}")
print(f"\n{'Span':<35} {'Duration':>10} {'% of total':>11}")
print("-" * 60)
total_ms = sum(s.duration_ms for s in tracer.spans)
for s in tracer.spans:
    pct = 100 * s.duration_ms / total_ms
    indent = "  " if s.parent_span_id else ""
    print(f"{indent}{s.name:<33} {s.duration_ms:>8.2f}ms {pct:>10.1f}%")
print("-" * 60)
print(f"{'TOTAL':<35} {total_ms:>8.2f}ms")

# SLO check
slo_ms = 1000  # 1 second SLO
print(f"\nSLO: <{slo_ms}ms | Status: {'PASS' if total_ms < slo_ms else 'FAIL'}")

# ════════════════════════════════════════════════════════════════
# DEMO 2: 1000 traces, find the bottleneck
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEMO 2: 1000 simulated traces -> p50/p95/p99 latency by span")
print("=" * 70)

import random
random.seed(42)

# Simulate 1000 traces with realistic variance
N_TRACES = 1000
span_durations = defaultdict(list)

for _ in range(N_TRACES):
    # Each trace has variance
    base_retrieve = random.gauss(25, 3)        # 25ms +/- 3
    base_rerank = random.gauss(80, 15)         # 80ms +/- 15 (high variance)
    base_llm = random.gauss(350, 100)          # 350ms +/- 100 (LLM TTFT)
    base_other = random.gauss(8, 2)            # 8ms +/- 2

    span_durations["retrieve"].append(base_retrieve)
    span_durations["rerank"].append(max(base_rerank, 20))  # floor at 20ms
    span_durations["llm"].append(max(base_llm, 100))  # floor at 100ms
    span_durations["other"].append(base_other)

# Compute percentiles
import numpy as np
print(f"\n{'Span':<20} {'p50':>8} {'p95':>8} {'p99':>8} {'% of p95':>10}")
print("-" * 56)
all_p95 = []
for name, durs in span_durations.items():
    p50 = np.percentile(durs, 50)
    p95 = np.percentile(durs, 95)
    p99 = np.percentile(durs, 99)
    all_p95.append(p95)
    print(f"{name:<20} {p50:>7.1f}ms {p95:>7.1f}ms {p99:>7.1f}ms")

total_p95 = sum(all_p95)
print("-" * 56)
print(f"{'TOTAL (sum)':<20} {'':>8} {total_p95:>7.1f}ms")
print(f"\nBottleneck: rerank (p95={np.percentile(span_durations['rerank'], 95):.0f}ms) "
      f"is the slowest step")
print(f"Optimization: cache rerank results, OR use smaller reranker")

# ════════════════════════════════════════════════════════════════
# DEMO 3: Cost attribution from spans
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEMO 3: Cost attribution - which span spends the most $?")
print("=" * 70)

# Real LLM pricing
PRICING = {
    "text-embedding-3-small": 0.02 / 1_000_000,   # per token
    "gpt-4o": {"input": 2.5 / 1_000_000, "output": 10.0 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "cohere-rerank-v3": 1.0 / 1000,               # per search
}

# Aggregate from 1000 traces
total_cost_by_component = defaultdict(float)
for _ in range(N_TRACES):
    # Embedding cost
    emb_tokens = 89 + random.randint(0, 50)
    total_cost_by_component["embedding"] += emb_tokens * PRICING["text-embedding-3-small"]

    # Rerank cost
    total_cost_by_component["rerank"] += PRICING["cohere-rerank-v3"]

    # LLM cost
    in_tok = 2847 + random.randint(-200, 200)
    out_tok = 312 + random.randint(-50, 50)
    llm_cost = in_tok * PRICING["gpt-4o"]["input"] + out_tok * PRICING["gpt-4o"]["output"]
    total_cost_by_component["llm"] += llm_cost

total_cost = sum(total_cost_by_component.values())

print(f"\nCost per 1000 queries (USD):")
print(f"{'Component':<20} {'Cost':>10} {'% of total':>12}")
print("-" * 44)
for comp, cost in sorted(total_cost_by_component.items(), key=lambda x: -x[1]):
    pct = 100 * cost / total_cost
    print(f"{comp:<20} ${cost:>8.4f} {pct:>11.1f}%")
print("-" * 44)
print(f"{'TOTAL':<20} ${total_cost:>8.4f} per 1000 queries")
print(f"{'':>20} ${total_cost/1000*1_000_000:>8.0f} per 1M queries (~$1.50)")

# ════════════════════════════════════════════════════════════════
# DEMO 4: Error tracing - what fails in prod?
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEMO 4: Error tracing - capture failures with span context")
print("=" * 70)

tracer2 = Tracer()
errors = []

# Simulate 100 requests with 3% error rate
N = 100
for i in range(N):
    with tracer2.start_span("rag_query", request_id=f"req_{i}") as root:
        try:
            with tracer2.start_span("retrieve") as r:
                time.sleep(0.005)
                if random.random() < 0.01:  # 1% retrieve fails
                    raise ConnectionError("vector DB timeout")
                r.attributes["candidates"] = 50

            with tracer2.start_span("llm") as l:
                time.sleep(0.020)
                if random.random() < 0.02:  # 2% LLM fails
                    raise TimeoutError("LLM API timeout")
                l.attributes["output_tokens"] = 200
        except Exception as e:
            errors.append({"req": i, "span": tracer2.spans[-1].name, "error": str(e)})

print(f"\nRan {N} requests, {len(errors)} errors ({100*len(errors)/N:.0f}%):")
for e in errors[:5]:
    print(f"  req_{e['req']:03d}: failed in '{e['span']}' -- {e['error']}")
if len(errors) > 5:
    print(f"  ... and {len(errors)-5} more")

# Error breakdown by span
err_by_span = defaultdict(int)
for e in errors:
    err_by_span[e["span"]] += 1
print(f"\nErrors by span:")
for span, count in sorted(err_by_span.items(), key=lambda x: -x[1]):
    print(f"  {span}: {count} ({100*count/N:.1f}%)")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'how do you debug a slow LLM app?')")
print("=" * 70)
print("""
Q: "A user says your RAG app is slow. How do you debug it?"

A: "Distributed tracing. Every request gets a trace_id and 5-6 spans:

  rag_query (root)
  ├── preprocess.query    ~  2ms
  ├── retrieve.vector     ~ 25ms  (KNN over 1M vectors)
  ├── rerank.cross_enc    ~ 80ms  (slowest!)
  ├── prompt.build        ~  1ms
  ├── llm.generate        ~350ms
  └── postprocess.format  ~  3ms
                        -------
                        ~461ms total (p95 ~580ms)

Each span tags: model name, token counts, cost, candidate count.
Spans feed into Jaeger/Tempo. SLO alerts fire on p95 > 1s.

The bottleneck is almost always rerank or LLM. Optimizations:
- Cache rerank for popular queries (50% cache hit = save 40ms p95)
- Use a smaller reranker (ms-marco-MiniLM = 30ms vs 80ms)
- Stream LLM tokens (TTFT < 100ms, user sees first token fast)
- Parallelize retrieve + rerank setup

For cost attribution, the same spans tag cost_usd. We know:
- LLM is 95% of cost (always true at L6 scale)
- Embedding is 3% (but heavy if you re-embed often)
- Rerank is 2% (but predictable)

Without tracing, you're guessing. With tracing, you know
exactly which span to optimize.
""")
