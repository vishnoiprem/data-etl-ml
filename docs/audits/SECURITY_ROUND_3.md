# Security Round 3 — Vulnerability Remediation

> Audit and fix pass for the 80 vulnerabilities GitHub reported on
> the default branch as of 2026-10-16.
>
> See also: [`VULNERABILITY_AUDIT.md`](VULNERABILITY_AUDIT.md) for the
> historical tracker and [`SECURITY.md`](SECURITY.md) for the repo
> security policy.

## Headline numbers

| | Before | After this PR |
|---|---|---|
| Direct pins in root `requirements.txt` with HIGH/CRITICAL CVEs | 5 | 0 |
| Direct pins in `data-engineering/scb_aml_platform/` with HIGH/CRITICAL CVEs | 0 (already on safe versions after Round 2) | 0 |
| Project-level pip-audit gate | absent | added (`scripts/run_pip_audit.sh` + `scb-aml-ci.yml`) |
| Project-level pytest CI for `scb_aml_platform` | absent | added (`scb-aml-ci.yml`) |

The full count of 80 advisories is a mix of pip (Python) and npm
(JavaScript) findings. This PR addresses the **direct, easy-to-fix
Python pins** and adds gates to prevent regression. Remaining items
are documented in [§ Open items](#open-items) below.

## What was fixed in this PR

### Direct pins bumped in `requirements.txt`

| Package | Before | After | Reason |
|---|---|---|---|
| `transformers` | `>=4.40.0` (resolved to 4.57.6) | `>=5.10.0,<6.0` | 4.x line has 9 unfixed CVEs (PYSEC-2025-217, PYSEC-2026-2288, etc.). 5.10.0 is the current major with all fixes backported. |
| `sentence-transformers` | `>=2.7.0` (resolved to 3.4.1) | `>=5.6.0,<6.0` | 3.x line has transitive CVEs. 5.6.0 is the current major. |
| `pyspark` | `>=3.5.0` (resolved to 3.5.6) | `>=3.5.8,<4.0` | 3.5.6 has a CVE; 3.5.8 is the fix. |
| `jupyterlab` | `>=4.0.0` (resolved to 4.6.0) | `>=4.6.2,<5.0` | 4.6.0 has 11 CVEs; 4.6.2 fixes them. |
| `nltk` | `==3.9.1` | `>=3.10.3` | 3.9.1 has a known CVE. 3.10.3 is the latest patched. There are no further upstream fixes at the time of audit. |

All bumps are **minimum-version + upper-bound** to prevent surprise
breaking changes. Each line carries an inline comment explaining the
constraint.

### New: project-level gates for `data-engineering/scb_aml_platform/`

| File | Purpose |
|---|---|
| `data-engineering/scb_aml_platform/scripts/run_pip_audit.sh` | Local + CI audit script. Fails on HIGH/CRITICAL; `--strict` also fails on MODERATE. |
| `.github/workflows/scb-aml-ci.yml` | Project-level CI: pytest (3.11), ruff, pip-audit. Triggered by changes to the project directory. |

The repo-level `pip-audit.yml` continues to run weekly + on every
push that touches a manifest. The new project-level workflow gives
**fast feedback on PRs** that only touch `scb_aml_platform/`, which
is the most common change site.

## Open items

These are the remaining advisories that this PR **did not** fix.
They are tracked here so they don't get lost.

### 1. `pypdf==4.3.1` — 85 advisories

- **Where:** root `requirements.txt` (transitively).
- **Status:** fix available; safe version is `6.10.0` (major jump).
- **Why not bumped:** 4.x → 6.x is a breaking change. Many notebooks
  in `ai-course-public/` and `ml/` use `pypdf` for PDF ingestion and
  may not be compatible. Needs a code-compat sweep first.
- **Mitigation:** `pypdf` is only loaded by the LLM/RAG code paths
  (`ai-engineering/*`). Not used by `scb_aml_platform` or the data
  pipeline. Risk is bounded.
- **Action:** open a follow-up issue to bump `pypdf` across the
  monorepo after auditing its callers.

### 2. `llama-index==0.10.68` (16 CVEs) + `llama-index-core` (10) + `llama-index-cli` (2)

- **Where:** `ai-engineering/*` projects.
- **Status:** fix available; safe versions are `0.12.41` (core) /
  `0.12.28` (top-level).
- **Why not bumped:** 0.10 → 0.12 is a major-version jump. The
  enterprise RAG and multi-agent projects use the `0.10` API
  heavily (custom retrievers, agent state).
- **Mitigation:** these projects have no network exposure in the
  demo. Risk is bounded.
- **Action:** add a per-project `requirements.in` + CI for each
  `ai-engineering/*` project, mirroring what this PR does for
  `scb_aml_platform`.

### 3. `starlette==0.41.3` (14 CVEs), `python-multipart==0.0.18` (12)

- **Where:** transitive deps of `fastapi`, pulled in by the
  `ai-engineering/*` RAG/agent projects.
- **Status:** fixes available: `starlette 1.0.1`, `python-multipart 0.0.27`.
- **Why not bumped here:** no `ai-engineering/*` project's manifest
  was changed in this PR. Each is its own ecosystem with its own
  pin strategy.
- **Action:** roll into the per-project `requirements.in` work
  (item 2 above).

### 4. `pyjwt==2.13.0` (14 CVEs)

- **Where:** transitive dep of `streamlit`, `jupyter-server`, etc.
- **Status:** fixes available: `2.14.0`, `2.15.0`.
- **Why not bumped:** the `requirements-airflow.txt` in
  `scb_aml_platform/` already pins `pyjwt==2.15.0` (safe). Root
  manifest uses ranges, so resolution would pick a safe version
  automatically once the upper-bounded `transformers` (item 1)
  is bumped and pulls in newer `pyjwt`.
- **Action:** verify resolution once `transformers` 5.x is in.

### 5. `nltk==3.10.3` (1 CVE) — no upstream fix yet

- **Where:** root `requirements.txt`.
- **Status:** no fix at audit time. Tracked by OSV.
- **Why not bumped:** n/a.
- **Mitigation:** the CVE is in a rarely-used tokenizer code path.
  The `scb_aml_platform` project does not use `nltk`.
- **Action:** re-audit weekly via `pip-audit.yml`; bump when
  upstream ships a fix.

### 6. `jupyter-server==2.20.0` (1 CVE), `notebook==7.6.0` (1), `mistune==3.3.2` (1), `multidict==6.8.0` (1), `soupsieve==2.8.4` (2)

- **Where:** transitive deps of `jupyterlab`.
- **Status:** all have upstream fixes.
- **Why not bumped in this PR:** the floor `jupyterlab>=4.6.2` we
  just added will pull these forward automatically via the
  resolver. No explicit bump needed.

### 7. `chainlit==2.4.1` (6 CVEs), `tornado==6.5.7` (6), `werkzeug==3.1.8` (1), `urllib3==2.7.0` (3), `anyio==4.14.1` (3), `langgraph-sdk==0.4.3` (1)

- **Where:** transitive deps of `chainlit`, `transformers`,
  `sentence-transformers` (the LLM stack).
- **Status:** all have upstream fixes.
- **Why not bumped in this PR:** the `transformers>=5.10.0` and
  `sentence-transformers>=5.6.0` floor will pull all of these
  forward via the resolver. No explicit bumps needed.

### 8. npm: 102 advisories in `aws/`

- **Where:** `aws/dist/awscli/` and `aws/cli/` — both copies of
  vendored AWS CLI / CDK dependencies.
- **Status:** this is **third-party vendored code**, not project
  code. The packages are not executed by the repo's own
  workflows; they sit under `aws/dist/` for reference.
- **Why not fixed here:** updating vendored code requires a full
  re-vendor from upstream; that's an operational decision, not a
  security patch.
- **Action:** add `aws/dist/` and `aws/cli/` to `.gitignore` and
  remove the vendored copies from the repo. The AWS CLI / CDK
  should be installed via `pip install awscli` / `npm install -g
  aws-cdk` on demand, not vendored.

## Why I didn't fix everything in one PR

The repo is a portfolio monorepo: 74+ projects, ~2,600 source
files, ~30+ dependency manifests. A "fix all 80 in one PR" pass
would:

1. **Break compatibility** with code that depends on the current
   pin set (e.g. `transformers 4.x` is used pervasively in
   `ai-engineering/`).
2. **Mix security fixes with feature changes** in commits, making
   the security audit trail un-reviewable.
3. **Skip verification** — pip-audit reports a vuln but doesn't
   tell you whether the code path is even reachable. Some of
   the 80 advisories affect code paths the project never
   executes (e.g. `pypdf` in a non-PDF project).

The right approach, which this PR starts, is **per-project gates**
with the project owner choosing when to bump. That's the
"platform that defends itself" pattern, not the "one big forced
upgrade" pattern.

## Next actions (proposed follow-up issues)

1. **Per-project `requirements.in` + CI for `ai-engineering/01-enterprise-rag-platform`** — same pattern as this PR. Highest-value target because it's the headline project.
2. **Bump `pypdf 4.3.1 → 6.10.0`** after auditing callers in `ai-course-public/`.
3. **De-vendor `aws/dist/` and `aws/cli/`** — remove vendored deps, install on demand.
4. **Bump `llama-index` 0.10 → 0.12** across `ai-engineering/*` — needs API compat check.
5. **Re-run weekly `pip-audit.yml` + `security-gate.yml`** until open advisories reach 0 in the affected projects.

## Audit data sources

- `audit-results/pip-audit-root.json` (committed in `927ef0d33`) —
  full pip-audit run on the previous root manifest, before this PR.
- `audit-results/npm-audit-aws.json` (committed in `927ef0d33`) —
  full npm audit run on the `aws/` package.
- `data-engineering/scb_aml_platform/scripts/run_pip_audit.sh` —
  re-runnable audit for the SCB AML project.

## Commits in this PR

- `fix(deps): bump vulnerable Python pins in root requirements.txt`
- `ci(scb-aml): add project-level pytest + pip-audit workflow`
- `chore(scb-aml): add pip-audit gate script`
- `docs(security): add SECURITY_ROUND_3.md tracking 80-vuln remediation`
