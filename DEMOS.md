# 🎬 Demos

Short, public, no-sign-in demos. Each is one clip / screen-cast (≤60 sec) so a
newcomer can see the system actually working.

| # | Project | What you'll see | Format | Status |
|---|---|---|---|---|
| 1 | **SCB AML Platform** — Lucid Search | Type a watchlisted name, get fuzzy matches across 750+ tables | GIF / screen-cast | ⬜ place `docs/assets/scb-aml-lucid-demo.gif` |
| 2 | **Realtime Stock Pipeline** | Tick → Kafka → Flink window → Postgres → dashboard refresh | GIF |
| 3 | **Flink CDC Dashboard** | Postgres update → Flink SQL → live chart | GIF |
| 4 | **Enterprise RAG Platform** | Question → hybrid retrieval → Bedrock answer w/ citations | GIF / Loom |
| 5 | **Multi-Agent Platform** | Goal → planner → tool calls → final answer | GIF / Loom |

> **Legend:** ⬜ = placeholder. ⏳ = recorded, needs edit. ✅ = published.

## How to add a demo

1. Record **60 sec** max. Trim silence. Show the system doing the interesting
   thing, not your shell prompt.
2. Export to GIF (≤5 MB) or upload to Loom / Vimeo and link it here.
3. Drop the file in `docs/assets/` with the convention `<project>-<thing>-demo.gif`.
4. Edit this file: move the row from ⬜ to ✅ and add the asset path / link.

## Embedding in READMEs

```markdown
![Realtime stock pipeline — tick to dashboard in 800ms](docs/assets/realtime-stock-demo.gif)
```

For Loom / YouTube, use a thumbnail link so the README stays light:

```markdown
[![Watch the demo](docs/assets/realtime-stock-thumb.png)](https://www.loom.com/share/XXXX)
```

## Why this is worth doing

- **Recruiters** skim a repo for ~30 seconds. A 30-sec clip says more than 30
  pages of README.
- **Search engines** index video thumbnails and alt-text. Every alt-text on an
  embed is a keyword opportunity.
- **Other contributors** see what the system is *for* in 5 seconds and can
  decide whether to engage.