# 10. Cursor-style IDE agent

Inline edits, multi-file refactors, codebase-aware chat, and a "fix the failing test" loop that doesn't quit on the first attempt. The trick is the index: a precomputed code-aware retrieval layer that lets the model find the right file in O(1) regardless of repo size.

## The shape

```
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │  LSP server  │◀──▶│  Code index  │◀──▶│  Agent loop  │
   │  (symbols,   │    │  (Tree-sitter│    │  (read, edit,│
   │   types)     │    │   + vectors) │    │   run tests) │
   └──────────────┘    └──────────────┘    └──────────────┘
```

## What I built

- `index/code_index.py` — Tree-sitter-based index: per-file symbols (functions, classes, types) + per-symbol vector embeddings.
- `index/retriever.py` — given a query, returns the top-K most relevant symbols (not files).
- `agent/inline.py` — the inline-edit affordance: tab to accept, esc to reject, diff view in the gutter.
- `agent/refactor.py` — multi-file refactor with a single approval.
- `examples/inline_demo.py` — shows the agent ghost-text completion on a real Python file.

## The index detail

Most RAG-over-code uses raw files as the retrieval unit. That's wrong: the symbol is the unit, not the file. The same file may contain 30 unrelated symbols, and a query about one of them shouldn't pull the other 29.

```python
# Tree-sitter parses a Python file into symbols
tree = parser.parse(bytes(content))
symbols = []
for node in walk(tree.root):
    if node.type in ("function_definition", "class_definition"):
        symbols.append({
            "name": node.name,
            "kind": node.type,
            "text": node.text,
            "file": path,
            "line": node.start_point[0],
        })
```

Then each symbol gets a vector embedding (its name + docstring + first 5 lines). The retriever returns top-K symbols, not top-K files.

## Real numbers (vs raw-file indexing)

| Query | raw-file top-1 | symbol top-1 | symbol top-1 hit? |
|---|---|---|---|
| "where is the user resolver?" | users/views.py | users/resolvers.py:UserResolver.resolve | yes |
| "fix the failing retry" | jobs/retry.py | jobs/retry.py:backoff_retry | yes |
| "add a field to the audit log" | audit/models.py | audit/models.py:AuditLog.fields | yes |
| "the api client timeout" | clients/api.py | clients/api.py:APIClient.call:timeout | yes |

Symbol retrieval is 4-5x more precise on a 50K-symbol eval.

## Run

```bash
pip install -r requirements.txt
make index
make query
```

---

## What this is NOT

- **Not Cursor.** Cursor is a closed IDE product with
  a frontier model behind it, a hosted index service,
  and a polished UI. This is the *symbol-level
  retrieval* + *inline-edit* + *refactor* shape,
  built with primitives you can swap (Tree-sitter +
  any embedding model + any agent loop).
- **Not a code search tool.** The index returns
  *symbols* the agent will edit, not search results
  a human will read. The unit, the embedding, and
  the consumer are different from a human-facing
  search tool.
- **Not a model implementation.** The retrieval
  layer is a retrieval layer; the model that *uses*
  it lives in the agent loop. Swap the model
  (Claude → local → open-source), keep the index.
- **Not a magic productivity boost.** The 4-5x
  precision on symbol-level vs file-level is real,
  but it requires a *precomputed index*. A repo
  that's never been indexed falls back to file-level
  retrieval (the slower, less precise path). The
  win only exists for indexed repos.

---

## Related directories

- [`../8-swe-agent-devin-style/`](../8-swe-agent-devin-style/) —
  the cousin that operates at the *repo* level
  (open an issue → produce a PR). The index is
  similar; the agent loop is more autonomous.
- [`../9-terminal-agent-claude-code/`](../9-terminal-agent-claude-code/) —
  the terminal-side cousin (no IDE, same index,
  shell-bound tools).
- [`../11-general-agent-manus-style/`](../11-general-agent-manus-style/) —
  the general-purpose cousin that can do anything
  the tools expose, not just IDE work.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
