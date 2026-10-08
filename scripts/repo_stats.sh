#!/usr/bin/env bash
# scripts/repo_stats.sh
# Prints repo stats that the README "By the numbers" table references.
# Usage:  bash scripts/repo_stats.sh
#         bash scripts/repo_stats.sh --json   # machine-readable
#
# Excludes .git, .idea, .pytest_cache, .env, .puku-cli, virtualenvs, and caches.

set -euo pipefail

# Resolve repo root from the script's location (works no matter where you run it).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

EXCLUDES=(
  -path "*/.git/*"      -o -path "*/.idea/*"
  -o -path "*/.pytest_cache/*"
  -o -path "*/.env/*"   -o -path "*/.puku-cli/*"
  -o -path "*/node_modules/*"
  -o -path "*/__pycache__/*"
  -o -path "*/.venv/*"  -o -path "*/venv/*"
)

count_files() {
  local ext="$1"
  # find + -prune for the patterns
  find . \( "${EXCLUDES[@]}" \) -prune -o -type f -name "$ext" -print 2>/dev/null | wc -l | tr -d ' '
}

SRC_PY=$(count_files "*.py")
SRC_SQL=$(count_files "*.sql")
SRC_YML=$(count_files "*.yml")
SRC_YAML=$(count_files "*.yaml")
SRC_DOCKER=$(count_files "Dockerfile")
SRC_JSON=$(count_files "*.json")
DOC_MD=$(count_files "*.md")
DOC_IPYNB=$(count_files "*.ipynb")

TOTAL_SRC=$((SRC_PY + SRC_SQL + SRC_YML + SRC_YAML + SRC_DOCKER + SRC_JSON))
TOTAL_DOC=$((DOC_MD + DOC_IPYNB))

# Per-folder README count, useful for the headline-projects claim
README_COUNT=$(count_files "README.md")
PROJECT_DIRS=$(find . \( "${EXCLUDES[@]}" \) -prune -o -type d -print 2>/dev/null | wc -l | tr -d ' ')

if [[ "${1:-}" == "--json" ]]; then
  cat <<EOF
{
  "src": {
    "python":   ${SRC_PY},
    "sql":      ${SRC_SQL},
    "yml":      ${SRC_YML},
    "yaml":     ${SRC_YAML},
    "dockerfile": ${SRC_DOCKER},
    "json":     ${SRC_JSON},
    "total":    ${TOTAL_SRC}
  },
  "docs": {
    "markdown":  ${DOC_MD},
    "ipynb":     ${DOC_IPYNB},
    "total":     ${TOTAL_DOC}
  },
  "meta": {
    "readmes":         ${README_COUNT},
    "directories":     ${PROJECT_DIRS},
    "generated_at":    "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  }
}
EOF
else
  cat <<EOF
📊 Repository stats (excluding .git, .idea, caches, venvs)

   Source files
   ────────────
   Python            ${SRC_PY}
   SQL               ${SRC_SQL}
   YAML (yml+yaml)   $((SRC_YML + SRC_YAML))
   Dockerfile        ${SRC_DOCKER}
   JSON              ${SRC_JSON}
   TOTAL SOURCE      ${TOTAL_SRC}

   Docs / notebooks
   ────────────────
   Markdown          ${DOC_MD}
   Jupyter           ${DOC_IPYNB}
   TOTAL DOCS        ${TOTAL_DOC}

   Meta
   ────
   README.md files   ${README_COUNT}
   Directories       ${PROJECT_DIRS}
   Generated         $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
fi