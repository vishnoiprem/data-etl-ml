.PHONY: test lint fmt ledger

test:
	pytest

lint:
	ruff check .
	ruff format --check .

fmt:
	ruff check --fix .
	ruff format .

# Show the current cycle's ledger, if one exists.
ledger:
	@test -d shared/notes/ledger || (echo "no ledger yet — run a cycle first"; exit 1)
	@cat shared/notes/ledger/*.jsonl 2>/dev/null | tail -50