# Dataset Design

The build-vs-buy decision in
`../01-problem-and-constraints/build-vs-buy-decision.md` recommends
Path A (retrieval + prompt engineering) *first*. If we ever get to
Path C, the fine-tune's quality ceiling is set before a single
gradient step runs — by this document.

## The three datasets, and why there are three

People conflate "the training data." There are three distinct
artifacts with three distinct lifecycles, and mixing them up is the
most common way a fine-tune gets a headline number that doesn't
survive contact with production:

| Dataset | Size | Refreshed | Who grades it | What breaks if you skip it |
|---|---|---|---|---|
| **Train** | ~30k rows | Quarterly | Upstream curation (thumbs up/down) | Nothing breaks — you just get a weaker model and don't know why |
| **Eval (dev)** | ~500 rows | Monthly | Human raters, 3-point scale | You can't tell a real improvement from noise |
| **Eval (holdout, never trained on)** | ~200 rows | Quarterly | Human raters + compliance | You ship a model that memorized the eval |

The eval sets are the expensive part. A 500-row human-rated eval set
is roughly 40–60 hours of rater time. **That is the artifact.** The
training data is replaceable; the eval set is not.

## The reference implementation runs on a public dataset

The working pipeline (`agentic-ai/19-mlops-finetune-genai/`) uses
`mlabonne/FineTome-100k` from HuggingFace — a public, permissively
licensed instruction dataset. That choice is deliberate for a
*reference* artifact:

- **No consent problem.** The provenance constraint from
  `../01-problem-and-constraints/constraints.md` (§2 Data) is real:
  customer ticket data usually cannot legally be used for
  fine-tuning without a consent review. A public dataset sidesteps
  the question entirely, which means the pipeline is demonstrable
  without a legal team.
- **The pipeline is the deliverable, not the corpus.** Swapping
  `FineTome-100k` for a proprietary corpus is a config change in
  `agent/dataset.py`, not a rewrite. If the artifact can't survive
  that swap, it's a demo.

**This is explicitly not what a production run would use.** See
"What I'd change for production" below.

## Filters, in the order I apply them

Order matters. Cheap-and-destructive first, expensive-and-subtle last.

1. **Drop `thumbs_down == 0` rows.** `FineTome-100k` ships an
   upstream quality signal. ~30% of rows drop here.
2. **Deduplicate by SHA-256 of the templated text.** Not by the
   prompt alone — templated text, because two prompts that produce
   the same completion are the same training signal.
3. **Length filter: drop rows over 2048 tokens *after* templating.**
   Filtering pre-templating is a classic bug — the Llama 3.1
   template adds ~40 tokens of role scaffolding, so a 2,000-token
   row can template to 2,060 and get silently dropped by a downstream
   `max_length` truncation instead of by your filter. Different
   failure, same symptom.
4. **Leakage filter against the held-out eval prompts.** Any training
   row whose templated text has Jaccard similarity ≥0.7 with any
   held-out eval prompt is dropped.

### Why the leakage filter exists at all

Without it, the headline number is unfalsifiable. If a training row
and an eval prompt are near-duplicates, the model gets the eval
score for free — and you cannot distinguish "the fine-tune worked"
from "the fine-tune memorized."

`agent/dataset.py` implements this as an explicit filter with the
threshold in config, not as a comment saying "don't do this." It's a
line of code, so it's reviewable, and it runs on every training
invocation. The test suite (`tests/test_dataset.py`) asserts the
filter actually fires.

## Synthetic mode is a contract, not a fallback

`agent/dataset.py` takes a `--synthetic` flag that swaps the HF
dataset for an 8-row in-repo JSONL. This exists so:

- `make test` passes on a laptop with no GPU, no `HUGGINGFACE_TOKEN`,
  and no network.
- A new engineer can run the whole pipeline once and understand what
  each stage does before they earn the right to run the real one.

The constraint from `../01-problem-and-constraints/constraints.md`
(§5 People) applies: the learning curve is 3–6 months. A pipeline
that only runs with the full stack present extends that curve. One
that runs in synthetic mode in 90 seconds does not.

**The guard against synthetic mode becoming the default:** the
synthetic path sets `is_synthetic=True` in the run's MLflow params,
and `scripts/ablation_table.py` refuses to render a table row for a
synthetic run. You can produce a synthetic run; you cannot launder it
into the headline table.

## What I'd change for production

If this were a real Path C run against the ticket-classification
workload:

| Change | Why | Cost |
|---|---|---|
| Source = curated ticket corpus, not FineTome-100k | Domain match is the whole point of the fine-tune | 3+ months legal + curation |
| Split by *time*, not by row | A random split leaks. Jul tickets must not appear in train if eval is measured on Jul tickets | Free, but must be decided before the split exists |
| Add an explicit `intent_id` column | Lets me report per-category scores, not one blended number | 1 week |
| Human-rewrite ~2k of the highest-frequency intents | Fine-tuning on raw drafts teaches the model to be sloppy | 80 hrs |
| Hold out entire *intents*, not individual tickets | Otherwise near-duplicate tickets straddle the split | 1 week |

The last two are the ones teams skip. Per-category reporting is what
turns "accuracy went up 3 points" into "billing intents got worse and
that's the 3 points."

## The rule I hold

> If you cannot name the exact rows that will be your eval set, you
> do not have a dataset plan. You have a data source.

`FineTome-100k` is a data source. The 200-row holdout is a dataset.
Only one of those two is an asset.