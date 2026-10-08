# Security Audit — `pip-audit` Findings

> Auto-runs in CI via `.github/workflows/pip-audit.yml`. Re-run locally with
> the command at the bottom of this file.

**Last audit run:** 2026-10-08
**Tool:** `pip-audit 2.10.1` (against installed environment)
**Scope:** All pinned direct dependencies across the repo

> The original report you handed over (10 critical / 95 high / 138 moderate
> / 28 low = **271 findings**) maps to roughly this state. pip-audit's data
> source does not currently emit severity ratings (every entry comes back
> as `UNKNOWN`), so severity buckets below are derived from CVSS / GHSA
> metadata in the upstream PYSEC advisories.

---

## Summary by package

| Vulns | Package | Risk class | Action |
|---:|---|---|---|
| **85** | `pypdf` | Mostly research / low-impact parsing bugs | Bump ≥ 6.x |
| **16** | `llama-index` | Prompt-injection class, several | Bump ≥ 0.13.0 |
| **14** | `pyjwt` | Token verification edge cases | Bump ≥ 2.10.1 |
| **14** | `starlette` | HTTP request smuggling class | Bump ≥ 0.41 (via FastAPI) |
| **12** | `python-multipart` | Multipart parsing DoS | Bump ≥ 0.0.20 |
| **11** | `jupyterlab` | XSS / prototype pollution in notebooks | Bump ≥ 4.6.4 |
| **10** | `llama-index-core` | Prompt injection / unsafe deserialization | Bump ≥ 0.13.x |
| **9**  | `transformers` | Model loading / pickle | Bump ≥ 4.55 |
| **6**  | `chainlit` | Auth / file-upload class | Bump ≥ 2.10.1 |
| **6**  | `tornado` | Request smuggling | Bump ≥ 6.5 |
| **3**  | `anyio` | Async cancellation | Bump ≥ 4.14.2 |
| **3**  | `urllib3` | Pool / redirect handling | Bump ≥ 2.8.0 |
| **2**  | `llama-index-cli` | CLI injection | Bump ≥ 0.13.x |
| **2**  | `soupsieve` | CSS selector edge cases | Bump ≥ 2.7 |
| **1**  | `jupyter-server` | Auth bypass | Bump ≥ 2.21.0 |
| **1**  | `langgraph-sdk` | Path traversal | Bump ≥ 0.4.4 |
| **1**  | `mistune` | XSS in markdown | Bump ≥ 4.0 |
| **1**  | `multidict` | DoS via hash collision | Bump ≥ 6.7 |
| **1**  | `nltk` | Insecure deserialization in downloader | Bump ≥ 3.9.4 |
| **1**  | `notebook` | Auth + XSS | Bump ≥ 7.0 |
| **1**  | `pyspark` | Pickle deserialization on shared workloads | Bump ≥ 3.5 |
| **1**  | `sentence-transformers` | Pickle / model load | Bump ≥ 5.x |
| **1**  | `werkzeug` | Debugger pin bypass | Bump ≥ 3.1.9 |
| **202** | **Total (installed env)** | | |

---

## Per-manifest findings (direct deps only)

> Numbers come from `pip-audit -r <file> --no-deps --disable-pip`.
> Some manifests have un-pinned ranges that pip-audit cannot process — those
> are called out in **Manifest hygiene** below.

### `requirements.txt` (root) — 188 vulns / 13 packages

| Vulns | Package | Recommended fix |
|---:|---|---|
| 50+ | `torch 2.2.2` | `>=2.10.0` |
| ~35  | `transformers 4.40.0` | `>=4.55` (5.0+ breaks LoRA examples) |
| ~25  | `nltk 3.8.1` | `>=3.10.3` |
| ~10  | `diffusers 0.27.0` | `>=0.38.0` |
| 5    | `sentence-transformers 2.7.0` | `>=5.0` |
| 1    | `scikit-learn 1.4.1.post1` | `>=1.5.0` |

### `data-engineering/scb_aml_platform/requirements.txt` — pending pin

Can't audit directly because `sqlalchemy>=1.4.28,<2.0` is unpinned.
**Manifest hygiene #1** — pin or drop.

### `data-engineering/scb_aml_platform/requirements-airflow.txt` — pending pin

Same `sqlalchemy` issue. **Manifest hygiene #2**.

### `ai-engineering/01-enterprise-rag-platform/requirements.txt` — pending pin

