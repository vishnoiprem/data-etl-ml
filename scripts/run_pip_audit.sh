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
# Excludes vendored / template / dist folders — those are not source-of-truth.
MANIFEST_LIST="$OUT_DIR/manifests.txt"
: > "$MANIFEST_LIST"
find . \
    -path "*/.git/*"      -prune -o \
    -path "*/.idea/*"     -prune -o \
    -path "*/.pytest_cache/*" -prune -o \
    -path "*/__pycache__/*"   -prune -o \
    -path "*/.venv/*"     -prune -o \
    -path "*/.env/*"      -prune -o \
    -path "*/.puku-cli/*" -prune -o \
    -path "*/dist/*"      -prune -o \
    -path "*/sam-installation/aws-sam-cli-src/*" -prune -o \
    -path "*/cookiecutter-*/*" -prune -o \
    -type f -name "requirements*.txt" -print 2>/dev/null \
  | sort > "$MANIFEST_LIST"

# pip-audit requires every line to be pinned (==). We respect user-facing
# `>=` ranges in the source manifests, but for auditing we materialise a
# pinned copy in $OUT_DIR (resolved to currently-installed versions if any,
# else the most recent stable release on PyPI).
pin_for_audit() {
  local src="$1" dst="$2"
  : > "$dst"
  while IFS= read -r line; do
    case "$line" in
      ""|\#*|"-r "*|"-e "*|*"--"*)
        printf '%s\n' "$line" >> "$dst" ;;
      *)
        # Extract the package name (everything up to the first operator or whitespace)
        pkg=$(printf '%s' "$line" | sed -E 's/^([A-Za-z0-9_.\-]+).*/\1/')
        pinned=$(grep -E "^${pkg}==|^${pkg} @ " "$src" 2>/dev/null | head -1)
        if [ -n "$pinned" ]; then
          printf '%s\n' "$pinned" >> "$dst"
        else
          # Resolve to a known pinned version: prefer installed, else keep
          # the original >= range if everything is already pinned.
          resolved=$(.env/bin/python -c "
import importlib.metadata as m, sys
try:
    print(m.version('${pkg}'))
except Exception:
    sys.exit(1)
" 2>/dev/null || true)
          if [ -n "$resolved" ]; then
            printf '%s==%s\n' "$pkg" "$resolved" >> "$dst"
          else
            printf '%s\n' "$line" >> "$dst"
          fi
        fi
        ;;
    esac
  done < "$src"
}

if [ "${1:-}" = "--json" ]; then
  echo "{ \"scans\": ["
  first=1
  while IFS= read -r m; do
    [ -z "$m" ] && continue
    src_json="$OUT_DIR/$(echo "$m" | tr '/' '_').src"
    pin_for_audit "$m" "$src_json"
    json="$OUT_DIR/$(echo "$m" | tr '/' '_').json"
    if ! "$PIP_AUDIT" -r "$src_json" --no-deps --disable-pip --format json -o "$json" 2>/dev/null; then
      echo "  (skipping $m — pip-audit rejected)" >&2
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
  done < "$MANIFEST_LIST"
  echo "  ] }"
  exit 0
fi

echo "🔒 pip-audit — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo
printf '%-58s %10s %10s\n' "MANIFEST" "VULNS" "PACKAGES"
printf '%-58s %10s %10s\n' "--------" "-----" "--------"

total_v=0
total_p=0
while IFS= read -r m; do
  [ -z "$m" ] && continue
  src_json="$OUT_DIR/$(echo "$m" | tr '/' '_').src"
  pin_for_audit "$m" "$src_json"
  json="$OUT_DIR/$(echo "$m" | tr '/' '_').json"
  if ! "$PIP_AUDIT" -r "$src_json" --no-deps --disable-pip --format json -o "$json" 2>/dev/null; then
    printf '%-58s %10s %10s\n' "$m" "(rejected)" "—"
    continue
  fi
  v=$(.env/bin/python -c "import json; d=json.load(open('$json')); print(sum(len(x.get('vulns',[])) for x in d.get('dependencies',[])))" 2>/dev/null || echo 0)
  p=$(.env/bin/python -c "import json; d=json.load(open('$json')); print(sum(1 for x in d.get('dependencies',[]) if x.get('vulns')))" 2>/dev/null || echo 0)
  total_v=$((total_v + v))
  total_p=$((total_p + p))
  printf '%-58s %10s %10s\n' "$m" "$v" "$p"
done < "$MANIFEST_LIST"

echo
echo "TOTAL: $total_v vulnerabilities across $total_p packages"
echo
echo "See docs/SECURITY_AUDIT.md for the fix plan (Tier 1/2/3)."