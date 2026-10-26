#!/bin/sh
# docker-healthcheck.sh — invoked by the Dockerfile's HEALTHCHECK
# directive. Returns 0 if the package is importable (and optionally
# the database is reachable), 1 otherwise.
#
# Two-tier check:
#   1. Always: import the critical Python modules. If anything is
#      missing, the image is broken at install time.
#   2. When AVILX_DB_HOST is set: a lightweight TCP probe to the
#      database. Lets the orchestrator distinguish "package broken"
#      from "database unreachable" — useful when the container is
#      healthy but the DB is restarting.
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

# Tier 1: import the runtime modules.
python3 -c 'import db.lead_store, find_more_leads, resume_tailor'

# Tier 2: if a DB host is configured, probe the TCP socket. Avoid
# psycopg2.connect() so a missing-or-broken driver doesn't mask
# install-time breakage with a connection error.
if [ -n "${AVILX_DB_HOST:-}" ]; then
  python3 <<'PY'
import os, socket
host = os.environ.get("AVILX_DB_HOST", "localhost")
port = int(os.environ.get("AVILX_DB_PORT", "5432"))
s = socket.create_connection((host, port), timeout=5)
s.close()
PY
fi

# Optional: print the in-image version so
# `docker inspect --format='{{.State.Health.Log}}'` shows the
# build SHA / semver when an operator debugs.
if [ -r VERSION ]; then
  printf 'version=%s\n' "$(tr -d '[:space:]' < VERSION)"
fi