# Security Policy

## Supported Versions

This repository is a personal portfolio / learning monorepo. Most projects here are:

- **Course / tutorial code** — not maintained for security. Use at your own risk.
- **Reference architectures** — meant as interview preparation; not deployed to production.
- **Vendored third-party code** — see `sam-installation/aws-sam-cli-src/` (AWS source, governed by AWS's own security policy).

| Project area | Supported | Notes |
|---|---|---|
| `/` (root `requirements.txt`) | Receives periodic Dependabot updates; no SLA | Reference ML/DE portfolio |
| `ai-engineering/*` | Receives Dependabot updates | Course code |
| `data-engineering/*` | Receives Dependabot updates | Reference ETL code |
| `agentic-ai/*` | Receives Dependabot updates | LangChain / AWS Bedrock samples |
| `sam-installation/aws-sam-cli-src/` | **No — AWS upstream** | See [aws/aws-sam-cli](https://github.com/aws/aws-sam-cli/security) |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

### Where to report

- **Email:** `vishnoiprem@users.noreply.github.com` (use a personal email or open a [GitHub Security Advisory](https://github.com/vishnoiprem/data-etl-ml/security/advisories/new))
- **For vendored AWS SAM CLI source** (`sam-installation/aws-sam-cli-src/`): report to AWS directly per the [AWS SAM CLI security policy](https://github.com/aws/aws-sam-cli/security/policy).

### What to expect

- **Acknowledgement:** within 7 days
- **Status update:** every 14 days until resolved or risk-accepted
- **Fix timeline:** best-effort; this is a portfolio repository, not a production service

### What to include

1. Description of the vulnerability and affected file/folder
2. Steps to reproduce
3. Proof-of-concept code (if available)
4. Suggested fix (optional)

## Automated Scanning

This repo uses [GitHub Dependabot](https://github.com/dependabot) for:

- **Python (pip)** — root + `/ai-engineering` weekly
- **npm** — `aws/ecs-data-ingestion` + 2 TypeScript starters weekly
- **GitHub Actions** — root weekly

Dependabot alerts are visible to repo admins at `https://github.com/vishnoiprem/data-etl-ml/security/dependabot`.

### Periodic local audits

| Tool | When | Output location |
|---|---|---|
| `pip-audit` | manual / pre-release | `audit-results/pip-audit-root.json` |
| `npm audit` | manual / pre-release | `audit-results/npm-audit-*.json` |

## Cryptography Notice

This repository contains **no production credentials, secrets, or real keys**. Any sample `.env` files contain dummy values only. Before deploying any code from this repo:

- Rotate any credentials used during local testing.
- Generate fresh secrets via your cloud provider's KMS / Secrets Manager.
- Review `git log --all` and `gitleaks` history before publishing.

## Supply Chain Notes

- Vendored source in `sam-installation/aws-sam-cli-src/` is **not** developed in this repository. Do not modify it directly — pull upstream fixes.
- GitHub Actions are pinned to major versions (`@v4`); for production hardening, **pin by SHA** rather than version tag.

## Container Image (`leads-pipeline`)

The `leads-pipeline` Docker image is published to
`ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline` on every push to
`main` by `.github/workflows/leads-cd.yml`. A separate
`release-please` workflow drives semver releases (see
`.github/workflows/release-please.yml`); when a release PR is
merged, `leads-cd` is re-dispatched with a `latest-vX.Y.Z` tag so
production consumers can pin to a specific release.

**Vulnerabilities in the image** — report via the GitHub Security
Advisories flow (link above). The CD workflow will pick up the
patch and publish a new `latest` tag automatically.

**Pulling a patched version:**

```bash
docker pull ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline:latest
```

For reproducibility / supply-chain hardening, pin to a SHA tag:

```bash
docker pull ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline:main-abc1234
```

For a semver-pinned version (post-release-please):

```bash
docker pull ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline:latest-v1.2.3
```

**Image hardening** (see `leads-pipeline/draft-cron/Dockerfile`):

- Runs as non-root user `avilx` (uid 1001)
- Uses `python:3.12-slim` base (no compilers, no extra packages)
- Excludes `.tailored_resumes/`, `*.log`, `*.csv`, `.git/`, `tests/`
  via `.dockerignore`
- Capped at 300 MB by the `leads-ci` workflow's size-budget step
- `leads-cd`'s `verify` job re-pulls the published image and runs
  a Python import smoke test, so a broken manifest can't silently
  land in GHCR
- Each release ships an SPDX 2.3 SBOM as a workflow artifact
  (downloadable from the `leads-cd` run page, 30-day retention)
- `org.opencontainers.image.version` label is stamped from the
  in-tree `VERSION` file at build time
- Every published tag is signed with **cosign keyless** (OIDC +
  GitHub Actions workload identity). Verify any pull:
  ```bash
  cosign verify \
    --certificate-identity-regexp 'https://github.com/vishnoiprem/data-etl-ml' \
    --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
    ghcr.io/vishnoiprem/data-etl-ml/leads-pipeline:latest
  ```
- GHCR's built-in scanner continuously reviews the published tags,
  and `leads-ci`'s `vuln-scan` job re-runs grype on every PR and
  uploads the SARIF to the Security tab. grype is currently
  **advisory only** (no build failure on any severity) — the
  `python:3.12-slim` base image frequently ships Critical CVEs in
  OS packages (glibc, openssl, libsqlite3) that are out of our
  control until upstream debian ships a fix, so failing CI on
  those would mean every PR is red for months at a time. The
  findings still surface in GitHub's vulnerability graph and
  Dependabot alert feed. If/when the leads-pipeline graduates to
  a production deployment, flip `fail-build: true` and a sensible
  `severity-cutoff` to gate merges on real risk.

## License & Disclaimer

This software is provided "as is", without warranty of any kind. See [LICENSE](LICENSE) for full text.

---

**Last updated:** 2026-10-12
