# Audit Results — periodic security audit output

> **The output of periodic security audits against the
> repo's dependencies.** This directory is the landing
> pad for the JSON reports; the README tracks the
> summary, the remediation status, and the policy
> that drives what gets fixed vs. accepted.

The repo runs two audits on a schedule:

1. **Python** — `pip-audit` against the root `.venv/`
   (catches CVEs in the Python dependency tree).
2. **npm** — `npm audit` against
   `aws/ecs-data-ingestion/` (the only `package.json`
   in the repo; catches CVEs in the React dependency
   tree).

Both write their JSON output to this directory. The
JSON is the source of truth; this README is the
human-readable summary that the README pointer pulls
from.

---

## Current findings (2026-10-08)

### Python (`pip-audit`)

- **202 known vulnerabilities across 23 packages** in
  the root venv.
- Top offenders by CVE count:

| Package | CVE count |
|---------|-----------|
| `pypdf 4.3.1` | 85 |
| `llama-index 0.10.68` | 16 |
| `starlette 0.41.3` | 14 |
| `pyjwt 2.13.0` | 14 |
| `python-multipart 0.0.18` | 12 |
| `jupyterlab 4.6.0` | 11 |
| `llama-index-core 0.10.68` | 10 |
| `transformers 4.57.6` | 9 |

### npm (`npm audit` on `aws/ecs-data-ingestion`)

- **102 total vulnerabilities** (5 critical · 34 high
  · 49 moderate · 14 low).
- The CRA scaffold pins an old `react-scripts`; the
  bulk of the high-count CVEs are transitive deps
  from that lockfile.

---

## How to re-generate the audit output

```bash
# Python — from repo root
source .venv/bin/activate
pip install pip-audit
pip-audit --format json --output audit-results/pip-audit-root.json

# npm — from the React app dir
cd aws/ecs-data-ingestion
npm audit --json > ../../audit-results/npm-audit-aws.json
```

The JSON files in this directory are overwritten on
each re-run; the README summary is updated by hand
when the top-offenders list changes meaningfully.

---

## Remediation policy

The repo follows a tiered policy for handling
vulnerabilities:

| Severity | Policy | SLA |
|----------|--------|-----|
| **Critical** (CVSS ≥ 9.0) | Patch within 7 days; bump the dep or pin a safe version | 7 days |
| **High** (CVSS 7.0–8.9) | Patch within 30 days; evaluate impact | 30 days |
| **Moderate** (CVSS 4.0–6.9) | Patch in the next regular dep-update cycle | 90 days |
| **Low** (CVSS < 4.0) | Document; patch opportunistically | — |

For "transitive-only" CVEs (the dep is a transitive
import that the app doesn't actually exercise), the
policy is to wait for the upstream maintainer to
publish a fix rather than pinning or forking.

The list of already-applied remediations lives in
the top-level `SECURITY.md` and the
`requirements.txt` / `package.json` lockfiles.

---

## What this directory is NOT

- **Not a continuous monitor.** This is a *point-in-time*
  snapshot. The repo doesn't run a Dependabot / Snyk
  / Renovate bot on a schedule; the audits are
  run on demand and the JSON is checked in. For
  continuous monitoring, see the
  [GitHub Dependabot tab](https://github.com/vishnoiprem/data-etl-ml/security/dependabot)
  on the repo.
- **Not a fix list.** The JSON is the *finding* list;
  the fix list is in the lockfiles and the
  `SECURITY.md` file. This directory is the
  "what does the scanner say" half; the
  "what got fixed" half is in the dependency
  manifests.
- **Not exhaustive.** The audits cover the Python venv
  and the single `package.json` in the repo. The
  `sam-installation/`, `data-engineering-course/`,
  and `medium/` directories have their own deps
  that aren't audited here.

---

## Related directories

- [`../SECURITY.md`](../SECURITY.md) — the top-level
  security policy (key rotation, secret scanning,
  pre-commit hooks).
- [`../requirements.txt`](../requirements.txt) — the
  Python dep manifest that the `pip-audit` runs
  against.
- [`../aws/ecs-data-ingestion/package.json`](../aws/ecs-data-ingestion/package.json) —
  the npm dep manifest that the `npm audit` runs
  against.
- [`../.github/workflows/pip-audit.yml`](../.github/workflows/pip-audit.yml) —
  the CI workflow that re-runs the pip-audit on
  every push.
