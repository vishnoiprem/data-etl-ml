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

## What this is NOT

- **Not Devin.** Devin is a closed product with a
  long-context frontier model, a hosted sandbox, and
  a UX. This is the *shape* of a Devin-like agent —
  planner + executor + tester + recovery — sized for
  one engineer to run against their own repos. The
  frontier-model + hosted-sandbox + UI are a
  separate, much larger, problem.
- **Not a production engineering tool.** The 3-of-5
  SWE-bench-lite result is honest. The two failures
  (long-context retrieval across many files) are
  the same failure mode that production
  code-modification agents hit. The fix is the
  Tree-sitter + vector-store retrieval layer, not a
  bigger model.
- **Not a CI replacement.** CI is *deterministic* —
  given the same code, it returns the same result.
  The agent is *probabilistic* — same issue, two
  runs, two different PRs. Use CI for the test
  gate; use the agent to *produce* the PR that
  CI gates.
- **Not a security boundary.** The agent pushes to
  a new branch and leaves the PR in `draft:`. That's
  the only safety net. If you let it commit to
  `main`, you have given an LLM write access to
  production.

---

## Related directories

- [`../9-terminal-agent-claude-code/`](../9-terminal-agent-claude-code/) —
  the terminal-side cousin: agent in the shell,
  same planner / executor / tester pattern.
- [`../10-ide-agent-cursor-style/`](../10-ide-agent-cursor-style/) —
  the IDE-side cousin: agent in the editor, scoped
  to the current file and project.
- [`../11-general-agent-manus-style/`](../11-general-agent-manus-style/) —
  the general-purpose cousin: agent that can do
  anything the tools expose, not just code.
- [`../16-autonomous-loop/`](../16-autonomous-loop/) —
  the bounded-loop + budget + retry pattern that
  the executor loop in this build is a variant of.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
