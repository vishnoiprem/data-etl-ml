# Audit Results

This folder contains output from periodic security audits.

## Files

| File | Source | Last run |
|---|---|---|
| `pip-audit-root.json` | `pip-audit` against `.env/` virtualenv for the root project | 2026-10-08 |
| `npm-audit-aws.json` | `npm audit` against `aws/ecs-data-ingestion/package.json` + lockfile | 2026-10-08 |

## Current Findings (2026-10-08)

### Python (`pip-audit`)

- **202 known vulnerabilities across 23 packages** in the root venv.
- Top offenders by CVE count:
  - `pypdf 4.3.1` → 85 CVEs
  - `llama-index 0.10.68` → 16 CVEs
  - `starlette 0.41.3` → 14 CVEs
  - `pyjwt 2.13.0` → 14 CVEs
  - `python-multipart 0.0.18` → 12 CVEs
  - `jupyterlab 4.6.0` → 11 CVEs
  - `llama-index-core 0.10.68` → 10 CVEs
  - `transformers 4.57.6` → 9 CVEs

### npm (`npm audit` on `aws/ecs-data-ingestion`)

- 102 total vulnerabilities.
- **5 critical · 34 high · 49 moderate · 14 low.**

## How to Re-generate

```bash
# Python
source .env/bin/activate
pip-audit --format json --output audit-results/pip-audit-root.json

# npm (run from project dir)
cd aws/ecs-data-ingestion
npm audit --json > ../../audit-results/npm-audit-aws.json
```

## Remediations Already Applied

See `requirements.txt` (root) and `SECURITY.md` for the most recent policy.
