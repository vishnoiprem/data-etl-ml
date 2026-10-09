# Project 4 — AI Data Analyst (Architecture)

> **Phase 4, Project 4.** A fresh-engagement AI Data Analyst. The
> customer asks "what were last quarter's signups by region?"; the LLM
> writes pandas code; a sandboxed subprocess runs it; the answer is
> returned. The threat model is "the LLM emits code the customer
> didn't realize is dangerous," so the security boundary is a hard
> blocklist + a subprocess sandbox.

## 1. System diagram

```
                Acme Analytics employee
                            │
                            │  POST /analyst  {"question": "..."}
                            ▼
              ┌──────────────────────────────┐
              │  service/app.py              │
              │  /analyst                    │
              │  ───────────────────────────  │
              │  1. Build the prompt         │
              │  2. Ask the LLM for code     │
              │  3. Security check           │
              │  4. Run in sandbox           │
              │  5. Return answer + code     │
              └────────────┬─────────────────┘
                           │
                           ▼
              ┌──────────────────────────────┐
              │  service/security.py         │
              │  Hard blocklist              │
              │  ───────────────────────────  │
              │  28 regex patterns:          │
              │  os.system, subprocess,      │
              │  __import__, eval, exec,     │
              │  open(...), requests,        │
              │  pickle.loads, ...           │
              │  100% match required         │
              └────────────┬─────────────────┘
                           │  if any pattern matches: 403
                           ▼
              ┌──────────────────────────────┐
              │  service/sandbox.py          │
              │  Subprocess runner           │
              │  ───────────────────────────  │
              │  • timeout (5s wall-clock)   │
              │  • memory cap (256MB rlimit) │
              │  • no-network env (no keys)  │
              │  • fresh cwd (temp dir)      │
              └────────────┬─────────────────┘
                           │
                           ▼
                     stdout / stderr →
                     returned to the user
```

The data analyst is a **fresh engagement** (not PacificFreight). The
customer is a 20-person SaaS company, "Acme Analytics" — placeholder
name; the learner substitutes their own. The pattern transfers; the
domain doesn't.

## 2. Component choices

| Component | Choice | Why |
|---|---|---|
| Wire format | JSON over HTTP | The same as the Phase 3 service. Acme's frontend already speaks JSON. |
| LLM call | GPT-4o-mini (Phase 1's `complete()`) | The customer's data is small (a few CSVs); the LLM is used for code generation, not for chat. A small model is enough. |
| Security | Hard regex blocklist (28 patterns) | A soft warning is unacceptable for untrusted LLM-emitted code. A real deployment would use gVisor/Firecracker; for this engagement, the blocklist + sandbox is the right level. |
| Sandbox | subprocess + rlimit + minimal env | Subprocess is the right level for "an LLM emitting code" (NOT "a malicious user"). The lesson notes that gVisor is the upgrade path. |
| Timeout | 5s wall-clock | Most pandas questions complete in < 1s. A 5s timeout catches infinite loops. |
| Memory cap | 256 MB | Enough for typical pandas operations; catches `df = pd.DataFrame(...)` blowups. |
| Storage | In-process dict (cache) + on-disk CSVs | The customer's data is small enough to fit in memory; the CSVs are read on every call from a configurable `data/` dir. |

## 3. Capacity model

| Metric | Phase 3 baseline (PF drafter) | Phase 4 AI Analyst | Notes |
|---|---|---|---|
| Throughput | 150 drafts/day | ~50 questions/day | Analysts ask fewer, deeper questions. |
| Latency | P95 1.8s | P95 3.5s (code gen ~2s + sandbox ~1s) | The LLM call dominates. |
| Cost | $0.50/week | $0.30/week (50 questions × $0.006/question) | LLM cost is higher per call; volume is lower. |
| Storage | 22 chunks in policy | 4 CSVs (~50 MB total) | Trivial. |
| Failure modes | LLM down → stub | LLM down → stub; sandbox timeout → "your code took too long"; blocklist hit → 403 with violation list | The system survives any single component failure. |

## 4. Cost model

| Layer | Cost per call | Why |
|---|---|---|
| LLM (GPT-4o-mini) | ~$0.005 | Code generation prompt is ~800 tokens. |
| Subprocess | ~$0 | Runs on the same VM. |
| Total per question | ~$0.006 | Comparable to the drafter ($0.0005/draft), but each question is heavier. |

The 50 questions/day cap means $0.30/week or $15/year. The CFO approves.

## 5. Failure modes

| Failure | Detection | Mitigation | Recovery |
|---|---|---|---|
| LLM emits dangerous code | Blocklist match | Return 403 with `violations=[...]` | Log to `usage.jsonl`; the customer sees the violation list and rephrases |
| LLM emits infinite loop | Subprocess timeout (5s) | Return 504 | Suggest the customer add a filter / limit |
| LLM emits OOM code | rlimit kill (-9) | Return 507 | Suggest the customer use `df.head()` or `chunksize` |
| Subprocess crash | Non-zero return code | Return 500 with stderr | Log stderr; the customer sees the error |
| LLM down | API error | Stub: "the analyst is offline; please retry" | Phase 1 3-tier fallback pattern |
| Blocklist too aggressive | Customer complains | Whitelist pattern + redeploy | The `ALLOWED_IMPORTS` list is the lever |

## 6. Security policy

The threat model is "an LLM emits code that the customer didn't realize
is dangerous." The defenses are layered:

1. **Prompt-level constraint** — the LLM is told NOT to use `os.system`,
   `subprocess`, etc. This catches 95% of bad code.
2. **Hard blocklist** (28 regex patterns) — a 100% match is required.
   The blocklist is the source of truth; the prompt is just a hint.
3. **Subprocess isolation** — the code runs in a separate process with
   no network, no API keys, a fresh temp dir, and a memory cap.
4. **Timeout** — infinite loops are killed at 5s.
5. **Audit trail** — every `/analyst` call writes to `usage.jsonl` with
   the generated code, the violations (if any), and the sandbox result.

A real deployment with untrusted users should use **gVisor** or
**Firecracker** instead of plain subprocesses. The lesson notes this
explicitly; the code is the right level for "an LLM emitting code,"
not for "a malicious user uploading scripts."

## 7. What this project proves

Phases 1-3 are all about the PacificFreight drafter. Project 4 proves
the FDE pattern **transfers to a different customer, a different domain,
a different security model.** The sandbox is a fresh failure mode (code
execution) that the PF drafter doesn't have. The 5-question "FDE has
left" test (Case Study #5) is the rubric for the handoff.

The lesson is: **the security policy is the contract.** A new dangerous
pattern is a 1-line addition to `security.py::BLOCKED_PATTERNS`. A new
allowed import is a 1-line addition to `security.py::ALLOWED_IMPORTS`.
The sandbox and the prompt don't change.
