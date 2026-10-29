# 8.6 — Template vs Custom Code

> **Section 8 · Production Operations · Lecture 8.6 · 6:30**

## 🎯 What you will learn

- The genuine decision behind "template or custom code", and why the question is usually mis-framed
- What a **classic Dataflow template** actually is, and what it buys you that a flex template does not
- The real cost of a classic template: Java, or the Python packaging treadmill
- The four-question decision matrix, and what to do when the answers are mixed
- The hybrid answer: templates for the 80%, flex templates for the 20%
- Why a course graduate should learn flex templates, in terms of what they can actually ship
- A worked comparison you can defend in a design review

---

## 🧠 Concept

### The question, asked properly

"Should we use a template or write custom code?" is the wrong question,
because it treats templates and custom code as opposites. They are not
opposites. A flex template *is* custom code — a Python file, in your
repository, with your business logic in it. The real axis is:

> **Who owns the failure?**

A published Google-managed template is a product: someone else wrote it,
someone else maintains it, someone else is on the hook when it breaks.
Custom code — including a flex template — is your code: you wrote it, you
version it, you test it, you deploy it, and you own it at 3am.

The second axis is **where the logic lives**. A template has a fixed
contract: a set of parameters, a fixed shape of transformation, a
guaranteed output. Custom code has whatever you write.

Most teams ask the first question ("who owns it?") when they should ask
the second ("does the contract fit?") — and then they spend three months
fighting a template that does not do the one thing they need.

### The three kinds of "template" in Dataflow

The word is overloaded, and confusing the three is the source of most of
the confusion in this area.

| | **Classic template** | **Flex template** | **Batch template** |
|---|---|---|---|
| What it is | A published, versioned artefact — a Java JAR, or a Python wheel | A Python file uploaded to a container image and run by path | A named, parameterised job definition |
| Where it lives | Google's catalogue, or your own `gs://` | Your container registry | The Dataflow job's parameters |
| Who wrote it | Google (mostly), or you | You | You |
| Language | Java (and historically Python) | Python | Any |
| You can edit the logic? | No (Google-published), yes (self-hosted) | Yes — it is your file | Yes |
| Versioned? | Yes, with a published version and a support contract | Yes — by your own tagging and Git | No — a batch template is just a job with parameters |
| Example | "Text to BigQuery", "BigQuery to BigQuery" | The course's `project/templates/batch_template.py` | A `gcloud dataflow jobs run` with `--input`/`--output` |

Two points of vocabulary discipline, because people use "batch template"
and "flex template" interchangeably and they are quite different:

- A **batch template** is a *job type*. It means "this is a batch job
  that was configured from a set of parameters". It says nothing about
  where the code came from. A flex template run as a batch job is
  *both* things.
- A **flex template** is a *deployment mechanism*. It says "the pipeline
  code is a Python file in a container image that Dataflow runs". It says
  nothing about batch vs streaming.

The most useful mental model:

```text
                    what runs the code
                    ┌──────────────────┐
   your logic ──────┤                  │
                    │  flex template   │  ← you write Python, in Git
                    │  (container +    │
                    │   entrypoint)    │
                    └──────────────────┘

                    what describes the job
                    ┌──────────────────┐
   parameters ──────┤  batch template  │  ← a parameterised job definition
                    │  (job type)      │
                    └──────────────────┘
```

### The argument FOR a template

A **published classic template** is a piece of software with a support
contract behind it. When you use "BigQuery to BigQuery" or "Datastore
Import/Export", you are buying four specific things.

**1. Someone else owns the bugs.** Not "someone else has fixed the bugs"
— someone else is *responsible* for the bugs. There is a Google
engineering team, an issue tracker, and a release cadence. When the
underlying API changes, the template is updated. You are not writing the
`WriteToBigQuery` sharding logic, the `JobStatus` polling, the temporary
table lifecycle, the `_metadata` schema evolution handling, or the
retries.

**2. The contract is stable and versioned.** A published template has a
version, a documented set of parameters, and a documented output shape.
You can upgrade the template version and know the difference. That is a
property you can put in a runbook.

**3. The operational surface is small.** No container image, no
`requirements.txt`, no dependency pinning, no "did the image build?".
You submit a job with parameters. There is nothing to compile.

**4. It is often the fastest correct implementation of a common
pattern.** Google's own templates handle partitioning, resumption,
temporary tables, and error tables in ways that took years to get right.
Reproducing "BigQuery to BigQuery" correctly, with the temp-table dance
and the failed-row handling, is a week of work you would otherwise
repeat in every project.

