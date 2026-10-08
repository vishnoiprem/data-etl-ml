# Contributing

Thanks for stopping by! This is a personal portfolio / lab repo. Contributions are
welcome — but please read this first so we don't waste your time.

## Ground rules

1. **Open an issue first** for anything non-trivial. Use the templates provided.
2. **One change per PR.** Small, focused, reviewable.
3. **Match the surrounding style.** `black` + `ruff` for Python, 4-space indent.
4. **Add tests** when adding logic. `pytest -v` must pass.
5. **No secrets, no real customer data.** Synthetic / public data only.
6. **Be kind.** See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Local dev

```bash
git clone <this-repo>
cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install   # if a .pre-commit-config.yaml is present
pytest -q
```

## Pull request checklist

- [ ] Linked issue
- [ ] Tests added / updated
- [ ] Docs updated (README in the affected project folder)
- [ ] No new secrets, no real PII
- [ ] CI green

## Reporting a security issue

Please **do not** file a public issue. Email the address in the repo
`Settings → General → Social preview / About` and we will respond.