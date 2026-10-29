# Secrets — keep them out of git (and out of CI)

This repo is **public**. Once anything reaches `main` it is
visible to the whole internet within seconds. This file lists
the four layers of defense and how to use each one.

## TL;DR — what to do right now

1. **Never put a real secret in source.** Use `os.environ["X"]`
   and read from a `.env` file in your local clone. The
   `.env` file is gitignored (see root `.gitignore` lines
   1–17).
2. **For shared AWS / GCP keys between teammates** use a secret
   manager (AWS Secrets Manager, GitHub Actions secrets, 1Password,
   etc.) — not Slack DMs, not a shared `.env`, and not a public repo.
3. **Pre-commit hook** — install once and you're protected at
   `git commit` time:
   ```bash
   pip install pre-commit
   pre-commit install
   ```
   Then every commit runs `detect-secrets` (AKIA, GitHub PATs,
   high-entropy strings) plus the project's regular
   `flake8` / `hadolint` / `shellcheck`. Bypass with
   `git commit --no-verify` only if you have a real reason.
4. **CI** — even without the local hook, the
   `leads-ci` workflow runs
   `agentic-ai/5-amazon-transcribe/tests/test_no_hardcoded_aws_keys.py`
   which scans the 3 source files for the `AKIA[0-9A-Z]{16}`
   pattern and a 40-char base64 secret. Two layers because
   not everyone has the hook installed.

## What is gitignored (root `.gitignore` lines 1–17)

| Pattern | Catches |
|---|---|
| `.env`, `.env.*` | literal `.env`, `.env.local`, `.env.production`, etc. |
| `*.env` | `foo.env`, `aws.env`, `production.env`, etc. |
| `*aws.env` | the rename-resistant variant of `aws.env` |
| `*credentials*` | `aws_credentials.csv`, `gcp-credentials.json`, etc. |
| `*secrets*` | `db_secrets.yaml`, etc. |
| `creds/`, `secrets/` | the conventional directory names |
| `.aws/`, `.gcp/`, `.azure/` | the CLI config dirs |

Whitelisted (still tracked): `.env.example` files — these are
**placeholders**, never real values, and they tell users what
to set.

## If you leaked a secret (don't panic, but act fast)

1. **Revoke the credential immediately.** AWS → IAM →
   Security credentials → Delete the access key. GitHub →
   Settings → Developer settings → Personal access tokens →
   Revoke. GCP → IAM → Service accounts → Disable key.
2. **Audit CloudTrail / audit logs** for the last 90 days.
   Look for calls you don't recognize.
3. **Generate a replacement** and load it from a secret
   manager. Update any code that uses it.
4. **Rotate any code that referenced the leaked credential**
   — passwords, tokens, API keys — even if the audit log
   looks clean. Leaked means compromised.
5. **Remove the leaked value from git history.** This is the
   optional hard step:
   ```bash
   # remove a file from history entirely
   git filter-repo --path secrets.env --invert-paths
   # amend the most recent commit to scrub a value
   git rebase -i HEAD~1   # then `git commit --amend`
   ```
   After either of these, **force-push** and notify all
   collaborators to re-clone. (The repo is public, so the
   leaked secret was already exposed by the time you do this —
   rotation is the real fix; history rewrite is cosmetic.)

## Why two layers (hook + CI test)?

Pre-commit hooks are easy to skip (`git commit --no-verify`).
The CI test is automatic and runs on every PR. Having both
means a leak gets caught twice, by two different teams, in
two different contexts. The cost is two extra installs
(`pip install pre-commit detect-secrets` once per dev, and
zero extras in CI since the test is already there).

The regression test file
`agentic-ai/5-amazon-transcribe/tests/test_no_hardcoded_aws_keys.py`
is the source of truth — read it for the exact patterns it
catches. The pre-commit config uses the same patterns
indirectly (via `detect-secrets`'s built-in `AWSKeyDetector`).

---

**Last updated:** 2026-10-13  
**License:** MIT — use freely in your own courses, prototypes, and products.