The honest failure mode of relying on templates: **you hit the edge of
the contract, and there is no seam to push on.** The template does not
expose the transform you need, the windowing you need, the state you
need. You are stuck with a template that is 95% right, and you cannot fix
the 5%.

### The argument FOR custom code

**1. The template does not do what you need.** This is the most common
reason, and it is usually a specific, concrete gap: the template joins on
one key, and you need to join on three. The template does a
`GROUP BY` on a single column, and you need a nested rollup. The
template does not expose a `DoFn` hook.

**2. You need a `DoFn` the template does not expose.** This is the
flexibility argument in its sharpest form. A `DoFn` is where the
business logic lives — the thing that distinguishes your pipeline from
everyone else's. If your revenue recognition rule is a 40-line `DoFn`
with a lookup and a date-dependent condition, a template that does not
accept a `DoFn` is a template that cannot express your business.

**3. You need custom windowing or state.** Templates that are
batch-shaped cannot do streaming windowing. Templates that are
SQL-shaped cannot hold keyed state across a window boundary. If your
problem involves "count distinct users per 30-minute window, with
sessionisation", you need the Beam model.

**4. You need to version your business logic.** This is the argument
people underrate. A template's parameters are a *configuration*. Your
business logic — the rules that change every quarter — should be
*versioned code*, with a commit hash, a test, a changelog and a rollback.
A parameter that says `--threshold 0.85` is not the same as a versioned
rule that says "above 0.85, and this is rule v7".

**5. You need to be able to test it.** A published template is a black
box. You cannot unit-test its internals. You can test its output, but
you cannot test the logic that produced it. If the rule is important
enough to be right, it is important enough to be a function you wrote
and can test.

The honest failure mode of custom code: **you now own the retry logic,
the error handling, the temp table lifecycle, the schema evolution, the
dependency pinning, the container image, and the 3am page.**

### What a classic template gives you that a flex template does not

This is the crux, and it is narrower than most people assume.

