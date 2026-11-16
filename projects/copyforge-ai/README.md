# CopyForge AI

> **Insert high-performing copy structures into a draft — without
> rewriting the draft.** You hand it a markdown file. It reads what the
> article already has, works out what it is missing, picks the right
> direct-response framework for each gap, writes the block, and puts it
> where that framework belongs. Your prose is never touched.

This is the project that lives at `projects/copyforge-ai/`.

---

## What it is, in one sentence

A deterministic copy-insertion pipeline: the *placement* of every copy
block is decided in plain Python from a curated framework library, and a
local model is only asked to write the words — so the output is
reproducible, the tests are hermetic, and every insertion can be
explained.

---

## The design decision that matters

Most "AI copywriter" tools do one of two things. Either they hand the
whole article to a model and say *"make this better"* — in which case
the model rewrites sentences you were happy with and you have no idea
which parts it touched. Or they apply one template to every article and
call it structure.

CopyForge splits the job:

| Step | Who decides it | Why |
|---|---|---|
| What is the draft missing? | `markdown.analyze` — plain Python | A gap is a fact about the text, not an opinion |
| Which framework fills it? | `planner.plan_copy` — plain Python | Placement is the part that must be reproducible |
| What does the block say? | A local model | Writing is the part a model is good at |
| Did it help? | `scoring.score_document` — plain Python | "Better" needs to be a number |

**The model is not in the decision path.** It writes. It does not decide
what gets written, or where. That split is what makes the output
reproducible, the test suite hermetic, and every insertion auditable —
the plan records *why* each framework was chosen for each gap.

---

## The framework library

`src/copyforge_ai/frameworks.py` holds eleven curated patterns. Each one
carries a rationale, its structural slots, a worked example, the
positions where it is valid, and the gap signals it resolves.

| Framework | What it does | Where it goes |
|---|---|---|
| **PAS** — Problem–Agitate–Solve | Names the pain, twists it, hands over the fix | Opening |
| **Curiosity Gap** | Opens on an oddity the reader cannot yet explain | Opening |
| **Contrarian Open** | Disagrees with the consensus the reader already holds | Opening, after the hook |
| **BAB** — Before–After–Bridge | Shows the before, shows the after, names the mechanism | Body |
| **Social Proof** | Borrows credibility from someone the reader already trusts | Body |
| **Objection Sandwich** | Surfaces the strongest counter-argument and answers it | Late body |
| **So-What Bridge** | Turns an abstraction into an action | Body |
| **Problem Agitation List** | Turns a vague worry into a countable list | Body |
| **Concrete Example** | Replaces an abstraction with one real instance | Body |
| **Call to Action** | Asks for one specific, easy next action | Before the close |
| **Closing Question** | Ends on a question the reader cannot answer "yes" to | Close |

Each position in the article has its own slot — `body_example`,
`body_bridge`, `body_action`, `body_proof`, `body_list` — so the body
can carry a concrete example *and* a before/after bridge *and* a so-what
without them collapsing into one slot and starving the article of
structure.

---

## The pipeline

```
  draft.md
     │
     ▼
  ┌─────────────────┐   what copy structures are missing?
  │  markdown       │   → a list of gap signals
  │  .analyze       │
  └────────┬────────┘
           ▼
  ┌─────────────────┐   which framework fills which gap, and where?
  │  planner        │   → an ordered, explained plan
  │  .plan_copy     │
  └────────┬────────┘
           ▼
  ┌─────────────────┐   the words, from a local model
  │  llm            │   (or the deterministic stub)
  │  .complete      │
  └────────┬────────┘
           ▼
  ┌─────────────────┐   splice the blocks in, marked
  │  writer         │   <!-- copyforge:framework -->
  │  .write_article │
  └────────┬────────┘
           ▼
  ┌─────────────────┐   the same rubric, before and after
  │  scoring        │   → 47.5 → 62.5
  │  .score_document│
  └─────────────────┘
```

---

## How to run

```bash
cd projects/copyforge-ai

make up       # install dependencies into the shared venv
make test     # 161 tests, offline: no API key, no network, no Ollama
make demo     # the offline end-to-end story
make eval     # rubric improvement, idempotence, author-text preservation
make lint     # ruff check src/ tests/ scripts/
```

### On a single draft

```bash
# See what the planner decided, and why, without writing anything
python scripts/write_article.py draft.md --dry-run

# Write the result to a new file
python scripts/write_article.py draft.md -o formatted.md

# Rewrite the draft in place
python scripts/write_article.py draft.md --in-place

# Use a local Ollama model instead of the deterministic stub
python scripts/write_article.py draft.md --provider ollama
```

### With a local model

```bash
# 1. Pull a model (any instruct model works)
ollama pull qwen2.5:7b-instruct

# 2. Point CopyForge at it
export COPYFORGE_LLM_PROVIDER=ollama
export COPYFORGE_OLLAMA_MODEL=qwen2.5:7b-instruct
export COPYFORGE_OLLAMA_HOST=http://localhost:11434

python scripts/write_article.py draft.md --in-place
```

If the server is not reachable, CopyForge falls back to the deterministic
stub. It never fails a run because a model was down.

