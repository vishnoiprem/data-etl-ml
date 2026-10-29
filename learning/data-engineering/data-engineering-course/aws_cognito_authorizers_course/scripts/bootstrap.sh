#!/usr/bin/env bash
# bootstrap.sh — set up a fresh Python environment for the AWS Cognito
# Authorizers Crash Course.
#
# Author: Prem Vishnoi <pvishnoi@avilx.com>
#
# This script is POSIX-compatible (uses only bash builtins, no GNU-only
# flags) and is safe to re-run. On every invocation it will:
#
#   1. Create .venv/ if it does not already exist (or refuse to clobber
#      an existing environment that does not look like a venv).
#   2. Activate the venv in the current shell.
#   3. Upgrade pip, setuptools, and wheel.
#   4. Install the course's requirements.txt (root of the course).
#   5. Print the AWS CLI version if installed (warns if missing).
#   6. Echo a short list of the next steps the student should take.

set -euo pipefail

# Resolve the course root (the parent of the directory this script lives in)
# so the script can be sourced from any CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COURSE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${COURSE_ROOT}"

echo ">>> Course root: ${COURSE_ROOT}"

# --- 1. venv ---------------------------------------------------------------
VENV_DIR="${COURSE_ROOT}/.venv"
if [ -d "${VENV_DIR}" ]; then
    if [ ! -x "${VENV_DIR}/bin/python" ]; then
        echo "ERROR: ${VENV_DIR} exists but is not a Python virtual environment." >&2
        echo "       Remove it (rm -rf ${VENV_DIR}) and re-run this script." >&2
        exit 1
    fi
    echo ">>> Reusing existing venv at ${VENV_DIR}"
else
    echo ">>> Creating venv at ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# --- 2. pip upgrade --------------------------------------------------------
echo ">>> Upgrading pip, setuptools, wheel"
python3 -m pip install --upgrade pip setuptools wheel

# --- 3. requirements -------------------------------------------------------
REQ_FILE="${COURSE_ROOT}/requirements.txt"
if [ ! -f "${REQ_FILE}" ]; then
    echo "ERROR: requirements.txt not found at ${REQ_FILE}" >&2
    exit 1
fi
echo ">>> Installing requirements from ${REQ_FILE}"
python3 -m pip install -r "${REQ_FILE}"

# --- 4. AWS CLI sanity check ----------------------------------------------
if command -v aws >/dev/null 2>&1; then
    AWS_VERSION="$(aws --version 2>&1 || true)"
    echo ">>> AWS CLI detected: ${AWS_VERSION}"
    if ! echo "${AWS_VERSION}" | grep -q 'aws-cli/2'; then
        echo "    WARNING: AWS CLI v1 is end-of-life. Install v2:"
        echo "      https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    fi
else
    echo ">>> AWS CLI is NOT installed."
    echo "    Install AWS CLI v2 before running the assignments:"
    echo "      https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    echo "    (Bootstrap continues — this is a warning, not an error.)"
fi

# --- 5. Next steps ---------------------------------------------------------
cat <<'NEXT'

=== AWS Cognito Authorizers course — next steps ===

1. Configure AWS credentials (only once per machine):
       aws configure sso
   or with long-lived keys:
       aws configure

2. Sanity-check your setup:
       aws sts get-caller-identity
       python3 -c "import boto3, moto, jwt; print('boto3', boto3.__version__); print('moto', moto.__version__); print('jwt', jwt.__version__)"

3. Run the test suite (moto-based, no AWS calls):
       python3 scripts/run_all_tests.py -v

4. Pick a section to start with (the README.md has the full map):
       01_foundations  ->  02_user_pools  ->  03_identity_pools  ->  04_api_gateway_integration  ->  05_advanced_patterns

5. When you're ready for a graded task, work through
       assignments/assignment_1_user_pool_api.md  (4h)
   in order — they build on each other.

NEXT

echo ">>> Bootstrap complete. Activate the venv with:"
echo "       source ${VENV_DIR}/bin/activate"
