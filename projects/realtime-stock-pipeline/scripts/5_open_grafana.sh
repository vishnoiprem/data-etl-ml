#!/usr/bin/env bash
# 5_open_grafana.sh — open Grafana in the default browser (macOS).
set -euo pipefail

URL="http://localhost:3000"

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "==> Opening $URL in default browser"
  open "$URL" || true
elif command -v xdg-open >/dev/null 2>&1; then
  echo "==> Opening $URL via xdg-open"
  xdg-open "$URL" || true
else
  echo "No GUI opener found — please visit $URL manually."
fi

cat <<EOF

Grafana:        $URL
  user:         admin
  password:     admin

Other UIs:
  Flink UI      http://localhost:8081
EOF