| Capability | Classic (published) template | Flex template |
|---|---|---|
| Google maintains the code and the bugs | yes | no |
| A published version with a support contract | yes | no (you tag your own images) |
| A documented, stable parameter contract | yes | no (you define it) |
| Google-supported SLA / support path | yes | no (your support path) |
| No container image to build or run | yes | no |
| Custom `DoFn`, custom windowing, custom state | **no** | yes |
| Your own version control, tests, CI | no | yes |
| Source readable by you | no (Google's) | yes |
| A language other than Python | yes (Java) | no (Python) |
| Works with a non-Python SDK ecosystem | yes | no |

The three rows in the top block are the real difference. The bottom block
is where the flex template wins, decisively.

Note the asymmetry: **the classic template wins on operational
ownership, and loses on functional fit.** So the decision is not "which
is better" — it is "does the published contract cover my requirement, and
do I want to own the failure?"

### The cost of a classic template

The cost is not "Java is hard". It is concrete:

**If you write it yourself** (a self-hosted classic template), you need:

- A Java (or Python 3.7-era) build, a dependency management story, and a
  packaging format Dataflow accepts.
- The `TemplateDescriptor` metadata, the parameter metadata, the
  argument validators.
- A registry to publish to, and a version discipline.

**If you use a published one**, you are locked to its contract. There is
no "extend it". You either fit or you do not.

**The Python classic-template story is worth being precise about.**
Google's published Python classic templates (Batch, Streaming) were
packaged as Python wheels with a specific directory layout and
`requirements.txt`, and they were a real option for a long time. They
have not kept pace with the flex template approach: a flex template is
"one Python file plus your dependencies in a container image", which is
strictly simpler, is version-controllable in Git, and does not need the
classic packaging layout at all. For anything you build today, if you
want Python, you want a flex template.

### The decision matrix

Four questions, in this order:

| # | Question | If yes | If no |
|---|---|---|---|
| 1 | **Is the transformation a published, common pattern** (BQ→BQ, GCS→GCS, Datastore import, Pub/Sub to BigQuery)? | Use the published template. Do not rewrite it. | Go to question 2. |
| 2 | **Is the business logic in the parameters, or in the code?** | Parameters → a batch template is fine. Code → go to question 3. | |
| 3 | **Do you need a custom `DoFn`, custom windowing, custom state, or a custom source/sink?** | Custom code (a flex template). Nothing else will do. | Go to question 4. |
| 4 | **Does the logic change on a schedule you control, and does it need to be versioned, tested and reviewed?** | Flex template, in Git, with CI. | A scheduled batch template, and revisit when it changes. |

The interesting case is a "no" on question 4 with a "yes" on question 3.
That is a pipeline whose logic will eventually need to change, but does
not change often enough to justify a full CI pipeline *today*. The
right answer is still a flex template, because the migration cost from
"batch template" to "flex template" is much higher than the migration
cost from "flex template" to "flex template with CI".

### The hybrid answer

Almost every real system is a mix. The pattern that works:

- **80%: published templates and batch templates.** The plumbing.
  Getting data from A to B. These are boring, well-solved, and should
  never consume engineering time.
- **20%: flex templates.** The business logic. The joins, the rules, the
  transformations that make the pipeline *yours*.

The architectural consequence: keep the boundary explicit. A published
template writes to a table; a flex template reads that table and does
the real work. The interface between them is a schema, and a schema is a
contract you can version independently of either side.

```text
  published template            your flex template
  ────────────────────          ─────────────────────
  ingest raw orders   ─────▶   orders_raw table
  (BQ → BQ, no code)              │
                                   ▼
                              enrich + aggregate
                              (your DoFn, your rules)
                                   │
                                   ▼
                              orders_by_region table
                              (your schema, your version)
```

The rule of thumb: **use the published template to get the data into a
table you control, then use your own code to make that table mean
something.** The moment the template's contract stops matching your
requirement, you own that piece — and it should be a flex template from
that point, not a fork of someone else's Java.

### The recommendation for a course graduate

**Learn flex templates.** Here is the argument, in order of weight:

1. **They are Python.** The entire course is Python. A classic template
   in Java means learning a second language, a second build system and a
   second deployment model, for no benefit to the pipeline.
2. **They are version-controlled in Git.** The pipeline is a file. It goes
   through code review, it has a commit hash, it is diffable, it is
   testable with the same tooling as the rest of your project.
3. **They do everything a classic template does, except publish a
   supported artefact.** The only thing you give up is the support
   contract and the Google-maintained bug fixes — and for a pipeline with
   your own business logic, those were never the valuable part.
4. **They are the same code as your local pipeline.** `project/batch_pipeline.py`
   and `project/templates/batch_template.py` share their logic. The
   template is a thin shell — argument parsing plus a `build_pipeline`
   call. You do not maintain two implementations.
5. **They are what the market is hiring for.** Almost every modern Beam
   job on Dataflow is a flex template. Classic templates are a legacy
   deployment mechanism with a shrinking catalogue.

The one thing to take from the classic-template world is the *mindset*:
a template has a **stable, documented, versioned contract**. A flex
template should have one too — and you can give it one, by writing the
parameters down, validating them, and pinning the container image by
digest rather than by `:latest`.

### The worked comparison

The course's own batch pipeline, expressed three ways.

| Dimension | Published classic template | Course flex template | Custom script on a VM |
|---|---|---|---|
| Entry point | `gcloud dataflow jobs run gs://dataflow-templates/.../TextToBigQuery --arguments=...` | `gcloud dataflow jobs run ... --image ... --input ... --output ...` | `python batch_pipeline.py` |
| Code you own | none | one Python file | one Python file |
| Business logic | fixed by the template | yours | yours |
| Versioning | template version, chosen by you | your Git tag + image digest | your Git tag |
| Testing | output comparison only | unit tests + pipeline tests | unit tests + pipeline tests |
| Deployment effort | none | container build | SSH + systemd + log rotation |
| Scaling | managed | managed | you |
| Operational burden | near zero | moderate | high |
| Cost profile | low | low | low at small scale, high at large |
| Failure ownership | Google | you | you |
| Best for | common, standard patterns | anything with your rules | prototyping, tiny loads |

And the decision for three concrete situations:

**Situation A — "Move a GCS bucket's CSV into a partitioned BigQuery
table, nightly."**
Published template. "Text to BigQuery" does exactly this, with the
partitioning and the schema handling. Writing a flex template for it is
wasted effort. *Answer: published template.*

**Situation B — "Compute net revenue per region per day, where net
revenue applies a rule that changes every quarter, and the rule depends
on a customer tier table that itself changes daily."**
The rule is code. The tier table is a join. The rule changes need
versioning. *Answer: flex template.*

**Situation C — "We already have a flex template that reads from
BigQuery and writes to BigQuery, and now we want to add a column
based on a lookup table."**
This looks like a parameter change and is not. The lookup is a join, the
column is a derived field, and the schema changes. *Answer: modify the
flex template; do not try to express a join as a template parameter.*

---

## 🛠️ Hands-On: Choosing and Building

### Step 1 — Inventory the pipelines you already have

Before choosing, look at what exists. In the course project:

```bash
cd data-engineering/data-Course/google/Dataflow
ls project/templates/
```

You have one flex template (`batch_template.py`) and one plain script
(`batch_pipeline.py`). Notice the relationship: the template's
`build_pipeline` is a near-copy of the script's. That duplication is
exactly what the chapter is arguing against, and the fix is on the next
step.

### Step 2 — Build a parameter contract for a flex template

A flex template should have a documented, validated parameter contract —
the thing it gives up from the classic template world. Here is the
pattern, using `argparse` with explicit types and required arguments:

```python
import argparse
import logging

log = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse and validate the template's parameters.

    Args:
        argv: The argument list. Defaults to `sys.argv[1:]`.

    Returns:
        The validated arguments.

    Raises:
        SystemExit: If a required parameter is missing or malformed.
    """
    parser = argparse.ArgumentParser(description="Batch revenue pipeline")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output path prefix")
    parser.add_argument(
        "--bigquery-table",
        default=None,
        help="Optional BigQuery table as project.dataset.table",
    )
    parser.add_argument(
        "--statuses",
        default="complete",
        help="Comma-separated statuses to count toward revenue",
    )
    parser.add_argument(
        "--reference",
        default=None,
        help="Optional product reference NDJSON used as a side input",
    )
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        log.info("ignoring unrecognised arguments: %s", unknown)
    return args
```

Note the deliberate use of `parse_known_args` rather than
`parse_args`. Beam's own flags (`--runner`, `--job_name`, `--streaming`,
and every Dataflow option) travel in the same argument vector, and
`parse_args` would reject them. `parse_known_args` lets the template's
own parameters and Beam's coexist. The `unknown` list is then logged, so
a typo in a template parameter is visible rather than silently ignored.

