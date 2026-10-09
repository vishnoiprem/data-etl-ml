# Technical Track — AI FDE Phase 1

> **You finish this track and you have a working AI tool on your laptop.**
> Four lessons, ~3 hours total. All code runs without an API key.

This track teaches the **engineering craft** of an AI FDE: small, shippable Python tools that solve one customer's real problem. Every lesson ends with runnable code you can demo.

---

## Lesson map

| # | Lesson | What you build | Time |
|---|---|---|---|
| 01 | [Python tooling](./technical/01-python-tooling.md) | A tiny CLI with `--help`, `python-dotenv`, type hints, packaging basics | 25 min |
| 02 | [Git for AI work](./technical/02-git-for-ai-work.md) | A scripted mini workflow: init → branch → commit → PR → `.gitignore` for secrets | 20 min |
| 03 | [Modern AI tooling](./technical/03-modern-ai-tooling.md) | A unified LLM client (OpenAI / Anthropic / mock) with retry + cost tracking | 30 min |
| 04 | [The first AI tool](./technical/04-first-ai-tool.md) | **The capstone** — a CLI that reads a customer email, looks up a shipment, drafts a reply | 45 min |

After lesson 04, you have the **first working AI tool** — Phase 1's deliverable.

---

## What "Phase 1 technical" is NOT

- It is **not** async-first. Phase 1 keeps it sync; the `hardcode/` track is where you graduate to `asyncio` + WebSockets.
- It is **not** framework-heavy. No LangChain, no LlamaIndex. Plain `openai` + `anthropic` SDKs so you understand the API.
- It is **not** production. It runs on your laptop. The `capstone-starters/` track is where you ship to real users.
- It is **not** 1000-line systems. Each file is 50-150 lines, designed to be read in one sitting.

---

## The shared scenario

Every lesson uses the PacificFreight customer. You will:

- Lesson 01: build a CLI that prints a fake shipment lookup.
- Lesson 02: commit that CLI to a fresh git repo with a proper `.gitignore`.
- Lesson 03: swap the fake lookup for a real LLM call (with a mock fallback that runs without a key).
- Lesson 04: put it all together — read an email, extract the shipment ID, look up the shipment, draft a reply.

By the end you can demo the tool to PacificFreight's ops manager in a 30-min meeting.

---

## Code conventions (Phase 1)

- Python 3.11+
- `python-dotenv` for env loading
- `argparse` for CLIs
- Type hints on every function signature
- Mock LLM fallback by default (no API key needed)
- All code in `technical/*.py` — runnable with `python3 <file>.py --help`

---

## What's next

- The **Consulting Track** — the other half of the FDE role. Build the documents that justify the code.
- **`course/practice/level-1-foundations/`** — when you want deeper architect thinking on the same topics.
- **`course/hardcode/level-1-llm-foundations/`** — when you want the 1000-line production version of lesson 04.
- **`course/capstone-starters/01-ai-doc-qa/`** — the natural Phase 2 build for PacificFreight.
