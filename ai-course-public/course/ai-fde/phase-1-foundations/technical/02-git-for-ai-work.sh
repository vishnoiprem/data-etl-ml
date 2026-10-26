#!/usr/bin/env bash
#
# Lesson 02 — Git for AI Work: scripted mini workflow.
#
# Idempotent. Safe to re-run. Demonstrates the entire lesson in 5 seconds.
#
# What it does:
#   1. Initializes git in this folder (skip if already a repo)
#   2. Writes a proper .gitignore
#   3. Makes a "chore: scaffold" commit on main
#   4. Creates feat/lookup-cli branch
#   5. Copies lesson 01's CLI onto the branch
#   6. Makes a "feat: pf-lookup CLI" commit
#   7. Drops a .pr/ directory with a PR-description template
#
# What you should be able to explain to a client after running this:
#   - The .gitignore pattern that protects .env but commits .env.example
#   - Why every commit message has a "Why" and a "What"
#   - Why we work on a branch, not main
#
# How to run:
#   bash technical/02-git-for-ai-work.sh
#   bash technical/02-git-for-ai-work.sh --reset   # nuke .git/ and start over

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ "${1:-}" == "--reset" ]]; then
  echo "==> Removing .git/ and starting fresh"
  rm -rf .git
fi

if [[ ! -d .git ]]; then
  echo "==> git init"
  git init -q
  git config user.email  "${GIT_EMAIL:-fde@pacificfreight.example}"
  git config user.name   "${GIT_NAME:-FDE Engineer}"
fi

# 1. .gitignore (idempotent: always rewrite, so a re-run is safe)
echo "==> writing .gitignore"
cat > .gitignore <<'EOF'
# FDE Phase 1 .gitignore — never commit customer secrets or data.

# Environment
.env
.env.*
!.env.example
.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/

# Tool caches
.mypy_cache/
.ruff_cache/
.idea/
.vscode/

# Local outputs
*.log
out/
tmp/

# Real customer data (our shared/shipments.json is a mock, OK to commit)
*-prod.json
EOF

# 2. .env.example (always rewrite)
echo "==> writing .env.example"
cat > .env.example <<'EOF'
# PacificFreight — environment variables
# Copy to .env and fill in real values. .env is gitignored.

PF_TRACKER_PATH=./shared/shipments.json
PF_REP_NAME=Linh
PF_LLM_PROVIDER=
PF_OPENAI_API_KEY=
PF_ANTHROPIC_API_KEY=
EOF

# 3. Stage scaffold
git add -A .gitignore .env.example shared/ technical/01-python-tooling.py consulting/ README.md TECHNICAL-TRACK.md CONSULTING-TRACK.md scenario-brief.md 2>/dev/null || true

# 4. First commit if not present
if ! git rev-parse HEAD >/dev/null 2>&1; then
  echo "==> chore: scaffold"
  git commit -q -m "chore: scaffold repo with .gitignore and .env template

Why: protects the customer from a leaked API key on day one.
What: standard Python + secrets gitignore, plus a .env.example
that documents every variable the tool expects."
fi

# 5. Branch per change
if ! git show-ref --verify --quiet refs/heads/feat/lookup-cli; then
  echo "==> git checkout -b feat/lookup-cli"
  git checkout -q -b feat/lookup-cli
fi

# 6. Make sure lesson 01 file is on this branch
if ! git diff --cached --quiet -- technical/01-python-tooling.py 2>/dev/null; then
  git add technical/01-python-tooling.py
fi
if [[ -n "$(git status --porcelain technical/01-python-tooling.py)" ]]; then
  git add technical/01-python-tooling.py
  echo "==> feat: pf-lookup CLI"
  git commit -q -m "feat: add pf-lookup CLI for one-shot shipment lookups

Why: CS team needs a fast terminal way to look up a single shipment
when the email only mentions one ID. The web tracker is too slow
for this (3-4 clicks, 20 seconds) and CS staff already live in the
terminal.

What: 50-line CLI that reads shipments.json, supports --json output,
returns honest exit codes (0=ok, 1=missing file, 2=missing shipment).
No AI yet — that lands in lesson 04.

Test: python3 technical/01-python-tooling.py PF-1003 prints the
held_customs status; --help lists both flags."
fi

# 7. PR description
mkdir -p .pr
cat > .pr/feat-lookup-cli.md <<'EOF'
# feat: pf-lookup CLI

## What
Adds a 50-line Python CLI that looks up a single shipment by ID
and prints a one-screen summary (or JSON, with --json).

## Why
CS team is currently 4-7 minutes per "where is my parcel?" email.
The first step of that is looking the shipment up. Terminal lookup
takes 2 seconds and lets us automate the rest in lesson 04.

## How to test
    python3 technical/01-python-tooling.py PF-1003
    python3 technical/01-python-tooling.py PF-1003 --json
    python3 technical/01-python-tooling.py PF-9999   # exit 2

## Risk
Low. Read-only against a JSON file. No network. No API key.

## What I am NOT doing
- No AI yet (lesson 04).
- No web UI (Phase 2 if you want one).
- No integration with the real PHP tracker (separate engagement).
EOF

if [[ -n "$(git status --porcelain .pr 2>/dev/null || true)" ]]; then
  git add .pr
  echo "==> docs: PR description"
  git commit -q -m "docs: add PR description for feat/lookup-cli"
fi

echo
echo "==> Final state:"
git log --oneline --decorate --all
echo
echo "==> Branches:"
git branch -v
echo
echo "==> Run 'python3 technical/01-python-tooling.py PF-1003' to verify the CLI still works."
