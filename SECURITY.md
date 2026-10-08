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

## License & Disclaimer

This software is provided "as is", without warranty of any kind. See [LICENSE](LICENSE) for full text.
