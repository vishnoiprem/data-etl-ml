# 🎬 Demos

> A 30-second clip does more than 30 pages of README. This file is the **checklist**
> for the five demos the root README points to.

| # | Project | What you'll see | Format | Status |
|---|---|---|---|---|
| 1 | **SCB AML — Lucid Search** | Type a watchlisted name, get fuzzy matches across 750+ tables | GIF / screen-cast | ⬜ place `docs/assets/scb-aml-lucid-demo.gif` |
| 2 | **Realtime Stock Pipeline** | Tick → Kafka → Flink window → Postgres → Grafana refresh | GIF | ⬜ place `docs/assets/realtime-stock-demo.gif` |
| 3 | **Flink CDC Dashboard** | Postgres update → Flink SQL → live chart | GIF | ⬜ place `docs/assets/flink-cdc-demo.gif` |
| 4 | **Enterprise RAG Platform** | Question → hybrid retrieval → Bedrock answer with citations | GIF / Loom | ⬜ place `docs/assets/enterprise-rag-demo.gif` |
| 5 | **Multi-Agent Platform** | Goal → planner → tool call → final answer | GIF / Loom | ⬜ place `docs/assets/multi-agent-demo.gif` |

> **Legend:** ⬜ = placeholder. ⏳ = recorded, needs edit. ✅ = published.

## Why this file exists

Three audiences benefit from demos in this exact order:

1. **Recruiters** — they skim a repo for ~30 seconds and decide to keep reading.
   A live demo says more than any README.
2. **Engineers evaluating the repo** — they want to see *the system working*,
   not code that might work.
3. **Search engines** — every GIF / Loom embed's alt text is keywordable.
   Embedding real keywords here compounds the SEO value of the README.

## How to record each demo (≤60 sec, ≤5 MB)

### 1. SCB AML — Lucid Search
```bash
cd data-engineering/scb_aml_platform
python run_demo.py                       # interactive
# OR
uvicorn lucid_search.api.app:app --reload  # then visit /docs
```
Screen-cast: type a name like `Mohammed Al-Rahman`, show fuzzy match,
click through to entity profile, show network graph.
Save as `docs/assets/scb-aml-lucid-demo.gif`.

### 2. Realtime Stock Pipeline
```bash
cd realtime-stock-pipeline
docker compose up -d
# wait ~30s; open the Grafana dashboard
```
Screen-cast: producer emits ticks, Flink windows aggregate, dashboard updates.
Save as `docs/assets/realtime-stock-demo.gif`.

### 3. Flink CDC Dashboard
```bash
cd flink-cdc-dashboard
bash 0_setup_project.sh
bash 1_start_containers.sh
bash 2_setup_cdc.sh
bash 3_run_flink_sql.sh
bash 4_run_data_generator.sh
bash "5_run_dashboard.sh"
```
Screen-cast: insert a row in Postgres → Flink SQL propagates → dashboard chart moves.
Save as `docs/assets/flink-cdc-demo.gif`.

### 4. Enterprise RAG Platform
```bash
cd ai-engineering/01-enterprise-rag-platform
make up         # starts the API + vector store
make eval       # runs RAGAS eval
# open the API at /docs and ask a real question
```
Screen-cast: ask a question over a real corpus, show hybrid retrieval + rerank
+ grounded answer with citations.
Save as `docs/assets/enterprise-rag-demo.gif` (or upload to Loom).

### 5. Multi-Agent Platform
```bash
cd ai-engineering/03-multi-agent-platform
make demo
```
Screen-cast: define a goal, watch the planner → tool-call → synthesis loop.
Save as `docs/assets/multi-agent-demo.gif` (or upload to Loom).

## Recording tips

- Trim every silence. ≤60 sec, no setup narration.
- Show the system doing the *interesting thing*, not your shell prompt.
- 1280×720 at 12-15 fps keeps GIFs under 5 MB.
- For Loom / YouTube, drop a thumbnail in `docs/assets/` and embed the link
  in this file so the README stays light.

## Embedding in the README

Once recorded, link the demo in two places so it's discoverable:

```markdown
<!-- in the matching section of README.md -->
![Realtime stock pipeline — tick to dashboard in 800ms](docs/assets/realtime-stock-demo.gif)
```

For external video, use the thumbnail pattern so the README stays light:

```markdown
[![Watch the demo](docs/assets/realtime-stock-thumb.png)](https://www.loom.com/share/XXXX)
```

## Update flow

After adding a demo:

1. Drop the file in `docs/assets/`.
2. Edit this file: move the row from ⬜ → ✅, set the asset path.
3. Optionally embed the demo in the matching section of the root README.
4. Commit with message like: `docs(demos): add realtime-stock demo gif`.

## Asset file conventions

| Use | Filename |
|---|---|
| Demo GIF / screen-cast | `<project>-<thing>-demo.gif` |
| Static screenshot | `<project>-<thing>.png` |
| Architecture diagram | `<project>-architecture.png` |
| Loom / YouTube thumbnail | `<project>-thumb.png` |

All under `docs/assets/`. See `docs/assets/README.md` for full conventions.