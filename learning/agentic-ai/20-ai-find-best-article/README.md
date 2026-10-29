# SignalScribe — "How to Pick the Best Article"

A complete research → draft → review pipeline for one long-form article about **evaluating and selecting the best article, tool, paper, model, or prompt for a given job**, aimed at AI, data engineering, ML, and agentic systems practitioners.

**Platform:** LinkedIn / Medium
**Target length:** 1,000–1,800 words
**Status:** ⚠️ **NOT PUBLISHABLE.** Requires human authorship sign-off. See [Publication gate](#publication-gate).

---

## What this project is

Most AI-tool content ranks tools. This project argues something different: **"best" is not a property of an artifact. It is a property of a specific job, under specific constraints, judged by someone who can detect the failures that matter.** Selection is a procedure you run, not a ranking you read.

The pipeline produces that article three times over — 100 distinct drafts, one selected candidate, and 100 structured reviews of it — with a strict evidence and disclosure standard at every step.

---

## Pipeline

```
  Phase 1                Phase 2              Phase 3                Phase 4
┌───────────┐         ┌───────────┐        ┌───────────┐         ┌───────────┐
│ Research  │────────▶│ 100 drafts│───────▶│article.md │────────▶│  Memory   │
│ + rubric  │         │distinct   │ select │ + 100     │         │  system   │
│ + voice   │         │ angles    │ best   │   reviews │         │           │
└───────────┘         └───────────┘        └───────────┘         └───────────┘
      ▲                       │                   │                     │
      └─────── sources.md ────┴───────────────────┘                     │
                                                                 persistent
                                                                 across sessions
```

**Phase 1 — Scaffolding and research.** `rubric.md` defines a 100-point scoring system with eight hard-fail checks. `voice-guide.md` defines the editorial voice. `research/notes.md` and `sources.md` capture what each source actually says — with exact numbers, what each source does *not* support, and peer-review status. `outline.md` fixes the article's skeleton. `article-template.md` fixes the front-matter contract.

**Phase 2 — 100 drafts.** Each draft is a genuinely different article: different title, hook, thesis wording, section order, organizing device, decision-framework shape, and examples. They are not rewrites of each other. Each carries a self-assessed `rubric_score`, a `hard_fail` flag, and a `distinctness_angle` line in front matter.

**Phase 3 — 100 reviews.** The strongest draft is copied to `article.md`. Then 100 review passes are run against it. Each pass has its own analytical focus (hook, voice, thesis, evidence, structure, technical depth, practical utility, ethics, title, subtitle, tags, readability, SEO, distribution, publication readiness, citation density, factual verification, counterargument handling, scannability, audience fit, opening line, closing question, headings, transitions, list quality, concreteness, jargon density, and a final full audit). Early passes diagnose; later passes converge.

**Phase 4 — Memory.** Project, user, and feedback memories are written to `.puku-cli/agent-memory/article-review-generator/` so future sessions inherit the disclosure rules and working preferences.

---

## File inventory

| Path | What it is |
|---|---|
| `README.md` | This file. |
| `rubric.md` | 100-point editorial rubric, 8 hard-fail checks, banned-phrase list. |
| `voice-guide.md` | LinkedIn/Medium voice rules with five worked before/after examples. |
| `outline.md` | Canonical article skeleton all drafts follow. |
| `article-template.md` | Structural template with front-matter contract. |
| `sources.md` | Deduplicated source list; URL → claim mapping; access date 2026-10-26. |
| `research/notes.md` | Source-by-source research notes: what each source supports, what it does not, and cross-source synthesis. |
| `draft-001.md` … `draft-100.md` | 100 distinct drafts. |
| `article.md` | The selected best candidate — the review target. |
| `review-001.md` … `review-100.md` | 100 review passes against `article.md`. |
| `.puku-cli/agent-memory/article-review-generator/` | Persistent memory: `project_*.md`, `user_*.md`, `feedback_*.md`, `MEMORY.md` index. |

---

## How to use the reviews

The reviews are a **progression, not 100 opinions**. Open them in order.

- **`review-001.md` through `review-020.md` — Diagnostic.** Each isolates one dimension and records the score for it. Use these to build the list of everything wrong with the draft.
- **`review-021.md` through `review-070.md` — Convergent.** The focus shifts toward cross-cutting defects: citation density, factual verification, counterargument handling, scannability, jargon density, list quality. These passes cross-reference earlier findings and start proposing concrete replacement language.
- **`review-071.md` through `review-100.md` — Converging audit.** Publication readiness, distribution, audience fit, and the final full audit. By pass 100 the review should describe a specific final state of the piece.

**Each review file contains:**
1. Pass number and analytical focus.
2. A "what changed since review N-1" note at the top, so the sequence demonstrably progresses.
3. Every rubric criterion scored individually with points, the total out of 100, PASS/FAIL status.
4. Hard-fail findings, if any.
5. Evidence and citation problems — which claims lack support, which URLs are weak or unverified.
6. Specific fixes at section and line level.
7. A concise revised-outline suggestion at the end.

**Reading pattern for a human editor:** read reviews 1, 20, 50, 75, and 100 first to get the arc, then read any pass whose focus matches the part of the article you are working on.

---

## Evidence and disclosure rules (binding on every artifact here)

1. **No fabricated facts.** Every statistic, benchmark number, quote, and URL traces to `research/notes.md` and `sources.md`. Anything traced to S17 or S18 carries an inline `[UNVERIFIED]` marker.
2. **No invented first-person claims.** The only permitted form of personal material is a literal `[AUTHOR EXPERIENCE: ...]` placeholder. This is a hard rule from the system spec.
3. **No banned phrases.** The list in `rubric.md` applies to every file this project writes, including the reviews.
4. **No auto-publication.** The pipeline routes the best candidate to human review. It never publishes.

---

## Publication gate

> ### ⚠️ This article is not publishable yet.
>
> It requires **human authorship sign-off**. Specifically:
>
> 1. **Every `[AUTHOR EXPERIENCE: ...]` placeholder must be replaced** with the author's real firsthand account, or the surrounding sentence must be rewritten so the article stands without it. The placeholders are intentional seams, not placeholders to delete.
> 2. **A human must verify the factual claims** — open each URL in the source list, confirm the number, and confirm the source supports the sentence attached to it. The pipeline's checks are automated; they are not a substitute for a reader who is accountable.
> 3. **A human must own the disclosure** and confirm it matches what actually happened in producing the piece.
>
> Until all three are done, the file is a draft with a review trail — not a post.

---

## Re-running the pipeline

The project is plain Markdown; there is no build step. To work with it:

```bash
# read the article under review
open article.md

# compare the best candidate against its source draft
diff article.md draft-0NN.md

# find a specific review's focus
grep -l "ANALYTICAL FOCUS" review-*.md | head

# check a draft's self-score and angle
head -20 draft-0NN.md
```

---

## Source and research provenance

Sixteen sources were fetched and verified on **2026-10-26**, plus two that could not be verified (`[UNVERIFIED]`). Peer-reviewed: S1 (NeurIPS 2023), S3 (TACL 2023), S4 (AAAI 2024), S10 (ACL 2022), S11 (ICLR 2023). The rest are arXiv preprints, including several from 2026. The article says so.

`research/notes.md` also records the sources that were **rejected** and why — vendor blogs, SEO content, aggregators, and preprints that could not be opened. If a claim appears in no source, it does not appear in a draft.
