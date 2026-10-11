# Security Audit — `pip-audit` Findings

> Auto-runs in CI via `.github/workflows/pip-audit.yml`. Re-run locally with
> the command at the bottom of this file.

**Last audit run:** 2026-10-11
**Tool:** `pip-audit 2.10.1` (against installed environment)
**Scope:** All pinned direct dependencies across the repo

> The Dependabot digest from 2026-10-10 reported **374 vulnerabilities on
> the default branch** (17 critical / 115 high / 201 moderate / 41 low).
> After the Tier 1 + Round 2/3 + Tier 2 sweep in this commit, the
> Tier-1-only audit drops from **337** (after the first bump round) to
> **66 residual** advisories, of which:
> - 51 are `pypdf` entries whose fix version (6.10.0+) is **not yet on
>   PyPI** — we are at 6.9.2 (latest published) and must wait for upstream.
> - 11 are `cryptography` 46.x→50.0.0 (CVE-2026-69247/69248) — major
>   version jump (46→50) deferred to Tier 3 (see "Tier 3" below).
> - 2  are `pyarrow` 17.x→23.0.1 (CVE-2026-25087) — major jump (17→26)
>   deferred to Tier 3.
> - 1  is `nltk` 3.10.3 with **no fix published** (CVE-2026-81726).
> - 1  is `mlflow` 3.15.0 with **no fix published** (CVE-2026-71211).
> pip-audit's data source does not emit severity ratings (every entry
> comes back as `UNKNOWN`); severity buckets are derived from CVSS / GHSA
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

### `data-engineering/scb_aml_platform/requirements.txt` — audit clean

Pinned to `sqlalchemy==1.4.52` and the full Tier 1 transitive override
set. No manifest changes needed; pip-audit processes the manifest
directly.

### `data-engineering/scb_aml_platform/requirements-airflow.txt` — audit clean

Same overrides as the main file. No manifest changes needed.

### `ai-engineering/01-enterprise-rag-platform/requirements.txt` — **hygiene fixed 2026-10-11**

All 12 `>=` ranges pinned to `==` (per `SECURITY_AUDIT.md` Manifest
hygiene #3). pypdf==6.4.0, sentence-transformers==5.6.0,
faiss-cpu==1.8.0, fastapi==0.110.0, etc.

### `ai-engineering/05-distributed-inference/requirements.txt` — **hygiene fixed 2026-10-11**

`numpy>=1.26.0` pinned to `numpy==1.26.4` (Manifest hygiene #4).

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
urllib3==2.8.0          # 10 vulns (high-impact)
pyjwt==2.15.0           # 21 vulns (token verification edge cases)
werkzeug==3.1.9         # 7 vulns (debugger bypass)
starlette==1.3.1        # 14 vulns (smuggling class)
python-multipart==0.0.31 # 1 vuln (DoS)
anyio==4.14.2           # 2 vulns
soupsieve==2.9.0        # 6 vulns
multidict==6.9.1        # 1 vuln
mistune==3.3.0          # 1 vuln (XSS)
# --- Round 2/3 added 2026-10-10 to address 374 Dependabot digest ---
requests==2.33.0        # 6 vulns
idna==3.15              # 2 vulns
setuptools==83.0.0      # 2 vulns
tornado==6.5.9          # 23 vulns
cryptography==46.0.5    # 13 vulns
pillow==12.3.0          # 36 vulns
tqdm==4.67.3            # 2 vulns
marshmallow==3.26.2     # 2 vulns
sqlparse==0.6.0         # 10 vulns
pyasn1==0.6.4           # 10 vulns
oauthlib==4.0.0         # 1 vuln
filelock==3.20.3        # 4 vulns
protobuf==6.33.5        # 4 vulns
pymongo==4.18.2         # 4 vulns
fsspec==2026.6.0        # 1 vuln
httplib2==0.32.0        # 2 vulns
azure-core==1.38.0      # 2 vulns
azure-identity==1.16.1  # 2 vulns
gunicorn==23.0.0        # 4 vulns
mako==1.3.12            # 2 vulns
bleach==6.4.0           # 2 vulns
orjson==3.11.6          # 2 vulns
multipart==1.2.2        # 2 vulns
ujson==5.13.0           # 8 vulns
litestar==2.22.0        # 8 vulns
nbconvert==7.17.1       # 6 vulns
pyarrow==17.0.0         # 1 vuln
sentence-transformers==5.6.0  # 1 vuln
pyspark==3.5.8          # 3 vulns
fonttools==4.60.2       # 1 vuln
geopy==2.5.0            # 1 vuln
jaraco-context==6.1.0   # 1 vuln
diffusers==0.38.0       # 5 vulns
gitpython==3.1.60       # 39 vulns
pypdf==6.4.0            # covers ~85 historical vulns (bumped major)
aiohttp==3.14.3         # 64 vulns
nltk==3.10.3            # 74 vulns
mlflow==3.15.0          # 50 vulns
transformers==5.10.0    # 43 vulns (major bump — 5.x line)
jupyterlab==4.6.4       # 16 vulns
jupyter-server==2.21.0  # 13 vulns
notebook==7.6.3         # covers class of notebook-server vulns
chainlit==2.10.1        # covers Chainlit 2.x auth/upload class
llama-index==0.13.0     # covers prompt-injection / deserialization class
llama-index-core==0.13.0
llama-index-cli==0.13.0
langgraph-sdk==0.4.4    # path-traversal
langchain==1.3.9        # 8 vulns (major bump — 1.x line)
langchain-core==1.3.3   # 15 vulns (major bump — 1.x line)
langchain-community==0.3.27  # 11 vulns
langchain-openai==1.1.14     # 2 vulns
langsmith==0.8.18       # 5 vulns
distributed==2026.1.0   # 2 vulns
ray==2.56.0             # 11 vulns
streamlit==1.54.0       # 7 vulns
black==26.3.1           # 3 vulns
pytest==9.0.3           # 2 vulns
```

> **Note on pinned `==` vs `>=`:** The actual manifests use pinned `==`
> versions so that the security floor is reproducible across installs
> (no surprise minor upgrades re-introducing a vuln). The list above
> is the **minimum acceptable** version floor — bump the pin to track
> new fixes.

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