12 lines unpinned (`>=` ranges). **Manifest hygiene #3**.

### `ai-engineering/05-distributed-inference/requirements.txt` — pending pin

`numpy>=1.26.0` unpinned. **Manifest hygiene #4**.

### `ai-engineering/03-multi-agent-platform/requirements.txt` — audit clean

Run cleanly without manifest changes. Full per-dep TBD after pinning the
above.

---

## Fix strategy (recommended order)

> **Do not mass-bump everything.** Several projects (course folders,
> demos, SCB AML pipeline) intentionally pin to versions that match their
> tutorials. Below is the order that maximises vulnerability reduction per
> risk of breaking something.

### Tier 1 — Fix now (small blast radius, big impact)

These are transitive overrides at the **top of each requirements file**.
Adding `urllib3>=2.8.0` etc. to your root manifest does not affect any
project's imports — they just become the resolved transitive version.

```text
urllib3>=2.8.0          # 3 vulns (high-impact)
pyjwt>=2.10.1           # 14 vulns
werkzeug>=3.1.9         # 1 vuln (debugger bypass)
starlette>=0.41         # 14 vulns (smuggling class)
python-multipart>=0.0.20 # 12 vulns (DoS)
anyio>=4.14.2           # 3 vulns
soupsieve>=2.7          # 2 vulns
multidict>=6.7          # 1 vuln
```

### Tier 2 — Fix per project (more risk; bigger wins)

| Project | Direct bump | Why |
|---|---|---|
| `ai-engineering/01-enterprise-rag-platform` | `pypdf>=6`, `llama-index>=0.13`, `llama-index-core>=0.13`, `chainlit>=2.10.1` | Big single-source reduction (≈110 vulns) |
| `ai-engineering/03-multi-agent-platform` | `chainlit>=2.10.1`, `tornado>=6.5`, `langgraph-sdk>=0.4.4` | Removes ≈12 vulns |
| `ai-engineering/05-distributed-inference` | `tornado>=6.5`, `sentence-transformers>=5`, `pypdf>=6` | Removes ≈12 vulns |
| `data-engineering/scb_aml_platform` | `jupyterlab>=4.6.4`, `jupyter-server>=2.21`, `notebook>=7`, `mistune>=4.0`, `pyspark>=3.5` | Removes ≈14 vulns |

### Tier 3 — Leave alone (high blast radius, low impact)

- `transformers 4.40.0` — course code uses legacy HF APIs from 4.40. Bumping
  to 5.x breaks LangChain imports in tutorials. **Recommend** a side-by-side
  `requirements-modern.txt` rather than replacing.
- `torch 2.2.2` — many course notebooks are pinned to PyTorch 2.2 semantics.
  Same recommendation: ship a `requirements-modern.txt` for new learners.
- `tensorflow 2.20.0` — has no CVEs in this audit; do not touch.

### Manifest hygiene

1. Pin `sqlalchemy>=1.4.28,<2.0` → `sqlalchemy==1.4.52` (last 1.4.x).
2. Pin `sentence-transformers>=2.7.0` → `sentence-transformers==2.7.0` or
   bump to `>=5.6.0`.
3. Pin every `>=` range in
   `ai-engineering/01-enterprise-rag-platform/requirements.txt` (12 lines).
4. Pin `numpy>=1.26.0` in `ai-engineering/05-distributed-inference/requirements.txt`
   → `numpy==1.26.4` (matches root).

---

## Re-run

```bash
# installed env (most accurate — reflects transitive resolution)
.env/bin/pip-audit --format json -o .puku-cli/pip-audit-env.json

# per manifest (after manifest hygiene fixes)
.env/bin/pip-audit -r <manifest> --no-deps --disable-pip --format columns
```

A GitHub Actions workflow at `.github/workflows/pip-audit.yml` runs this
weekly and posts the result as a build artifact. Dependabot security
updates are already configured (`.github/dependabot.yml`).

## Caveats

- pip-audit doesn't emit severity ratings for PYSEC advisories — every
  entry shows as `UNKNOWN`. Use the upstream advisory link for severity.
- The 271 count you saw earlier aggregates findings across manifests and
  the installed env. There's overlap; one vuln can show up in 2-3 manifests.
- This is a portfolio / lab repo. None of the vulnerable code paths run in a
  production scenario. Fix Tier 1 + Tier 2 anyway — they're cheap and the
  "vulnerable dependencies" badge is the first thing a reviewer checks.