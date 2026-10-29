# Troubleshooting — the 5 things that go wrong on `make demo`

If you ran `make demo` (or any other target) and it didn't
behave like the README says, check this list first. 95% of
"it broke" issues are here. The remaining 5% are usually
"you're offline and didn't realize it" — check that first.

---

## 1. `ModuleNotFoundError: No module named 'fpdf2'`

**Cause:** you skipped `make install`.

**Fix:**
```bash
make install
# or, manually:
pip install -r requirements.txt
```

**Verify:** `python3 -c "import fpdf; print(fpdf.__version__)"`

---

## 2. `ModuleNotFoundError: No module named 'anthropic'`

**Cause:** you have `ANTHROPIC_API_KEY` set but didn't
`pip install anthropic`.

**Fix (one of):**
- Uncomment the `# anthropic>=0.30.0` line in `requirements.txt`,
  then `make install`.
- Or unset the env var and let the router fall back to
  `StubRouter` (offline mode):
  ```bash
  unset ANTHROPIC_API_KEY
  unset OPENAI_API_KEY
  make demo
  ```

The `StubRouter` returns template-based content for all 4
streams. The demo works the same; the content is less
varied. Sufficient for testing the pipeline, not for
production use.

---

## 3. `make demo` runs but the dashboard says `$0.00 / 0 events`

**Cause:** `ledger.db` is empty. This happens after a fresh
clone + `make clean`, or if you ran the streams individually
without the orchestrator.

**Fix:** run `make demo` (not `make stream-1` etc.) — the
orchestrator writes a starting ledger entry. Or run
`make simulate-30d` to inject 30 days of synthetic data.

```bash
make demo              # 1 day of real-looking data
make simulate-30d      # 30 days of synthetic data
make dashboard         # print the dashboard
```

---

## 4. `Permission denied: ledger.db` after `make demo`

**Cause:** `ledger.db` was created by a different user (e.g.
you ran `make demo` as root once, or it was committed and
owned by another user on a shared checkout).

**Fix:**
```bash
rm -f ledger.db
make demo
```

The `make clean` target does the same. The DB is re-creatable
from scratch.

---

## 5. `output/` is empty or has fewer products than the README claims

**Cause:** a previous `make clean` removed it, or you ran an
individual stream (`make stream-3`) which only writes the
products for that stream.

**Fix:**
```bash
make demo              # writes all 4 streams' products
```

If you only want stream 3 products, that's correct behavior
— but you'll see ~3 products instead of ~9.

---

## 6. The LLM returns weird JSON (`KeyError: 'ideas'`)

**Cause:** the LLM didn't follow the JSON schema. This is
real, not a bug in the router. The OpenAI Router uses
`response_format={"type": "json_object"}` which mostly
works, but the Anthropic Router asks for JSON in the prompt
and gets it back ~95% of the time. The 5% case is bad.

**Fix (try in order):**
1. Re-run — the prompt is deterministic so the second call
   usually works.
2. Lower `max_tokens` — some models truncate long JSON
   responses and produce invalid output.
3. Switch providers — `unset ANTHROPIC_API_KEY && make demo`
   falls back to OpenAI (or vice versa).
4. Open an issue with the exact prompt + the model version.

---

## 7. `make test` fails with `ImportError: No module named 'src.X'`

**Cause:** you're not in the project root. The `conftest.py`
adds `src/` to `sys.path`, but only when pytest runs from
the project root.

**Fix:**
```bash
cd ai-engineering/40-ai-side-hustle
make test
```

---

## When the issue is NOT in this list

1. Run with `PYTHONPATH=. python3 scripts/run_factory.py` instead
   of `make demo` — you get a real traceback instead of
   Make's "recipe failed" one-liner.
2. Check `ledger.db` with `sqlite3 ledger.db "SELECT * FROM
   events LIMIT 5"` — if it has rows, the streams worked and
   the issue is just the dashboard render.
3. Open a GitHub issue with the output of `python3 --version`,
   `pip freeze`, and the failing command. The issue template
   asks for exactly this.

---

**See also:**
- [`FIRST_DOLLAR.md`](./FIRST_DOLLAR.md) — the 7-day runbook
- [`../README.md`](../README.md) — the project overview