---

## What the output looks like

Input — a real draft, deliberately weak:

```markdown
# Scaling Data Pipelines Without Breaking Them

In today's fast-paced world, data teams are under increasing pressure to
scale their pipelines. This article will explore the topic of pipeline
reliability and what you can do about it.

## The Challenge

Data pipelines can be difficult to maintain. There are many moving parts,
and things go wrong. It is important to note that reliability matters.
...
```

Output — the author's text **verbatim**, with copy blocks inserted and
marked:

```markdown
# Scaling Data Pipelines Without Breaking Them

In today's fast-paced world, data teams are under increasing pressure to
scale their pipelines. This article will explore the topic of pipeline
reliability and what you can do about it.

<!-- copyforge:curiosity_gap-->

Two teams run the same pipeline on the same 4 TB of data. One of them
finishes in 9 minutes. The other takes 3 hours. The difference is one
setting nobody wrote down.

## The Challenge

Data pipelines can be difficult to maintain. There are many moving parts,
and things go wrong. It is important to note that reliability matters.

<!-- copyforge:bab-->

Today it is manual: a checklist, a spreadsheet, and a quarterly cleanup
that nobody looks forward to.
...
```

The markers are the point. They say exactly which framework produced each
block, which means:

* a second run adds nothing (the pipeline is idempotent by marker);
* an editor can see at a glance what was inserted and why;
* the eval harness can measure framework coverage without guessing.

---

## The rubric

`scoring.py` scores an article out of 100 across eleven criteria. Every
criterion is checkable from the text alone — no model judges it, and no
human has to disagree about it.

| Criterion | Points | What it checks |
|---|---|---|
| Hook present | 10 | The article opens with prose |
| Hook specific | 15 | The opening names something concrete — a number, a quantity |
| Problem established | 10 | The reader's problem is named early |
| Framework coverage | 15 | The copy structures a strong piece has are present |
| Proof present | 10 | At least one passage offers evidence, not assertion |
| Objection addressed | 5 | The strongest counter-argument is surfaced and answered |
| Actionable step | 10 | The reader is told something they can do |
| CTA present | 10 | There is a call to action |
| Closing question | 5 | The article ends on a question |
| Readability | 5 | No paragraph is a wall of text |
| No AI filler | 5 | No machine-filler phrases |

This is a **structural** score, not a taste score, and that is a
deliberate limit. The rubric can tell you the article has no hook. It
cannot tell you the hook is *good* — the first is a fact, the second is
a conversation, and a tool that pretended otherwise would be lying.

The interesting number is not "62/100". It is **47.5 → 62.5**: what the
insertion bought.

---

## Measured results

From `make eval` over the three sample drafts in `data/`:

```
[ok ] rrk_15yr_draft.md              38.8 →   53.8 (+15.0)  8 frameworks
[ok ] sample_draft.md                47.5 →   62.5 (+15.0)  7 frameworks
[ok ] sample_draft_2.md              40.0 →   55.0 (+15.0)  8 frameworks

  mean score delta: +15.00
  mean coverage:    7.67 frameworks
  idempotent:       100%
  author text kept: 100%

Acceptance: PASS
```

The four gates:

| Gate | Threshold | Why it exists |
|---|---|---|
| `min_mean_score_delta` | 5.0 | The insertion has to actually improve the article |
| `min_idempotent_drafts` | 1.0 | A writer that keeps adding copy is not a writer |
| `min_preserved_paragraphs` | 1.0 | The author's prose must survive untouched |
| `min_coverage` | 2.0 | At least two copy structures per article |

---

## Four properties worth calling out

### 1. The author's prose is never rewritten

CopyForge *inserts*. Every original paragraph, heading, list and code
block comes through byte-for-byte — the parser keeps each block's source
text and the writer copies it through. The eval harness asserts this on
every run, because a tool that quietly rewrites your draft is a tool you
cannot trust.

### 2. The pipeline is idempotent

Run it twice, get the same article. This is enforced by the markers: the
analyzer excludes CopyForge's own blocks from gap detection, and credits
a gap as closed when an already-inserted framework resolves it.

Getting this right took three attempts, and each failure was instructive:

* **First attempt:** the analyzer saw the inserted block as *evidence the
  gap was still open*, so the second run inserted a second copy. Fixed by
  excluding inserted blocks from gap detection.
* **Second attempt:** excluding them entirely re-opened the gaps the
  blocks had just filled. Fixed by crediting a gap as closed when an
  inserted framework resolves it — the credit is *derived* from the
  library, not guessed.
* **Third attempt:** one shared `middle` slot meant two body gaps
  competed for one position, one went unfilled, and the next run tried
  to fill it. Fixed by giving each body framework its own position.

### 3. The specificity check matches on word boundaries

The scorer asks "does this hook name something concrete?" by counting
specificity markers — `%`, `4`, `minutes`, `GB`, `Q3`. The first
implementation matched them as substrings, and *"Data **teams** are
under increasing pressure to scale their **pipe**lines"* scored as
highly specific, because "teams" contains "ms" and "pipelines" contains
"lines".

