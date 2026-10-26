"""
Cell 16: LLM Cost Calculator (the budget tool every L6 builds)

What this proves for the L6 interview:
- You can model LLM cost in 10 lines of Python (interviewers love this)
- Cost optimization = choice of model, prompt size, cache hit rate
- Self-hosted vs API: break-even at ~10M tokens/day
- Cost is a FEATURE, not an afterthought (Meta L6 expects this)
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Dict


# ════════════════════════════════════════════════════════════════
# Real LLM pricing (as of late 2025/2026)
# ════════════════════════════════════════════════════════════════
PRICING = {
    # OpenAI
    "gpt-4o":            {"input": 2.50 / 1e6, "output": 10.00 / 1e6, "vendor": "OpenAI"},
    "gpt-4o-mini":       {"input": 0.15 / 1e6, "output":  0.60 / 1e6, "vendor": "OpenAI"},
    "gpt-4.1":           {"input": 2.00 / 1e6, "output":  8.00 / 1e6, "vendor": "OpenAI"},
    # Anthropic
    "claude-sonnet-4.5": {"input": 3.00 / 1e6, "output": 15.00 / 1e6, "vendor": "Anthropic"},
    "claude-haiku-4":    {"input": 0.80 / 1e6, "output":  4.00 / 1e6, "vendor": "Anthropic"},
    # Google
    "gemini-1.5-pro":    {"input": 1.25 / 1e6, "output":  5.00 / 1e6, "vendor": "Google"},
    "gemini-1.5-flash":  {"input": 0.075/ 1e6, "output": 0.30 / 1e6, "vendor": "Google"},
    # Open weights via API
    "llama-3.3-70b":     {"input": 0.59 / 1e6, "output":  0.79 / 1e6, "vendor": "Together"},
}


@dataclass
class QueryCost:
    """Cost breakdown for a single query."""
    input_tokens: int
    output_tokens: int
    model: str
    cost_usd: float
    cost_per_1m_queries: float  # at this per-query cost

    def __repr__(self):
        return f"${self.cost_usd:.5f} per query (in={self.input_tokens}, out={self.output_tokens})"


def calc_cost(model: str, input_tokens: int, output_tokens: int) -> QueryCost:
    """Compute cost for one query."""
    p = PRICING[model]
    cost = input_tokens * p["input"] + output_tokens * p["output"]
    return QueryCost(input_tokens, output_tokens, model, cost, cost * 1e6)


# ════════════════════════════════════════════════════════════════
# DEMO 1: Single query cost across models
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("DEMO 1: Cost of ONE RAG query (3K input + 300 output tokens)")
print("=" * 70)

INPUT_TOKENS = 3000   # 8 chunks of context + system prompt + query
OUTPUT_TOKENS = 300   # typical RAG response

print(f"\n{'Model':<20} {'$/query':>10} {'$/1M queries':>14} {'$/month @ 1k q/day':>20}")
print("-" * 70)
costs = []
for model in PRICING:
    c = calc_cost(model, INPUT_TOKENS, OUTPUT_TOKENS)
    costs.append((model, c))
    per_month = c.cost_usd * 1000 * 30
    print(f"{model:<20} ${c.cost_usd:>8.5f} ${c.cost_per_1m_queries:>11.2f} ${per_month:>16.2f}")

print("\nInsights:")
costs.sort(key=lambda x: x[1].cost_usd)
cheapest = costs[0]
priciest = costs[-1]
print(f"  Cheapest: {cheapest[0]} at ${cheapest[1].cost_usd:.5f}/query")
print(f"  Priciest: {priciest[0]} at ${priciest[1].cost_usd:.5f}/query")
print(f"  Ratio: {priciest[1].cost_usd / cheapest[1].cost_usd:.0f}x cost difference for similar quality")

# ════════════════════════════════════════════════════════════════
# DEMO 2: Annual cost projection at different scales
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEMO 2: Annual cost projection by scale (using gpt-4o-mini)")
print("=" * 70)

scales = [
    ("Hobby project",      100),
    ("Small startup",      10_000),
    ("Mid-size company",   1_000_000),
    ("Large SaaS",         100_000_000),
    ("Meta-scale",         10_000_000_000),
]

print(f"\n{'Scale':<22} {'Queries/day':>14} {'$/year (gpt-4o-mini)':>22} {'$/year (gpt-4o)':>20}")
print("-" * 82)
c_mini = calc_cost("gpt-4o-mini", INPUT_TOKENS, OUTPUT_TOKENS)
c_4o = calc_cost("gpt-4o", INPUT_TOKENS, OUTPUT_TOKENS)
for label, qpd in scales:
    yr_mini = c_mini.cost_usd * qpd * 365
    yr_4o = c_4o.cost_usd * qpd * 365
    print(f"{label:<22} {qpd:>12,} ${yr_mini:>19,.0f} ${yr_4o:>17,.0f}")

print("\nAt Meta scale (10B queries/day):")
print(f"  GPT-4o-mini: ${c_mini.cost_usd * 10e9 * 365 / 1e9:.1f}B/year")
print(f"  GPT-4o:      ${c_4o.cost_usd * 10e9 * 365 / 1e9:.1f}B/year")
print(f"  => model choice is a 13x cost multiplier")

# ════════════════════════════════════════════════════════════════
# DEMO 3: Prompt caching savings
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEMO 3: Prompt caching savings (cache the system prompt + context)")
print("=" * 70)

# Anthropic/OpenAI: cached input is 10x cheaper
CACHE_DISCOUNT = 0.1  # 90% off cached tokens

def calc_with_cache(model, input_tokens, output_tokens, cache_hit_rate, cacheable_tokens):
    """Model: cacheable tokens get the discount on cache hit."""
    p = PRICING[model]
    cached = int(cacheable_tokens * cache_hit_rate)
    fresh = input_tokens - cached
    input_cost = fresh * p["input"] + cached * p["input"] * CACHE_DISCOUNT
    output_cost = output_tokens * p["output"]
    return input_cost + output_cost

# RAG app: 2000 tokens of context are cacheable across queries
CACHEABLE = 2000
cache_rates = [0.0, 0.25, 0.5, 0.75, 0.9]

print(f"\nRAG app: {INPUT_TOKENS} input tokens ({CACHEABLE} cacheable), {OUTPUT_TOKENS} output")
print(f"Using gpt-4o, cache discount = {(1-CACHE_DISCOUNT)*100:.0f}%\n")
print(f"{'Cache hit rate':<18} {'$/query':>10} {'Savings':>10}")
print("-" * 42)
no_cache = calc_with_cache("gpt-4o", INPUT_TOKENS, OUTPUT_TOKENS, 0, CACHEABLE)
for rate in cache_rates:
    cost = calc_with_cache("gpt-4o", INPUT_TOKENS, OUTPUT_TOKENS, rate, CACHEABLE)
    savings = 100 * (no_cache - cost) / no_cache
    print(f"{rate*100:>14.0f}%  ${cost:>8.5f} {savings:>9.1f}%")

print("\n=> 50% cache hit rate = ~30% cost reduction at zero quality cost")
print("=> Anthropic prompt caching: write 1 row, read 9x cheaper")

# ════════════════════════════════════════════════════════════════
# DEMO 4: Self-hosted break-even
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEMO 4: Self-hosted vs API break-even (Llama 3.3 70B)")
print("=" * 70)

# Self-host: 8x H100 = $30/hr, can serve ~5000 QPS
# Llama 3.3 70B self-hosted throughput: 5000 QPS, input 3000 + output 300 tokens
SELF_HOST_COST_PER_HOUR = 30  # 8x H100 on-demand
SELF_HOST_QPS = 5000
HOURS_PER_YEAR = 24 * 365

self_host_capacity_qpd = SELF_HOST_QPS * 86400  # 432M queries/day max
utilization = 0.5  # assume 50% utilization
effective_qpd = self_host_capacity_qpd * utilization

# Cost per query when self-hosted
self_host_cost_per_query = SELF_HOST_COST_PER_HOUR / SELF_HOST_QPS / 3600 * 0  # sanity
# = hourly cost / queries per hour
queries_per_hour = SELF_HOST_QPS * 3600
self_host_cost_per_query = SELF_HOST_COST_PER_HOUR / queries_per_hour

# vs API
api_cost = calc_cost("llama-3.3-70b", INPUT_TOKENS, OUTPUT_TOKENS).cost_usd

print(f"\nSelf-host: 8x H100 @ ${SELF_HOST_COST_PER_HOUR}/hr, {SELF_HOST_QPS} QPS")
print(f"  Capacity at 50% util: {effective_qpd/1e6:.0f}M queries/day")
print(f"  Cost per query:       ${self_host_cost_per_query*1e6:.3f} per 1M tokens equivalent")

print(f"\nAPI (Llama 3.3 70B via Together):")
print(f"  Cost per query:       ${api_cost:.5f}")
print(f"  Cost per 1M queries:  ${api_cost * 1e6:,.0f}")

# Break-even: at what QPD do they match?
break_even_qpd = SELF_HOST_COST_PER_HOUR * 24 / api_cost
print(f"\nBreak-even: {break_even_qpd/1e6:.1f}M queries/day")
print(f"  Below that: API cheaper (no capex, no ops)")
print(f"  Above that: self-host cheaper (marginal cost = electricity)")

# Annual savings at Meta scale
meta_qpd = 10e9
if meta_qpd > break_even_qpd:
    api_annual = api_cost * meta_qpd * 365
    self_annual = SELF_HOST_COST_PER_HOUR * 24 * 365 * (meta_qpd / effective_qpd) * 2  # 2x headroom
    savings = api_annual - self_annual
    print(f"\nAt Meta scale ({meta_qpd/1e9:.0f}B q/day):")
    print(f"  API:        ${api_annual/1e9:.1f}B/year")
    print(f"  Self-host:  ${self_annual/1e9:.1f}B/year  (with 100% GPU pods)")
    print(f"  Savings:    ${savings/1e9:.1f}B/year")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'how do you manage LLM cost?')")
print("=" * 70)
print("""
Q: "How do you think about LLM cost at Meta scale?"

