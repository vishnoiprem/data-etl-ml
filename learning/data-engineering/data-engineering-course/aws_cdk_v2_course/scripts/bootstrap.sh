#!/usr/bin/env bash
# bootstrap.sh — install npm dependencies and run tests for the AWS CDK v2 course.
#
# This script is the npm-equivalent of the ``run_all_tests.py`` Python
# entry point. It walks every populated TypeScript CDK project, runs
# ``npm install``, and then runs ``npm test`` in each.

set -euo pipefail

# Resolve the course root from this script's location.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COURSE_ROOT="$(cd "${HERE}/.." && pwd)"

echo "AWS CDK v2 Crash Course — bootstrap"
echo "Course root: ${COURSE_ROOT}"

if ! command -v npm >/dev/null 2>&1; then
    echo "Error: 'npm' is not on the PATH. Install Node 20+ and retry." >&2
    exit 1
fi
if ! command -v node >/dev/null 2>&1; then
    echo "Error: 'node' is not on the PATH. Install Node 20+ and retry." >&2
    exit 1
fi

NODE_MAJOR="$(node -v | sed -E 's/^v([0-9]+)\..*$/\1/')"
if [ "${NODE_MAJOR}" -lt 20 ]; then
    echo "Warning: detected Node ${NODE_MAJOR}.x; CDK v2 prefers Node 20+." >&2
fi

# Every section we walk. Add new sections here.
SECTIONS=(
    "02_app_stack_construct"
    "03_building_with_cdk"
    "04_appsync_stepfunctions"
    "05_testing_cicd"
)

failed=0
for section in "${SECTIONS[@]}"; do
    code_dir="${COURSE_ROOT}/${section}/code"
    if [ ! -d "${code_dir}" ]; then
        continue
    fi
    for project_dir in "${code_dir}"/*/; do
        [ -d "${project_dir}" ] || continue
        if [ ! -f "${project_dir}/package.json" ]; then
            continue
        fi
        project_name="$(basename "${project_dir}")"
        echo
        echo "=========================================================="
        echo "[${section}/${project_name}] npm install"
        echo "=========================================================="
        (cd "${project_dir}" && npm install --no-audit --no-fund)
        echo "[${section}/${project_name}] npm test"
        if (cd "${project_dir}" && npm test --silent); then
            echo "[${section}/${project_name}] OK"
        else
            echo "[${section}/${project_name}] FAIL" >&2
            failed=$((failed + 1))
        fi
    done
done

echo
if [ "${failed}" -eq 0 ]; then
    echo "Bootstrap complete — all projects passed."
else
    echo "Bootstrap finished with ${failed} failing project(s)." >&2
fi
exit "${failed}"