### Step 3 — Validate the parameters before building the graph

Fail fast, on the client, before a worker is ever started. This is the
single biggest advantage a flex template has over a classic one, and
almost nobody uses it:

```python
def validate_args(args: argparse.Namespace) -> tuple[str, ...]:
    """Validate the parsed parameters.

    Args:
        args: The parsed arguments.

    Returns:
        The normalised tuple of statuses.

    Raises:
        ValueError: If a parameter value is not usable.
    """
    statuses = tuple(s.strip() for s in args.statuses.split(",") if s.strip())
    if not statuses:
        raise ValueError("--statuses must name at least one status")
    for status in statuses:
        if not status.isascii() or not status.isalnum():
            raise ValueError(f"invalid status: {status!r}")
    if args.bigquery_table:
        parts = args.bigquery_table.split(".")
        if len(parts) != 3 or not all(parts):
            raise ValueError(
                "--bigquery-table must be project.dataset.table, "
                f"got {args.bigquery_table!r}"
            )
    return statuses
```

A template that validates its own parameters will fail in 200
milliseconds on the submitter's laptop instead of 90 seconds later on a
worker with a `ValueError` buried in a stack trace.

### Step 4 — See the difference in the job graph

The template and the script produce the same graph, but the template's
graph is visible in the Dataflow UI with a stable set of labels, which is
what makes it debuggable at 3am:

```python
import apache_beam as beam


def build_pipeline(
    pipeline: beam.Pipeline,
    *,
    input_path: str,
    output_path: str,
    statuses: tuple[str, ...] = ("complete",),
) -> None:
    """Build the revenue pipeline.

    Args:
        pipeline: The pipeline to add transforms to.
        input_path: The input path.
        output_path: The output path prefix.
        statuses: Which statuses count toward revenue.
    """
    orders = (
        pipeline
        | "ReadOrders" >> beam.io.ReadFromText(input_path)
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
    )

    completed = orders | "KeepCompletedOrders" >> beam.Filter(
        lambda row: len(row) > 6 and row[6] in statuses
    )

    summary = (
        completed
        | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "RevenueByRegion" >> beam.CombinePerKey(sum)
    )

    summary | "WriteSummaryCsv" >> beam.io.WriteToText(output_path)
```

Run it locally to confirm the graph is the same as the script's:

```bash
python project/templates/batch_template.py \
  --input ./sample_data/orders.csv \
  --output ./out/template_check
```

### Step 5 — Build and publish the flex template image

