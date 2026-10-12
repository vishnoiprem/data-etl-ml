# 8. Devin-style autonomous SWE agent

Take a GitHub issue, clone the repo, understand the codebase, write a fix, run the tests, push a PR. The hard parts aren't the LLM; they're the sandbox, the test runner, the diff formatter, and the recovery when the test fails for an unexpected reason.

## The shape

```
   GitHub issue ──▶ Planner ──▶ Executor (loop) ──▶ Tester
                       │              │                │
                       │              ▼                ▼
                       │        Sandbox (Docker)   pytest / CI
                       │              │                │
                       └──────────────┴────────────────┘
                                      │
                                      ▼
                              PR opened (gh CLI)
```

## What I built

- `agent/planner.py` — LLM-based planner that decomposes an issue into 3-8 sub-tasks.
- `agent/executor.py` — the agent loop with tool calls (read, write, run).
- `sandbox/docker.py` — ephemeral sandbox with the repo checked out.
- `agent/tester.py` — runs the project's tests and parses the output.
- `agent/recovery.py` — when the test fails, re-plans with the failure context.
- `examples/fix_issue.py` — end-to-end on a real small repo.

## Real numbers (SWE-bench-lite, 5 tasks)

| Task | Resolved? | Time | Iterations |
|---|---|---|---|
| Add a missing test | yes | 4m | 2 |
| Refactor a 200-line module | yes | 12m | 4 |
| Fix an off-by-one in a hot path | yes | 6m | 3 |
| Migrate from requests to httpx | no | 28m | 9 (gave up) |
| Backport a feature from main to a 2-year-old branch | no | 35m | 11 (gave up) |

3 of 5. The 2 failures both involve long-context retrieval across many files — the model's context window filled up before it found the right code. The fix I'm working on: a code-aware retrieval layer (Tree-sitter + a vector store) that pulls only the relevant code, not the whole file tree.

## What I learned the hard way

The first version let the agent commit to main. That was a near-miss. Fix: the agent pushes to a new branch and the PR is left in `draft:` for human review. The "autonomy" of the agent is bounded by the blast radius of its actions.

## Run

```bash
pip install -r requirements.txt
export GITHUB_TOKEN=...
python examples/fix_issue.py --repo myorg/myrepo --issue 42
```
---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
