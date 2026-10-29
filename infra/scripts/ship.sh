#!/usr/bin/env bash
# scripts/ship.sh
# Curate + ship a commit on master. Wraps the loop we've been doing by hand:
#
#   1. detect local-only wip(auto-snapshot) commits since the last
#      "real" merge commit (or the last curated commit on master)
#   2. soft-reset them so all of their content lands in the index
#   3. let you write a proper commit message (or pass one via -m)
#   4. pre-push gates: secret-scan the staged tree, py_compile-check
#      any newly added .py files, refuse to push if either fails
#   5. fast-forward push to origin/master (never force-pushes)
#
# Default usage (interactive, asks for message):
#   bash infra/scripts/ship.sh
#
# Non-interactive, with a message inline:
#   bash infra/scripts/ship.sh -m "fix(course): repair trades_gemini SyntaxError"
#
# Refuse the soft-reset (treat any local wip as sacred, just commit
# on top as normal — useful when you've reviewed the snapshots):
#   bash infra/scripts/ship.sh --no-squash -m "..."
#
# Dry run (everything except the actual commit + push):
#   bash infra/scripts/ship.sh --dry-run

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# ---- arg parsing -----------------------------------------------------------

MSG=""
DO_SQUASH=1
DRY_RUN=0

usage() {
  sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

while [ $# -gt 0 ]; do
  case "$1" in
    -m)            MSG="$2"; shift 2 ;;
    --no-squash)   DO_SQUASH=0; shift ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -h|--help)     usage ;;
    *)             echo "unknown flag: $1" >&2; exit 2 ;;
  esac
done

# ---- preflight -------------------------------------------------------------

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "FATAL: $REPO_ROOT is not a git working tree" >&2
  exit 1
fi

CURR_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$CURR_BRANCH" != "master" ]; then
  echo "FATAL: ship.sh refuses to run on branch '$CURR_BRANCH' (master only)." >&2
  echo "       Switch first: git checkout master" >&2
  exit 1
fi

# Refuse to clobber someone else's unpushed work.
AHEAD_OF_ORIGIN="$(git rev-list --count origin/master..master 2>/dev/null || echo 0)"
BEHIND_ORIGIN="$(git rev-list --count master..origin/master 2>/dev/null || echo 0)"

if [ "$BEHIND_ORIGIN" -gt 0 ]; then
  echo "FATAL: local master is BEHIND origin/master by $BEHIND_ORIGIN commit(s)." >&2
  echo "       Run 'git pull --ff-only' before shipping." >&2
  exit 1
fi

# ---- step 1: detect + (optionally) squash local-only wip commits ------------

# A wip commit is one whose subject starts with 'wip('.
# Local-only = not on origin/master yet.
LOCAL_WIP=$(git log origin/master..master \
              --pretty=%H \
              --grep='^wip(' \
              2>/dev/null || true)

WIP_COUNT=$(printf '%s\n' "$LOCAL_WIP" | grep -c . || true)

if [ "$WIP_COUNT" -gt 0 ] && [ "$DO_SQUASH" -eq 1 ]; then
  # Find the oldest wip and step back one commit to capture it as the baseline
  # (so the soft-reset includes ALL local wip commits + everything since).
  OLDEST_WIP_SHA=$(git log origin/master..master \
                     --pretty=%H \
                     --grep='^wip(' \
                     --reverse \
                     2>/dev/null | head -1)
  BASELINE_SHA="$(git rev-parse "${OLDEST_WIP_SHA}^" 2>/dev/null || echo origin/master)"

  echo "==> Found $WIP_COUNT local-only wip auto-snapshot commit(s)"
  git log --oneline "$BASELINE_SHA..master"
  echo ""
  echo "    Soft-resetting to '$BASELINE_SHA' (everything stays staged)..."

  if [ "$DRY_RUN" -eq 1 ]; then
    echo "    --dry-run: skipping reset"
  else
    git reset --soft "$BASELINE_SHA"
  fi
elif [ "$WIP_COUNT" -gt 0 ]; then
  echo "==> --no-squash set: leaving $WIP_COUNT local wip commit(s) in place."
fi

# ---- step 2: staging state -------------------------------------------------

STAGED=$(git diff --cached --name-only | wc -l | tr -d ' ')
WORKTREE=$(git diff --name-only | wc -l | tr -d ' ')

if [ "$STAGED" -eq 0 ]; then
  echo ""
  echo "Nothing staged. Stage your edits first, e.g.:"
  echo "  git add path/to/file"
  echo "Then re-run: bash infra/scripts/ship.sh"
  exit 1
fi

echo "==> Staged: $STAGED files  |  Unstaged: $WORKTREE files"

# ---- step 3: pre-push gates ------------------------------------------------

echo ""
echo "==> Gate 1: secret scan on staged content"

# High-entropy credential patterns only; deliberately noisy patterns
# (e.g. literal "sk-" in CSS) are filtered by a placeholder allow-list.
PATTERN='(sk-[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,})'

HITS=$(git diff --cached --name-only \
        | grep -E '\.(py|ipynb|env|json|toml|yaml|yml|sh|js|ts|tsx|md|txt)$' \
        | while read -r f; do
            git show ":$f" 2>/dev/null
          done \
        | grep -oE "$PATTERN" | sort -u || true)

if [ -n "$HITS" ]; then
  echo ""
  echo "FATAL: secret pattern(s) detected in staged content:"
  printf '  %s\n' $HITS
  echo ""
  echo "If these are demo strings / documentation, exempt them by"
  echo "moving them out of staged files first. Otherwise treat as"
  echo "a real leak: rotate the key, then re-stage."
  exit 1
fi
echo "    OK"

echo ""
echo "==> Gate 2: py_compile sweep on staged .py"

BAD_PY=""
git diff --cached --name-only --diff-filter=ACMR \
  | grep -E '\.py$' \
  | while read -r f; do
      TMP=$(mktemp -t ship-pycheck.XXXXXX.py)
      git show ":$f" > "$TMP" 2>/dev/null
      if ! python3 -m py_compile "$TMP" >/dev/null 2>&1; then
        echo "$f"
      fi
      rm -f "$TMP"
    done > /tmp/ship-pycheck.$$ 2>/dev/null

if [ -s /tmp/ship-pycheck.$$ ]; then
  echo "FATAL: these staged .py files don't compile:"
  cat /tmp/ship-pycheck.$$
  rm -f /tmp/ship-pycheck.$$
  exit 1
fi
rm -f /tmp/ship-pycheck.$$
echo "    OK"

# ---- step 4: commit --------------------------------------------------------

if [ "$DRY_RUN" -eq 1 ]; then
  echo ""
  echo "--dry-run: would now commit $STAGED files with message:"
  if [ -n "$MSG" ]; then
    echo "    $MSG"
  else
    echo "    (interactive editor)"
  fi
  echo "--dry-run: would then push origin master"
  exit 0
fi

if [ -n "$MSG" ]; then
  git commit -m "$MSG" 2>&1 | tail -5
else
  git commit  # opens $EDITOR
fi

COMMIT_SHA=$(git rev-parse HEAD)
echo ""
echo "==> Commit: $COMMIT_SHA  ($(git log -1 --pretty=%s))"

# ---- step 5: push ----------------------------------------------------------

echo ""
echo "==> Pushing origin/master (fast-forward only)"

if ! git push origin master 2>&1 | tail -5; then
  echo ""
  echo "FATAL: push failed. Resolve the upstream conflict and re-run."
  echo "       (ship.sh will never force-push.)"
  exit 1
fi

echo ""
echo "==> Shipped. master is at $(git rev-parse --short HEAD)."
