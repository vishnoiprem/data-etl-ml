# Portfolio — Head of AI Flagship

**This folder is a job-interview artifact, not a project portfolio.** It exists so an
interviewer at Head-of-AI / Director-of-AI / VP-of-AI level can read one
self-contained set of documents and learn my *judgment*: what I'd build, why,
what I'd kill, and what happens when things go wrong.

The code that proves those judgments live in `agentic-ai/19-mlops-finetune-genai/`
and is referenced throughout. This folder is the reasoning on top of the code.

## How to read this

If you're an interviewer with **15 minutes**, read in this order:

1. [`01-problem-and-constraints/build-vs-buy-decision.md`](./01-problem-and-constraints/build-vs-buy-decision.md) — my judgment on what to build vs. buy.
2. [`01-problem-and-constraints/success-metrics.md`](./01-problem-and-constraints/success-metrics.md) — what "good" looks like, with numbers.
3. [`05-ops-and-organization/incident-postmortem.md`](./05-ops-and-organization/incident-postmortem.md) — the failure I caused and what it taught me.
4. [`05-ops-and-organization/org-design.md`](./05-ops-and-organization/org-design.md) — what I'd build as a leader.

If you have **another hour**, read 2, 3, 4, 5, 6 in order.

If you have **another week**, run the code under
[`06-reference-implementation/`](./06-reference-implementation/) and read
`agentic-ai/19-mlops-finetune-genai/README.md` — that's the working system this
narrative is built on.

## What this artifact deliberately is NOT

- **Not a project tour.** The repo has 80+ projects; they're evidence of
  range, not the point. The point here is the reasoning.
- **Not a pitch.** I don't know your company, your industry, or your
  constraints. I'm trying to show how I think, not pitch a solution.
- **Not aspirational.** Everything here is something I would actually do.
  If a section reads as "what a Head of AI *should* write," that's the bug,
  not the feature.

## The flagship

The flagship I document here is **MLOps fine-tuning of a production GenAI
assistant**, scoped small enough to be fully read in an evening and
executed end-to-end on a single GPU. The reference implementation is
`agentic-ai/19-mlops-finetune-genai/`. The chapters describe the *judgment*
behind a system like that one — what to build, in what order, what to
measure, who does what, and what fails.

## Contributing

I treat this folder the way I'd treat internal leadership docs: I will
revise sections when the reasoning doesn't hold up against a specific
interview pushback. If you spot a section where the logic is circular or
the numbers don't agree with the conclusions, point at it — that's the
most useful feedback I can ask for.
