# GitHub Copilot-style inline suggestion engine

Streaming token-by-token completion with debounce, prefix cache, and ghost-text UX. The latency budget is the product.

## Shape

```
   keystrokes
       │
       ▼
   ┌──────────┐
   │ Debouncer│──still typing──► suppress
   └────┬─────┘
        │ quiet ≥ 250ms
        ▼
   ┌──────────────┐
   │  PrefixCache │──hit──► skip prefill (save 50ms)
   └────┬─────────┘
        │ miss
        ▼
   inference (stream)
   ┌────┬────┬────┬────┐
   │ t1 │ t2 │ t3 │ t4 │   <── 1st token at ~50ms, full at prefill + n/tps
   └────┴────┴────┴────┘
        │
        ▼
   ghost-text overlay
```

## What I built

- `serve/inline.py` — `Debouncer` (settle-ms) + `PrefixCache` (LRU) + `CopilotEngine.suggest()`.
- `Debouncer.should_emit()` returns `False` if the user is still typing fast — don't fire an inference for a half-typed line.
- `PrefixCache` keys on `(hash(prefix), hash(suffix))`; a hit skips the prefill cost (50ms in the toy, ~200ms real).
- `CopilotEngine.suggest()` returns a `SuggestionResult` with first-token latency, total latency, cache_hit flag.
- Smoke test: 5 rapid keystrokes (debouncer suppresses most), then a stable request that hits the cache.

## Real numbers

- First-token latency: < 100ms p50 (Copilot's target is ~80ms).
- Total completion: 200-500ms p50 for a 32-token suggestion.
- Cache hit rate: 60-80% in real code (the prefix is "what's around the cursor", which changes slowly).
- Debounce: 200-300ms is the sweet spot — too short and you fire during typing; too long and the user thinks it's broken.

## What I learned the hard way

- **Debounce is the difference between magical and annoying.** Without it, you generate a completion for every keystroke and the user sees flicker. With it, the completion appears once the user pauses.
- **First-token latency is what users feel.** Total latency matters less. Streaming the first token as soon as the prefill is done is the trick.
- **Prefix cache hit rate is the metric to watch.** Low hit rate means the context window is wrong; high hit rate means the model isn't getting fresh context (might be stale).
- **Don't fire on whitespace-only changes.** A debounce that fires on every space character is worse than no debounce.

## When to use

- Inline code completion in an IDE.
- Search-as-you-type (with a smaller max_tokens).
- Any UX where the user sees ghost text.

## When NOT to use

- Batch generation (the streaming overhead is wasted).
- Long-form content (the debounce model doesn't fit; user expects to wait).

## Run

```bash
pip install -r requirements.txt
make smoke
```

---

## What this is NOT

- **Not Copilot.** Copilot is a closed product with
  a frontier model, a multi-language IDE plugin,
  and a hosted inference service. This is the
  *debounce + prefix cache + first-token streaming*
  pattern, sized for one engineer to understand.
- **Not a chat product.** The debounce + ghost-text
  UX assumes the user is *typing code*, not
  waiting for a long-form answer. For chat, the
  whole debounce is wrong.
- **Not a search tool.** Inline suggestion is for
  *predicting the next few tokens*; search is for
  *finding existing code*. The shapes overlap
  (both use a model) but the latency budgets and
  the UX are different.
- **Not a substitute for LSP / type-checking.**
  The suggestion engine produces text; it doesn't
  know whether the text is syntactically valid.
  Pair it with the LSP server from
  [`../../agentic-ai/10-ide-agent-cursor-style/`](../../agentic-ai/10-ide-agent-cursor-style/)
  for the full inline-completion UX.

---

## Related directories

- [`../../agentic-ai/10-ide-agent-cursor-style/`](../../agentic-ai/10-ide-agent-cursor-style/) —
  the IDE-agent cousin: same prefix-cache +
  symbol-level retrieval, but for a multi-file
  chat + refactor instead of single-line
  completion.
- [`../26-mistral-self-host/`](../26-mistral-self-host/) —
  the self-hosting pattern (prefix cache + budget
  guard) that this build's `PrefixCache` is a
  specialized version of.
- [`../20-cog-style-inference-api/`](../20-cog-style-inference-api/) —
  the inference service layer that this build
  plugs into.
- [`../36-together-gpu-cloud/`](../36-together-gpu-cloud/) —
  the GPU pool / autoscaler that the
  latency-sensitive Copilot workload needs.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
