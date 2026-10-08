# Contributing

Thanks for stopping by! This is a personal portfolio / lab repo. Contributions
are welcome — but please read this first so we don't waste your time.

## TL;DR

- **Open an issue first** for anything non-trivial (use the templates).
- **One change per PR.** Small, focused, reviewable.
- **Match the surrounding style.** `black` + `ruff` for Python, 4-space indent.
- **Add tests** when adding logic. `pytest -v` must pass.
- **No secrets, no real customer data.** Synthetic / public data only.
- **Be kind.** See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## What this repo is

A consolidated monorepo of:

- **Production-style projects** (runnable end-to-end on synthetic data).
- **Hands-on labs** from courses and reading.
- **Writing** — Medium articles and interview playbooks.
- **Resume / career assets.**

Not everything here is meant to be productionized — many sub-folders are
exercises. If you're unsure where your contribution fits, open an issue
and ask.

## Project areas you can contribute to

| Area | Examples | Where to look |
|---|---|---|
| **Data pipelines** | Spark / Kafka / Flink jobs, schema, dbt models | `data-engineering/`, `realtime-stock-pipeline/`, `flink-cdc-dashboard/` |
| **AI / LLM apps** | RAG ingestion, retrieval, eval, agents | `ai-engineering/`, `agentic-ai/` |
| **Cloud / infra** | AWS, Docker, Terraform, CI | `aws/`, `app/`, `infra/` |
| **Docs / writing** | READMEs, articles, interview guides | `medium/`, `docs/` |
| **Repo hygiene** | Scripts, CI workflows, linting | `scripts/`, `.github/` |

## Local dev

```bash
git clone <this-repo>
cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install   # if .pre-commit-config.yaml is present
pytest -q
bash scripts/repo_stats.sh   # sanity-check the README numbers
```

### Per-project bootstrap

Most projects also have their own `requirements.txt` (sometimes
`requirements-airflow.txt`). Inside any project folder:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # if present; edit it
pytest -q
```

## Coding standards

- **Python** 3.10+, type hints, docstrings on public APIs.
- **Style:** `black` line length 100, `ruff` for lint, `isort` for imports.
- **Logging:** structured JSON via `logging` + `python-json-logger`.
- **Tests:** `pytest`, fixtures under `tests/`, sample data under
  `data/dummy/` (synthetic only).
- **No secrets.** `.env` is git-ignored. Use `.env.example` to document
  required keys.
- **Commit messages:** Conventional Commits where it makes sense
  (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).

## Pull request checklist

- [ ] Linked issue (`Closes #123`) or clear motivation
- [ ] Tests added / updated, all green locally
- [ ] Docs updated (README in the affected project folder)
- [ ] No new secrets, no real PII / customer data
- [ ] `bash scripts/repo_stats.sh` still runs cleanly (if you touched
      top-level files)
- [ ] CI green

## Review SLA

This is a personal repo — review happens in batches, usually within a week.
If your PR is urgent, mention `@pvishnoi` and add the `priority:high` label.

## Reporting a security issue

Please **do not** file a public issue. Email the address in the repo
`Settings → General` and we will respond within 7 days.

## License

By contributing, you agree that your contributions will be licensed under
the [MIT License](LICENSE).