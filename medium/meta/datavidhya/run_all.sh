#!/usr/bin/env bash
# Run every problem file and report PASS/FAIL. Solutions are self-asserting:
# each one checks its query against hand-computed expected output, so a green
# run means the SQL is actually correct, not just syntactically valid.
cd "$(dirname "$0")" || exit 1

# Absolute path — the loop cd's into each subfolder, so a relative one breaks.
PY="$(cd ../../.. && pwd)/.env/bin/python"
if [ ! -x "$PY" ]; then echo "no venv python at $PY" >&2; exit 1; fi

pass=0; fail=0; failed=()
for f in $(find . -name '[0-9]*.py' -not -path '*.ipynb_checkpoints*' | sort); do
  d=$(dirname "$f"); b=$(basename "$f")
  if (cd "$d" && "$PY" "$b" >/dev/null 2>&1); then
    pass=$((pass+1)); printf '  ok   %s\n' "$f"
  else
    fail=$((fail+1)); failed+=("$f"); printf '  FAIL %s\n' "$f"
  fi
done
echo
echo "$pass passed, $fail failed"
for f in "${failed[@]}"; do echo "  failed: $f"; done
[ "$fail" -eq 0 ]