The image is the deployment artefact. Pin it by digest, not by tag, once
it is in production:

```bash
# Build the template image.
gcloud dataflow flex-template build project/templates/batch_template.py \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
  --temp-location gs://YOUR_BUCKET/tmp

# Run it.
gcloud dataflow jobs run dataflow-batch-template \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
  --temp-location gs://YOUR_BUCKET/tmp \
  --input gs://YOUR_BUCKET/orders.csv \
  --output gs://YOUR_BUCKET/summary

# For production, pin the digest.
gcloud dataflow jobs run dataflow-batch-template \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template@sha256:0123456789abcdef \
  --temp-location gs://YOUR_BUCKET/tmp \
  --input gs://YOUR_BUCKET/orders.csv \
  --output gs://YOUR_BUCKET/summary
```

### Step 6 — Compare the two deployment paths

| Step | Classic published template | Flex template |
|---|---|---|
| Build an artefact | no | yes (container image) |
| Register a version | yes (Google's registry) | yes (your tag / digest) |
| Validate parameters | yes (built into the template) | **your job** — do it explicitly |
| Run | `gcloud dataflow jobs run <template-gcs-path> --arguments=...` | `gcloud dataflow jobs run <name> --image ...` |
| Change the logic | upgrade the template version | rebuild the image |
| Roll back | pick the old version | pick the old digest |

The row that deserves attention is "validate parameters". In a classic
template, that is someone else's job. In a flex template, it is yours,
and skipping it is how you end up with a job that fails on a worker with
`ValueError: unknown currency: 'CHF'`.

---

## 🛠️ Common Errors and Fixes

### `SystemExit: 2` immediately after launch, with no log output

`argparse` rejected the arguments. The most common cause: the template
used `parse_args` instead of `parse_known_args`, and Beam's own flags
(`--runner`, `--job_name`, `--streaming`) were treated as unknown
positional arguments.

```python
# wrong
args = parser.parse_args(argv)

# right
args, unknown = parser.parse_known_args(argv)
```

### `error: unrecognized arguments: --job_name ...` from `gcloud`

The reverse problem: you passed Beam flags to a `gcloud dataflow jobs run`
invocation that does not accept them. `gcloud dataflow jobs run` has its
own flag set; the Beam options go to the *template*, not to `gcloud`.

```bash
# Beam options are set via --flags in the flex-template invocation,
# or via the template's own argument list.
gcloud dataflow jobs run my-job \
  --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
  --flags "--streaming --window_size 60"
```

### `ValueError: unknown currency: 'CHF'` on a worker, not on submit

Your parameter validation is missing. The failure happens on a worker
because the currency check is inside the `DoFn`, not in the argument
parsing. Move the class of checks that can be made from parameters into
the client's validation step, as in Step 3.

### `Docker build failed: no such file or directory` during `flex-template build`

The build ran from the wrong directory, and the path to the template
file was relative to a different working directory. Use a path relative
to where you are:

```bash
cd data-engineering/data-Course/google/Dataflow
gcloud dataflow flex-template build project/templates/batch_template.py ...
```

### The job used the wrong template version

The image was referenced by `:latest`, and `latest` had been rebuilt
between the launch and the retry. Pin by digest:

```bash
gcloud dataflow jobs describe JOB_ID --format='value(labels)'
gcloud container images describe gcr.io/YOUR_PROJECT_ID/dataflow/batch-template@sha256:... 
```

### `ModuleNotFoundError: No module named 'transforms'` in the container

The template image does not contain your project modules. The course
template works around this by inserting the parent directory on
`sys.path`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

In a real container, include the module in the image's `COPY` and install
it, or use a `requirements.txt` that references the package.

---

## 💡 Production Notes

- **The most common bad outcome is not choosing wrong — it is choosing a
  template for a job that has custom logic, and then fighting it.** The
  moment you find yourself wanting to change the template's internals,
  you have already answered the question.
- **A published template's real value is in the parts you would get wrong
  yourself**: resumption, temporary tables, error tables, schema
  evolution, and the `_metadata` row. Do not reimplement those for a
  pattern Google already publishes.
- **Owning the code means owning the boring parts too.** Retries, timeouts,
  partial-failure handling, and dead-letter routing. Budget for them or
  do not go custom.
- **Validate parameters on the client.** A flex template's biggest
  advantage is that it can fail in 200ms on the submitter's machine
  instead of 90 seconds later on a worker. Almost nobody does this.
- **Pin your image by digest, not by tag.** A `:latest` image means the
  job you are debugging is not the job you deployed, and a retry of the
  "same" job runs different code.
- **Templates hide their resource usage.** A published template picks the
  worker count and machine type. A flex template picks nothing, and
  defaults to whatever the runner thinks. If a template's resource
  profile is wrong for your data volume, you cannot fix it — that is
  another argument for custom code.
- **A batch template is not a deployment mechanism.** Calling a
  parameterised job a "template" leads to arguments about "should we use
  a template" that are really arguments about parameterisation. Be
  precise in the vocabulary; it saves hours.
- **Plan the migration path from classic to flex.** Most organisations
  end up with a mixed estate for years. Keep the interface between the
  two a *schema* — a table, with a version — so you can move the logic
  across without moving the data.
- **The hybrid is the answer almost everyone should give.** Templates for
  the plumbing, custom code for the rules, and an explicit schema at the
  boundary. Resist the tidiness of "one way of doing everything".

---

## 🔑 Key Takeaways

- The real question is not "template or custom code" but **"who owns the
  failure, and does the contract fit?"**
- A **classic template** is a published, versioned artefact with a support
  contract. A **flex template** is your Python file in a container. A
  **batch template** is a parameterised job type. They are different
  axes, not competitors.
- Classic templates win on **operational ownership** (someone else owns
  the bugs, no image to build, a stable contract) and lose on
  **functional fit** (no custom `DoFn`, no custom windowing, no state).
- Use a published template when the pattern is standard and your logic is
  in the parameters. Use custom code when the logic is in the code.
- The decision matrix: *is it a standard pattern? → is the logic in the
  parameters? → do you need a custom `DoFn`? → does the logic change and
  need versioning?*
- The **hybrid** answer — templates for the 80% of plumbing, flex
  templates for the 20% of business logic, with a schema at the
  boundary — is what most mature teams converge on.
- **Learn flex templates**: they are Python, they live in Git, they are
  testable, and they do everything a classic template does except publish
  a supported artefact.
- A flex template should still have a **stable, documented, validated
  parameter contract** — that is the property you have to build for
  yourself, and the one most teams skip.

---

## 📚 Practice Exercises

1. **Run the matrix against your own pipelines.** Take three real
   pipelines from your work and answer the four questions for each.
   For each, write one sentence justifying the answer.
   *Expected answer:* at least one of them should land in the "flex
   template" cell, and the reason should be "the logic is code and it
   changes", not "templates are more flexible".

2. **Write the parameter contract.** For the course's batch pipeline,
   write the full parameter documentation a classic template would
   publish: name, type, required or optional, default, and a one-line
   description. Then implement the validation for every optional
   parameter. *Expected answer:* the `--bigquery-table` validation should
   reject anything that is not exactly three dot-separated parts.

3. **Refactor to remove the duplication.** `project/batch_pipeline.py`
   and `project/templates/batch_template.py` each have a `build_pipeline`
   with almost the same body. Refactor so the template imports the
   script's `build_pipeline` rather than repeating it. Then confirm the
   template still runs and produces the same output.
   *Expected answer:* the template's `build_pipeline` becomes a thin
   wrapper, and the output is byte-identical.

4. **Pin by digest.** Build the template image, get its digest, and write
   the `gcloud dataflow jobs run` invocation that references the digest
   rather than `:latest`. Explain in two sentences what a reader of the
   job metadata can now conclude about the code that ran.

5. **Find the seam.** Take a published Google template you have used —
   "Text to BigQuery", "BigQuery to BigQuery", "Datastore Import/Export" —
   and write down the *one* requirement it cannot express. Then write the
   two lines of design that would fix it, and say which side of the
   hybrid boundary the fix belongs on.

6. **A design review.** Write a one-page memo arguing for flex templates
   over classic templates for a team of eight data engineers, with no
   existing Java capability. Include the three strongest arguments, the
   one strongest argument *against* your position, and how you would
   answer it.

---

## 📖 Further Reading

- Dataflow flex templates — https://cloud.google.com/dataflow/docs/guides/templates/flex
- Using Python flex templates — https://cloud.google.com/dataflow/docs/guides/templates/flex/using-python
- Classic templates — https://cloud.google.com/dataflow/docs/guides/templates/classic
- Beam's template catalogue — https://cloud.google.com/dataflow/docs/guides/templates/overview
- Dataflow job management — https://cloud.google.com/dataflow/docs/guides/managing-jobs
- Apache Beam's design documents on the Beam model — https://beam.apache.org/documentation/basic-topics/
