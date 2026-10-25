# SCB AML Platform — Security Posture

> Project-specific security notes. See the repo-level
> [`SECURITY.md`](../../SECURITY.md) for the overall policy and
> [`VULNERABILITY_AUDIT.md`](../../docs/audits/VULNERABILITY_AUDIT.md) for the
> current audit status.

## Threat model

This project is a **portfolio / reference implementation** of an
AML pipeline. It runs end-to-end against synthetic data and
**does not connect to real banking systems**.

If you adapt this code for production, the following items would
need to be reconsidered — they are appropriate for a local demo
but not for a regulated workload.

## What's safe in the demo

- **Synthetic data only.** No real customer, transaction, or
  sanctions-list data is included. `data/dummy/` is regenerated
  by `python run_demo.py`.
- **No outbound network calls.** The platform reads local files
  and writes local Parquet. Kafka / Elasticsearch clients are
  optional and fail closed to file-based simulation.
- **No credentials in source.** `config/settings.py` reads hosts
  and ports from environment variables with safe local defaults
  (e.g. `localhost:9200`).

## What changes for production

### CORS (fixed in P2)
Previously the FastAPI app accepted cross-origin requests from
`allow_origins=["*"]`. The Lucid Search API returns entity data,
sanctions matches, and counterparty networks — these are
sensitive and should not be readable from arbitrary browser
origins. CORS is now restricted to a `CORS_ALLOWED_ORIGINS`
env-driven allowlist (default: `localhost:3000,localhost:8000`).

### AuthN / AuthZ (NOT implemented)
The `/search`, `/entity/{id}`, and `/entity/{id}/network` endpoints
have no authentication. In production this would need:
- Mutual TLS or OAuth2 / OIDC at the API gateway.
- Per-analyst authorization (regional / team / clearance level).
- An audit log of every entity view — required for compliance in
  most jurisdictions.
- A rate limit per analyst (mitigates enumeration attacks).

### Rate limiting (NOT implemented)
No request rate limiting is applied. A real AML API should rate
limit per source IP and per analyst session, and should treat
large fan-out queries (e.g. "search all entities in HK") as
higher-risk.

### PII handling
The synthetic dummy data includes realistic-looking PII (names,
dates of birth, nationalities, addresses). When generated for
local demos this is fine. **Do not** generate dummy data using
real customer samples — this is the most common way regulated
data leaks into public repos.

### Datetime handling (fixed in P2)
`datetime.utcnow()` is deprecated in Python 3.12+ and will be
removed in a future release. All call sites now use
`datetime.now(timezone.utc)`, which returns a timezone-aware UTC
datetime.

## Dependency posture

- **Runtime deps:** see [`pyproject.toml`](pyproject.toml) —
  ~25 packages, all directly imported by the platform.
- **Airflow:** separate venv (see
  [`requirements-airflow.txt`](requirements-airflow.txt)).
  Airflow has its own pinned Flask/Jinja2/SQLAlchemy that clashes
  with the main env.
- **CI:** `pip-audit` runs weekly and on every PR that touches
  `requirements*.txt`. `security-gate.yml` blocks merges on
  HIGH/CRITICAL vulnerabilities in the manifest.
- **Secrets:** `detect-secrets` runs in pre-commit. Run
  `detect-secrets scan > .secrets.baseline` once per project to
  seed the baseline; audit any new findings with
  `detect-secrets audit .secrets.baseline`.

## Reporting vulnerabilities

If you find a security issue, follow the process in
[`SECURITY.md`](../../SECURITY.md#reporting-vulnerabilities) at
the repo root. Please **do not** open a public GitHub issue for
security findings.
