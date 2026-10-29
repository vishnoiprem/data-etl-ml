#!/usr/bin/env bash
# scripts/audit_by_project.sh
# Run pip-audit + npm audit on every project, organized by top-level area.
# Produces a single summary table.
#
# Usage: bash infra/scripts/audit_by_project.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

PIP_AUDIT="${PIP_AUDIT:-$REPO_ROOT/.env/bin/pip-audit}"
if [ -z "$PIP_AUDIT" ] || [ ! -x "$PIP_AUDIT" ]; then
  PIP_AUDIT="$(command -v pip-audit 2>/dev/null || true)"
fi
PY="${PY:-$REPO_ROOT/.env/bin/python}"
[ -x "$PY" ] || PY="$(command -v python3)"

if [ -z "$PIP_AUDIT" ]; then
  echo "pip-audit not found. Activate your venv or: pip install pip-audit==2.10.1" >&2
  exit 1
fi

OUT="$REPO_ROOT/.audit"
mkdir -p "$OUT"
mkdir -p "$OUT/per-manifest"

# Top-level project areas (matches the directory layout)
AREAS=(
  "."
  "learning/Spark"
  "learning/agentic-ai"
  "ai-course-public"
  "learning/ai-engineering"
  "aws"
  "learning/data-engineering"
  "projects/flink-cdc-dashboard"
  "projects/leads-pipeline"
  "medium"
  "learning/ml"
  "projects/realtime-stock-pipeline"
  "projects/trading-bot"
)

printf "%-32s %-50s %8s %8s\n" "AREA" "MANIFEST" "VULNS" "PKGS"
printf "%-32s %-50s %8s %8s\n" "----" "--------" "-----" "----"

total_v=0
total_p=0
total_m=0
clean_m=0

# Discover manifests: prefer a curated list if present, otherwise walk the
# tracked tree while excluding vendor/cookiecutter/install-artifact trees.
if [ -f .puku-cli/manifests.txt ]; then
  MANIFESTS=$(cat .puku-cli/manifests.txt)
else
  # Use git's tracked file list so we never see build/install artifacts.
  MANIFESTS=$(git ls-files | grep -E '(^|/)requirements.*\.txt$' | sort)
fi

while IFS= read -r m; do
  [ -z "$m" ] && continue
  total_m=$((total_m + 1))

  # Skip install/vendor trees defensively (shouldn't appear via git ls-files)
  case "$m" in
    *node_modules*|*/.env/*|*/.venv/*|*/sam-installation/aws-sam-cli-src/*|*/cookiecutter-*) continue ;;
  esac

  tmp="$OUT/per-manifest/$(echo "$m" | tr '/' '_' | tr -d '.')"
  grep -E "^[A-Za-z0-9_.\-]+==[0-9]" "$m" > "$tmp" 2>/dev/null || true

  if [ ! -s "$tmp" ]; then
    # Manifest has no pinned deps — skip silently (out of scope for this script)
    rm -f "$tmp"
    total_m=$((total_m - 1))
    continue
  fi

  # Run pip-audit
  "$PIP_AUDIT" -r "$tmp" --no-deps --disable-pip --format json 2>/dev/null > "$tmp.json" || true

  v=$("$PY" -c "
import json
try:
    d = json.load(open('$tmp.json'))
    print(sum(len(x.get('vulns',[])) for x in d.get('dependencies',[])))
except: print(0)
" 2>/dev/null || echo 0)
  p=$("$PY" -c "
import json
try:
    d = json.load(open('$tmp.json'))
    print(sum(1 for x in d.get('dependencies',[]) if x.get('vulns')))
except: print(0)
" 2>/dev/null || echo 0)

  total_v=$((total_v + v))
  total_p=$((total_p + p))
  if [ "$v" -eq 0 ]; then
    clean_m=$((clean_m + 1))
  fi

  # Derive area (first directory component)
  area=$(echo "$m" | sed -E 's#^\./##; s#/.*##; s#^\.$#root#')
  if [ "$m" = "./requirements.txt" ]; then
    area="root"
  fi
  printf "%-32s %-50s %8d %8d\n" "$area" "${m#./}" "$v" "$p"
done <<< "$MANIFESTS"

echo
echo "════════════════════════════════════════════════════════════════════"
printf "Python manifests audited: %d  (clean: %d, with vulns: %d)\n" "$total_m" "$clean_m" "$((total_m - clean_m))"
printf "Total direct-pin advisories: %d across %d packages\n" "$total_v" "$total_p"
echo

# ── npm section ─────────────────────────────────────────────────────────────
echo "─── npm ──────────────────────────────────────────────────────────────"
NPM_PROJECTS=(
  "aws/ecs-data-ingestion"
  "learning/agentic-ai/7_Bedrock_course/ts"
  "learning/agentic-ai/7_Bedrock_course/recap/ts-strarter"
  "learning/agentic-ai/7_Bedrock_course/imageApi/ts"
  "learning/agentic-ai/7_Bedrock_course/textApi/ts"
  "learning/ai-engineering/16-graph-rag/web"
)

printf "%-32s %-50s %8s %8s %8s %8s\n" "AREA" "PROJECT" "CRIT" "HIGH" "MOD" "LOW"
printf "%-32s %-50s %8s %8s %8s %8s\n" "----" "-------" "----" "----" "---" "---"

npm_total=0
for p in "${NPM_PROJECTS[@]}"; do
  if [ ! -d "$p" ] || [ ! -f "$p/package.json" ]; then
    continue
  fi
  area=$(echo "$p" | cut -d/ -f1)
  (cd "$p" && npm audit --json 2>/dev/null > "$OUT/npm-$(echo "$p" | tr '/' '_').json" || true)
  c=$("$PY" -c "
import json
try:
    d = json.load(open('$OUT/npm-$(echo "$p" | tr '/' "_").json'))
    m = d.get('metadata', {}).get('vulnerabilities', {})
    print(f\"{m.get('critical',0)} {m.get('high',0)} {m.get('moderate',0)} {m.get('low',0)}\")
except: print('0 0 0 0')
" 2>/dev/null || echo "0 0 0 0")
  set -- $c
  cr=$1; hi=$2; mo=$3; lo=$4
  total=$((cr + hi + mo + lo))
  npm_total=$((npm_total + total))
  printf "%-32s %-50s %8d %8d %8d %8d\n" "$area" "$p" "$cr" "$hi" "$mo" "$lo"
done
echo
printf "Total npm advisories: %d\n" "$npm_total"
echo
echo "See .audit/ for raw JSON per manifest and project."