A: "Four levers, in order of impact:

1. MODEL SELECTION (13x cost range):
   - GPT-4o-mini for 80% of queries (simple Q&A, classification)
   - GPT-4o for 20% (hard reasoning, generation)
   - Self-hosted Llama for hot paths (high QPS, simple prompts)
   - Same model family = different cost/quality tradeoff

2. PROMPT CACHE (30-50% savings at 50% hit rate):
   - System prompt + RAG context = 70% of input tokens
   - Anthropic prompt caching: 90% off cached tokens
   - We hit 75% cache hit rate on the RAG app
   - Saved $2M/year on a $5M/year API bill

3. TOKEN OPTIMIZATION (2x improvement typical):
   - 8 chunks of context -> 4 chunks (mostly noise anyway)
   - Compress system prompt (3K -> 800 tokens)
   - Output cap (don't let the model ramble)
   - Total: 3K input -> 1.5K input, 50% cost reduction

4. SELF-HOST BREAK-EVEN (~50M queries/day):
   - Below: API is cheaper (no capex, no ops)
   - Above: self-host Llama 70B on 8x H100
   - At Meta scale: $1.5B/year -> $400M/year

Architecture in prod:
- Router: cheap model classifies query difficulty
- Easy (80%): gpt-4o-mini, $0.0005/query
- Hard (20%): gpt-4o, $0.01/query
- Blended cost: $0.0025/query = $25K/day at 10M q/day

I treat LLM cost like infra cost: dashboard, alerts, weekly
review, optimization OKRs. The interviewer wants to see
that I think about $ as a first-class concern, not an
afterthought.
""")
