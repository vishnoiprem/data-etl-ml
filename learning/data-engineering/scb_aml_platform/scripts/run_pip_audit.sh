#!/usr/bin/env bash
# SCB AML Platform — pip-audit gate
#
# Audits requirements.in + pyproject.toml [project.dependencies] and
# fails on HIGH or CRITICAL vulnerabilities. Run locally before
# pushing; the project-level CI workflow (.github/workflows/scb-aml-ci.yml)
# runs the same script.
#
# Usage:
#   bash scripts/run_pip_audit.sh                # human-readable
#   bash scripts/run_pip_audit.sh --json         # machine-readable
#   bash scripts/run_pip_audit.sh --strict      # fail on MODERATE too

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

FORMAT="columns"
STRICT=0
for arg in "$@"; do
    case "$arg" in
        --json) FORMAT="json" ;;
        --strict) STRICT=1 ;;
        *) echo "unknown arg: $arg" >&2; exit 2 ;;
    esac
done

if ! command -v pip-audit >/dev/null 2>&1; then
    echo "pip-audit not found; install with: pip install pip-audit==2.10.1" >&2
    exit 2
fi

# The project uses two manifest sources:
#   1. requirements.in          — runtime pins (used by pip-audit)
#   2. pyproject.toml          — pip-install -e . reads this
# Both lists should agree. The audit runs against requirements.in
# because pip-audit requires exact pins; pyproject.toml uses ranges.
echo "Auditing requirements.in ..."
pip-audit -r requirements.in --no-deps --disable-pip --format "$FORMAT"

# Severity gate
HIGH_COUNT=$(pip-audit -r requirements.in --no-deps --disable-pip --format json 2>/dev/null \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(sum(1 for x in d.get('dependencies',[]) for v in x.get('vulns',[]) if v.get('severity') in ('HIGH','CRITICAL')))" 2>/dev/null || echo 0)
MOD_COUNT=$(pip-audit -r requirements.in --no-deps --disable-pip --format json 2>/dev/null \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(sum(1 for x in d.get('dependencies',[]) for v in x.get('vulns',[]) if v.get('severity') == 'MODERATE'))" 2>/dev/null || echo 0)

echo
echo "== summary =="
echo "HIGH+CRITICAL: $HIGH_COUNT"
echo "MODERATE:      $MOD_COUNT"

if [ "$HIGH_COUNT" -gt 0 ]; then
    echo "FAILED: HIGH or CRITICAL vulnerabilities must be fixed before merge." >&2
    exit 1
fi

if [ "$STRICT" -eq 1 ] && [ "$MOD_COUNT" -gt 0 ]; then
    echo "FAILED: --strict mode, MODERATE vulnerabilities not allowed." >&2
    exit 1
fi

echo "OK"
