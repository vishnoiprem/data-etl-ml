#!/bin/sh
# docker-healthcheck.sh — invoked by the Dockerfile's HEALTHCHECK
# directive. Returns 0 if the app is serving, 1 otherwise.
#
# Two-tier check:
#   1. Always: import the runtime modules and run one analysis pass
#      in-process. If anything is missing, the image is broken at
#      install time.
#   2. When the server is listening: an HTTP probe of /healthz.
#      Lets the orchestrator distinguish "package broken" from
#      "server not up yet" — useful when the container is healthy
#      but uvicorn is still binding.
#
# Kept POSIX-sh + python so the script runs on the same base
# (python:3.12-slim → /bin/sh is dash, no bash) without adding a
# shell.
#
# Locally, mark it executable: chmod +x docker-healthcheck.sh.
# Inside the image, Docker runs it with whatever USER the
# HEALTHCHECK is declared under, so file mode is set during
# `docker build`.

set -eu

# Tier 1: import the runtime modules and prove the analysis path
# works end to end. `build_corpus()` + `run_all()` is the cheapest
# possible exercise of the whole detector stack that needs no AWS
# data and no network.
python3 - <<'PY'
from aws_cost_analyzer.detectors.registry import run_all
from aws_cost_analyzer.evaluation import build_corpus
from aws_cost_analyzer.config import load_settings
from aws_cost_analyzer.pricing import default_card

corpus = build_corpus()
findings = run_all(corpus.input, load_settings(), default_card())
assert findings, "the analysis produced no findings"
PY

# Tier 2: if the server is up, probe the liveness endpoint. Use
# urllib rather than httpx so the check has no dependency on the
# HTTP client being importable — a broken httpx install should
# fail tier 1, not masquerade as "server unreachable".
if [ -n "${AWSCA_HEALTHCHECK_URL:-}" ]; then
  python3 - <<'PY'
import os, urllib.request
url = os.environ["AWSCA_HEALTHCHECK_URL"]
with urllib.request.urlopen(url, timeout=5) as r:
    if r.status != 200:
        raise SystemExit(f"health endpoint returned {r.status}")
PY
fi
