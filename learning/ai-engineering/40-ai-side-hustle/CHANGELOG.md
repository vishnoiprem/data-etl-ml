# Changelog

All notable changes to `40-ai-side-hustle` are documented here. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- `get_default_router()` now checks `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`
  before choosing a provider. Previously an installed SDK with no key
  selected the Anthropic router, and every stream failed with an
  authentication error instead of falling back to the offline stub.
- `HUSTLE_LLM_PROVIDER=stub` (documented in `.env.example`) is now honoured.
- Dashboard tests used fixed 2026-10 dates that aged out of the 14-day
  window; they now use dates relative to today.

## [0.2.0] — 2026-10-13

### Added
- `LICENSE` (MIT) — the README claimed MIT; now there's a file.
- `CHANGELOG.md` (this file) — buyers can see what changed between versions.
- `.env.example` — documents `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`
  (the SDKs read these implicitly, but the README only mentioned
  uncommenting `requirements.txt`).
- `.gitignore` — excludes `output/` (480KB of generated PDFs/HTML),
  `ledger.db` (local SQLite with the buyer's sales data), `.env`,
  and Python cache dirs. A fresh clone now starts clean.
- `docs/FIRST_DOLLAR.md` — a literal 7-day "make your first $1"
  runbook. The README's money math is the *why*; this file is the
  *do these 3 things Monday morning*.
- `docs/PRODUCT_NICHES.md` — the three niches the stub router
  already knows about (SOC2 / GDPR / AI governance) plus a
  shortlist of 7 more that the buyer can pick from. Previously
  only visible by reading `src/router.py` line by line.
- `docs/TROUBLESHOOTING.md` — the 4 most common "I ran `make demo`
  and nothing happened / it errored" failure modes, with copy-paste
  fixes.
- `tests/test_get_default_router.py` — 5 tests covering the env-var
  fallback chain (Anthropic → OpenAI → Stub). Previously untested;
  the function silently picked whatever was importable.
- `README.md` — Quick Start now shows `make help` first, points at
  the new docs, and links the env-var setup explicitly.

### Changed
- `README.md` — Quick Start reordered: `make help` → `make install`
  → `make demo`. Previously jumped straight to `make demo` and a
  buyer who hadn't `make install`'d got a `ModuleNotFoundError`.
- `Makefile` — `make help` now also prints the env-var hint at the
  bottom so a buyer who skipped the README sees it.

### Removed
- None. The codebase is unchanged; this release is metadata + docs +
  a test gap closed.

### Verified
- `make test` → 110/110 pass (was 105/105; +5 from
  `test_get_default_router.py`)
- `make demo` → produces the same 9 products in `output/`, the
  same dashboard output, no error.
- `make simulate-30d` → fills `ledger.db` with 30 days of synthetic
  sales; `make dashboard` renders the sparkline correctly.

## [0.1.0] — 2026-10-10

### Added
- Initial release. Four revenue streams (SEO content, micro-SaaS,
  digital products, print-on-demand merch), one offline `StubRouter`
  for demos, one LLM provider router (Anthropic / OpenAI), one
  SQLite revenue ledger, one dashboard with 14-day sparkline, one
  Gumroad launch-kit builder (PDF + sales page + tweet thread +
  cold email + Reddit post per product), one publish-checklist
  script, 105 unit tests.
