#!/usr/bin/env bash
# scripts/run_pip_audit.sh
# Audit every pinned requirements manifest in the repo and report counts.
#
# Usage:
#   bash scripts/run_pip_audit.sh           # human-readable summary
#   bash scripts/run_pip_audit.sh --json    # machine-readable (per-manifest)
#
# See docs/SECURITY_AUDIT.md for context and the fix plan.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PIP_AUDIT="${PIP_AUDIT:-$REPO_ROOT/.env/bin/pip-audit}"
if ! command -v "$PIP_AUDIT" >/dev/null 2>&1; then
  PIP_AUDIT="$(command -v pip-audit || true)"
fi
if [ -z "$PIP_AUDIT" ]; then
  echo "pip-audit not found. Activate your venv or: pip install pip-audit==2.10.1"
  exit 1
fi

OUT_DIR="$REPO_ROOT/.puku-cli"
mkdir -p "$OUT_DIR"

# Discover manifests (top-level + per-project), excluding anything that
# doesn't look like a pip requirements file. POSIX-compatible (no mapfile).
MANIFESTS=""
while IFS= read -r m; do
  MANIFESTS="$MANIFESTS$m
"
done < <(
  find . \
    -path "*/.git/*"      -prune -o \
    -path "*/.idea/*"     -prune -o \
    -path "*/.pytest_cache/*" -prune -o \
    -path "*/__pycache__/*"   -prune -o \
    -path "*/.venv/*"     -prune -o \
    -path "*/.env/*"      -prune -o \
    -path "*/.puku-cli/*" -prune -o \
    -type f -name "requirements*.txt" -print 2>/dev/null | sort
)

if [ "${1:-}" = "--json" ]; then
  echo "{ \"scans\": ["
  first=1
  for m in "${MANIFESTS[@]}"; do
    json="$OUT_DIR/$(echo "$m" | tr '/' '_').json"
    if ! "$PIP_AUDIT" -r "$m" --no-deps --disable-pip --format json -o "$json" 2>/dev/null; then
      # Manifest hygiene: at least one unpinned entry. Still try to continue.
      echo "  (skipping $m — un-pinned entries)" >&2
      continue
    fi
    vulns=$(.env/bin/python -c "import json,sys; d=json.load(open('$json')); print(sum(len(x.get('vulns',[])) for x in d.get('dependencies',[])))" 2>/dev/null || echo "0")
    pkgs=$(.env/bin/python -c "import json; d=json.load(open('$json')); print(sum(1 for x in d.get('dependencies',[]) if x.get('vulns')))" 2>/dev/null || echo "0")
    [ $first -eq 0 ] && echo "," || first=0
    .env/bin/python -c "
import json
d = json.load(open('$json'))
print('    { \"manifest\": \"$m\", \"vulnerabilities\": $vulns, \"packages_affected\": $pkgs }')
"
  done
  echo "  ] }"
  exit 0
fi

echo "🔒 pip-audit — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo
printf '%-58s %10s %10s\n' "MANIFEST" "VULNS" "PACKAGES"
printf '%-58s %10s %10s\n' "--------" "-----" "--------"

total_v=0
total_p=0
for m in "${MANIFESTS[@]}"; do
  json="$OUT_DIR/$(echo "$m" | tr '/' '_').json"
  if ! "$PIP_AUDIT" -r "$m" --no-deps --disable-pip --format json -o "$json" 2>/dev/null; then
    printf '%-58s %10s %10s\n' "$m" "(unpinned)" "—"
    continue
  fi
  v=$(.env/bin/python -c "import json; d=json.load(open('$json')); print(sum(len(x.get('vulns',[])) for x in d.get('dependencies',[])))" 2>/dev/null || echo 0)
  p=$(.env/bin/python -c "import json; d=json.load(open('$json')); print(sum(1 for x in d.get('dependencies',[]) if x.get('vulns')))" 2>/dev/null || echo 0)
  total_v=$((total_v + v))
  total_p=$((total_p + p))
  printf '%-58s %10s %10s\n' "$m" "$v" "$p"
done

echo
echo "TOTAL: $total_v vulnerabilities across $total_p packages"
echo
echo "See docs/SECURITY_AUDIT.md for the fix plan (Tier 1/2/3)."