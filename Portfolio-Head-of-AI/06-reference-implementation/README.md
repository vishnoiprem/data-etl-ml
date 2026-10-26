# Reference Implementation

The flagship this document describes is one decision expressed in
many chapter-shaped ways. There is exactly one implementation of
that decision, and it lives outside this folder.

```
Portfolio-Head-of-AI/         ← this folder, narrative
agentic-ai/19-mlops-finetune-genai/   ← the codebase
```

Everything in
`../01-problem-and-constraints/`,
`../02-data-and-eval/`,
`../03-system-architecture/`,
`../04-delivery/`, and
`../05-ops-and-organization/` is
narrative: a way of saying what the system is for, what it cost, and
what breaks when. The codebase is the system itself.

## What the codebase has that the narrative doesn't

- Working `Makefile` with `make up`, `make test`, `make smoke`,
  `make train`, `make serve`, `make monitor`, `make clean` targets.
- A `tests/` directory with 67 passing tests, including the
  end-to-end smoke that trains 1 step on 8 samples and serves a
  request on a 200 OK.
- A `scripts/` directory with `bootstrap.sh`, `run_pipeline.sh`,
  and `ablation_table.py` — one-shot automation that doesn't lie.
- A `infra/` directory with `docker-compose.yml`, two `Dockerfile`s,
  Prometheus + Grafana YAML, and provisioned Grafana dashboards.
- Synthetic mode (`--synthetic`, `HAVE_PEFT` guard) so the codebase
  runs on a machine without a GPU. CI as a contract, not an
  aspiration.

## What the narrative has that the codebase doesn't

None of the chapter-shaped documents is implemented as a workbook
that produces the chapter. The narrative hand-waves things the
codebase can't — and the codebase implements things the narrative
skips. The reason both are kept is that:

| Concern | Narrative | Codebase |
|---|---|---|
| **Why** | ✓ | – |
| **Who owns it** | ✓ | – |
| **What we kill if it fails** | ✓ | – |
| **What good looks like** | ✓ | partial |
| **How it's wired** | partial | ✓ |
| **What it costs to run** | ✓ | – |
| **What to do when it breaks** | ✓ | partial |

Each row is the chapter the other side doesn't fill in. Read together
they produce a defensible artifact; read either alone they produce
a partial program.

## The point of this folder

A common misread of "reference implementation" is "it's the
production version." The reference implementation is not the
production version of a fine-tuned assistant for a 200-person
company. It is the *machinery*: dataset pipeline, eval harness,
serving surface, monitoring spine. A real production deployment
swaps in real data, real eval sets, real GPU hosts, real auth, and
real secrets. The machinery is the same; the inputs are different.

This is the same point the
[`build-vs-buy-decision.md`](../01-problem-and-constraints/build-vs-buy-decision.md)
makes about Path A vs. Path C: the *machinery* is the thing that
matters first, because the machinery is what's reusable across
initiatives. The model is downstream.

## When this folder graduates

A reader who wants to evaluate the work as a Head-of-AI candidate
should walk through:

1. [`../README.md`](../README.md) — the 15-minute path.
2. The two files that take 30 minutes to read together:
   `../01-problem-and-constraints/build-vs-buy-decision.md` and
   `../01-problem-and-constraints/success-metrics.md`. These are
   the judgment.
3. The incident postmortem in
   `../05-ops-and-organization/incident-postmortem.md`. The
   shape of failure.
4. The codebase's `README.md` at
   `../../agentic-ai/19-mlops-finetune-genai/README.md`. The
   shape of the system.

That's it. Everything else is reference — useful when the question
narrows, but not necessary for the headline read.

## The one-sentence summary

I make explicit decisions, with named gates and named kills, in code
that's wired into the same metrics the business runs on, and I
document the choices so a reviewer two quarters later can audit
them. This document is the rules; the codebase is the proof.