That is exactly the sentence this check exists to catch, so the
substring match was worse than no check at all. The markers are now
matched on word boundaries.

### 4. Blocks are written about the title, not the opening sentence

The first version of the stub took its topic from the article's opening
sentence. That is the author's framing of the *situation*, not the
subject of the piece — so for a draft opening *"Data engineering has
changed a lot over fifteen years"*, the Concrete Example block's example
was that very sentence, and the BAB block's "before" was a checklist and
a spreadsheet that the article never mentioned.

Structurally valid, semantically empty. The prompt now carries the
article's title explicitly, and the title is reduced to a noun phrase
before it is threaded through the slots: *"Fifteen Years of Data
Engineering: What Actually Scales"* becomes *"Data Engineering"*.

This matters most for the stub, but it is not stub-specific — a real
model given the same context reaches for the same wrong sentence.

---

## When this is the right pattern

This is the right call when:

- You have a draft that is **structurally sound but flat** — the ideas
  are right, the hook is generic, and there is no call to action.
- You want **the same structural standard every time**, not a different
  shape each run.
- You need to know **exactly what was inserted** and why, for an editor
  to review or undo.
- You are **offline or privacy-constrained** and want local models, or
  no model at all.

It is **not** the right call when:

- You want a full rewrite from a one-line brief. This tool inserts into
  a draft; it does not generate one.
- You want **SEO content at volume**. The rubric scores structure, and
  structure is not the bottleneck when you have a thousand drafts.
- You want **a model to judge quality**. The scorer is structural by
  design. Judging whether the prose is *good* is a different problem,
  and a different tool.

---

## What this project is NOT

- **Not a copy generator.** It does not write articles. It inserts
  structures into an article you wrote.
- **Not an LLM-in-the-decision-path system.** The model writes. It does
  not decide. Every tool that claims to "use AI to improve your copy"
  without telling you *which part* is the model is hiding something.
- **Not a measurement of the top 1%.** Nobody has published the
  distribution of top-decile articles, and "top 1%" is not a
  measurable claim. The library encodes the *documented, well-worn*
  frameworks — PAS, BAB, the objection sandwich — not a percentile
  somebody made up.
- **Not a replacement for an editor.** The rubric can tell you the
  article has no hook. Whether the hook is good is a human judgement,
  and this project does not pretend to have made it.

---

## File layout

```
projects/copyforge-ai/
├── README.md                    ← this file
├── Makefile                     ← up / test / demo / eval / lint
├── pytest.ini
├── conftest.py                  ← makes src/ importable from any cwd
├── requirements.txt             ← httpx, pydantic, pytest, ruff. No model dependency.
├── data/
│   ├── sample_draft.md          ← a deliberately weak draft
│   ├── sample_draft_2.md
│   └── rrk_15yr_draft.md        ← a career-history draft (used for the eval)
├── output/                      ← generated articles (git-ignored)
├── reports/
│   └── copyforge_report.json    ← written by the demo
├── scripts/
│   ├── write_article.py         ← the CLI
│   └── run_demo.py              ← the offline end-to-end demo
├── src/copyforge_ai/
│   ├── __init__.py
│   ├── config.py                ← settings, read from the environment
│   ├── frameworks.py            ← THE LIBRARY: 11 frameworks, slots, examples
│   ├── markdown.py              ← parser + structural analysis + gap detection
│   ├── planner.py               ← gap → framework → position, with reasons
│   ├── llm.py                   ← LLMRouter / StubRouter / OllamaRouter
│   ├── writer.py                ← generation + splicing + the markers
│   ├── scoring.py               ← the 100-point rubric
│   └── evaluation.py            ← the eval harness and its gates
└── tests/                       ← 167 tests, hermetic
```

---

## Configuration

| Variable | Default | What it does |
|---|---|---|
| `COPYFORGE_LLM_PROVIDER` | `stub` | `stub` or `ollama` |
| `COPYFORGE_OLLAMA_MODEL` | `qwen2.5:7b-instruct` | The local model |
| `COPYFORGE_OLLAMA_HOST` | `http://localhost:11434` | Where Ollama is |
| `COPYFORGE_TARGET_WORDS` | `1200` | The target article length |
| `COPYFORGE_MIN_SCORE_DELTA` | `5.0` | The eval gate for improvement |

The provider is read from the environment **first**, and the provider is
matched explicitly. CopyForge never constructs a client and waits for it
to fail — the failure would land on the first article rather than at
startup.

---

## Dependency note

There is no embedding model here, deliberately. CopyForge matches draft
sections to frameworks by **structure**, not by meaning — the decision of
where a PAS block belongs is made in plain Python and is testable without
a 2 GB dependency. The model dependency is `httpx` (to talk to Ollama),
and that is optional: the deterministic stub needs nothing at all.

This is the same split the sibling `tech-trend-radar` project makes, for
the same reason: a model in the decision path makes the decisions
unauditable, and an unauditable decision is not worth making.

---

## CI

`.github/workflows/copyforge-ai-ci.yml` runs the suite, the eval
harness, the demo smoke test and ruff on every PR that touches this
project. No API key, no network, no Ollama, no Docker.

---

*Last updated: 2026-11-16 · License: MIT*
