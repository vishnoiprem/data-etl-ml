# Interview Question Bank — Google Cloud Composer with Apache Airflow

> **The question bank for this course.** Module files build the understanding;
> [top-50.md](top-50.md) is the final-night revision.

---

## What this bank is

This is a working interview bank for Google Cloud Composer and Apache
Airflow — not a flashcard list, and not a set of definitions. Every question
was selected because the answer **changes what you build**, and every answer
is written the way a senior engineer who has actually run this in production
would say it out loud.

Each answer follows the same six-part structure:

1. **The direct answer**, in the first one or two sentences. No throat-clearing.
2. **The mechanism** — the internal Airflow concept that explains it: the
   data interval, the scheduler loop, the metadata DB, XCom as a table, the
   trigger rule, the executor queue, the SLA clock.
3. **When the alternative wins** — the trade-off and its boundary condition.
   "It depends" is never acceptable without saying what it depends on.
4. **A production failure story** — the actual symptom, and the fix.
5. **Code**, where it clarifies and nowhere else.
6. **Numbers** — row counts, seconds, dollar figures, worker counts, the
   `1245` accepted orders and the `113592.19` EUR for AMER.

The failure story is the part interviewers probe. Anyone can recite that
`retries` re-runs a task; a senior interviewer wants to know whether you have
*seen* the day's rows written four times, and what the fix was.

### How the bank is structured

| File | Questions | What it covers |
|---|---:|---|
| [01-orchestration-fundamentals.md](01-orchestration-fundamentals.md) | 14 | Why orchestration exists; Airflow vs Spark vs Beam; architecture; the scheduler; executors; the 3am question |
| [02-dags-scheduling-and-templates.md](02-dags-scheduling-and-templates.md) | 14 | DAG anatomy; schedules; logical date vs data interval; catchup; Jinja templating; variables, params, connections |
| [03-tasks-xcom-and-branching.md](03-tasks-xcom-and-branching.md) | 14 | Operators; task dependencies; XCom; trigger rules; branching; dynamic task mapping; sensors |
| [04-reliability-and-production.md](04-reliability-and-production.md) | 16 | SLAs; retries; idempotency; backfills; testing; monitoring; cost; security; troubleshooting |
| [05-composer-and-gcp.md](05-composer-and-gcp.md) | 12 | Provisioning; environment sizing; image versions; the UI; IAM; cleanup and billing; Composer vs self-managed Airflow |
| [top-50.md](top-50.md) | **50** | The highest-yield subset — read this the night before |

**Total: 120 questions.** The module files are arranged in the order the
course teaches the material; `top-50.md` is arranged by *interview theme*,
because that is how a conversation actually goes.

### How the bank maps to the chapters

| Module file | Primary chapters |
|---|---|
| `01-orchestration-fundamentals.md` | [01-what-is-orchestration-and-why-airflow](../chapters/01-what-is-orchestration-and-why-airflow.md), [15-airflow-vs-beam-vs-spark](../chapters/15-airflow-vs-beam-vs-spark.md), [02-airflow-architecture-and-concepts](../chapters/02-airflow-architecture-and-concepts.md), [10-executors-and-workers](../chapters/10-executors-and-workers.md), [16-airflow-on-kubernetes](../chapters/16-airflow-on-kubernetes.md) |
| `02-dags-scheduling-and-templates.md` | [03-dags-and-scheduling](../chapters/03-dags-and-scheduling.md), [05-templates-and-jinja](../chapters/05-templates-and-jinja.md), [06-variables-params-and-connections](../chapters/06-variables-params-and-connections.md), [01-what-is-orchestration-and-why-airflow](../chapters/01-what-is-orchestration-and-why-airflow.md) |
| `03-tasks-xcom-and-branching.md` | [04-tasks-and-operators](../chapters/04-tasks-and-operators.md), [07-xcom](../chapters/07-xcom.md), [08-branching-and-dynamic-tasks](../chapters/08-branching-and-dynamic-tasks.md), [09-sensors-and-deferrable-operators](../chapters/09-sensors-and-deferrable-operators.md) |
| `04-reliability-and-production.md` | [11-slice-and-slas](../chapters/11-slice-and-slas.md), [12-idempotency-and-reliability](../chapters/12-idempotency-and-reliability.md), [03-dags-and-scheduling](../chapters/03-dags-and-scheduling.md), [13-testing-dags](../chapters/13-testing-dags.md), [14-orchestration-patterns](../chapters/14-orchestration-patterns.md), [15-airflow-vs-beam-vs-spark](../chapters/15-airflow-vs-beam-vs-spark.md), [06-variables-params-and-connections](../chapters/06-variables-params-and-connections.md) |
| `05-composer-and-gcp.md` | [02-airflow-architecture-and-concepts](../chapters/02-airflow-architecture-and-concepts.md), [10-executors-and-workers](../chapters/10-executors-and-workers.md), [16-airflow-on-kubernetes](../chapters/16-airflow-on-kubernetes.md), [15-airflow-vs-beam-vs-spark](../chapters/15-airflow-vs-beam-vs-spark.md), [03-dags-and-scheduling](../chapters/03-dags-and-scheduling.md) |
| `top-50.md` | All of the above — selected for cross-layer coverage |

Every question in the bank is answerable from the sixteen chapters and the
runnable project in `../project/`. The bank does not introduce concepts the
course does not teach; it probes whether the concepts survived contact with
production.

---

## The study plan

**A seven-day plan for someone who knows Python and has used a scheduler.**
If you have a week, do this. If you have two, spread each day over two
sessions. If you have a day, read `top-50.md` twice and skim the failure
stories in the module files.

### Day 1 — Why orchestration, and what Airflow actually is

Read [01-what-is-orchestration-and-why-airflow](../chapters/01-what-is-orchestration-and-why-airflow.md)
and [15-airflow-vs-beam-vs-spark](../chapters/15-airflow-vs-beam-vs-spark.md).
These two chapters answer the question an interviewer asks in the first five
minutes: *what problem does this solve that a cron job does not?* If your
answer is "scheduling", you have not answered.

Then read [02-airflow-architecture-and-concepts](../chapters/02-airflow-architecture-and-concepts.md)
and [10-executors-and-workers](../chapters/10-executors-and-workers.md).
You need the five components and the executor's job in your head as a
diagram, not as a list.

Finish with [01-orchestration-fundamentals.md](01-orchestration-fundamentals.md),
answering all 14 questions **out loud**. Not in your head — out loud,
standing up. If you cannot say the answer in two sentences, you do not have
the first half of it.

### Day 2 — DAGs, schedules, and the data interval

This is the day the off-by-one bug is either killed or survives.

Read [03-dags-and-scheduling](../chapters/03-dags-and-scheduling.md) until
you can state the rule for the logical date without hesitating: *a daily DAG's
run for `2026-01-15` processes `[2026-01-15, 2026-01-16)`*. Then read
[05-templates-and-jinja](../chapters/05-templates-and-jinja.md) and
[06-variables-params-and-connections](../chapters/06-variables-params-and-connections.md).

Do this before answering the module questions: take
`project/core/pipeline_logic.py` and write the SQL filter for a given logical
date **from memory**. Then check `logical_date_window(logical_date,
data_interval_days=1)` in the same file. The difference between what you
wrote and what that function returns is the whole lesson.

Then answer [02-dags-scheduling-and-templates.md](02-dags-scheduling-and-templates.md)
aloud.

### Day 3 — Tasks, XCom, branching

Read [04-tasks-and-operators](../chapters/04-tasks-and-operators.md),
[07-xcom](../chapters/07-xcom.md),
[08-branching-and-dynamic-tasks](../chapters/08-branching-and-dynamic-tasks.md)
and [09-sensors-and-deferrable-operators](../chapters/09-sensors-and-deferrable-operators.md).

Run the local runner and watch the dependency states:

```bash
python project/local_runner.py --list
python project/local_runner.py --dag branching_load --describe
```

The state vocabulary (`failed` vs `upstream_failed` vs `skipped`) is worth
memorising exactly — it is the difference between a false page and a real
one.

Then answer [03-tasks-xcom-and-branching.md](03-tasks-xcom-and-branching.md)
aloud.

### Day 4 — The reliability core

Read [11-slice-and-slas](../chapters/11-slice-and-slas.md) and
[12-idempotency-and-reliability](../chapters/12-idempotency-and-reliability.md).
These two chapters are the ones that separate a candidate who knows Airflow
from one who has shipped on it.

The single most important sentence in this course: **a retry re-runs your
code and undoes nothing.** Everything about `retries > 0`, `WRITE_APPEND`,
backfills, and `depends_on_past` follows from it.

Then answer the first ten questions of
[04-reliability-and-production.md](04-reliability-and-production.md) aloud.

### Day 5 — Testing, monitoring, and the cost of Airflow

Read [13-testing-dags](../chapters/13-testing-dags.md) and
[14-orchestration-patterns](../chapters/14-orchestration-patterns.md).

Write one structure test of your own against the course DAGs — even just
`assert dag.catchup is False` and `assert bag.import_errors == {}`. Running
it is worth more than reading about it, because the failure mode you will
hit (a missing `import_errors` check producing a confusing "DAG not found")
is the one the question is about.

Then answer the rest of
[04-reliability-and-production.md](04-reliability-and-production.md).

### Day 6 — Composer on GCP

Read [16-airflow-on-kubernetes](../chapters/16-airflow-on-kubernetes.md) and
re-read the Composer sections of
[02-airflow-architecture-and-concepts](../chapters/02-airflow-architecture-and-concepts.md).

You do not need a GCP account for the questions; you need to *understand*
them. Know what Composer manages for you, what it charges you for, and what
it deletes when you delete the environment.

Then answer [05-composer-and-gcp.md](05-composer-and-gcp.md) aloud, and do
the mock below.

### Day 7 — `top-50.md` and a mock interview

Read [top-50.md](top-50.md) **once, end to end**, in one sitting. Do not
write anything down yet. Notice which answers you could not produce.

Then go back and answer the ones you missed, out loud, writing down the
mechanism and the number if you can. Re-read only the answers you got wrong
or got vaguely right.

Finally, do a mock: pick 20 questions at random, set a timer for 90 seconds
per question, and answer each one **out loud** with the structure —
direct answer, mechanism, trade-off, failure story, number. The point of the
mock is not whether you know the answer; it is whether you can *get to* it
under pressure.

> **The honest advice:** `top-50.md` is for the final night. Reading it on
> day one is the single most common way people waste this bank. The module
> files are for building the understanding — they are slower, they repeat
> themselves, and they contain questions that will never be asked. That
> repetition is the point: it is what turns "I have read about the data
> interval" into "I know what happens when the upstream lands at 03:00 and
> the run starts three hours late."

---

## How to use the bank

**Do not memorise.** Memorised answers sound memorised, and a senior
interviewer can tell within two questions. What you are building is not
recall; it is the ability to *reason from a mechanism to a decision*.

**Write your own answer first.** Before you read the bank's answer, write
your own — three or four sentences, from memory. Then compare. You will find
one of three things:

- You knew it, and the bank adds a detail or a number. Good — you were
  nearly there, and the detail is worth keeping.
- You knew the shape but not the mechanism. This is the interesting case.
  Go back to the chapter and find the mechanism.
- You had the wrong model entirely. This is the most valuable outcome. Stop
  and re-read the chapter.

**Answer out loud.** Speaking is a different task from reading, and it is the
task the interview actually is. If you can only answer when you can see the
words, you have not prepared. The aim is: question → first two sentences
immediately, mechanism second, numbers third.

**Probe the failure story.** When you tell a failure story, ask yourself
"what was the symptom?" — a run state, a log line, a row count that was
double, a bill. An interviewer who hears "it was flaky" will not follow up.
An interviewer who hears "the run went green for three days, loaded 0 rows,
and the finance reconciliation caught it" will ask three good questions.

**Use the numbers.** The bank attaches numbers to most answers because
numbers are what distinguish an answer from a recital: `1245` accepted
orders, `113592.19` EUR for AMER, a `48 KB` XCom, a `2-hour` SLA,
`30–60 seconds` of Kubernetes pod startup, `$700/month` for an environment.
You do not need to memorise them exactly — you need to *have* them, so that
"it needs retries" becomes "the load appends to a partition-scoped table with
`WRITE_TRUNCATE`, so a retry replaces `20260115` and leaves the rest of the
table alone".

**Revise by theme, not by file.** If you are weak in one area, read the
relevant `##` section of `top-50.md` and then go back to the corresponding
module file. Reading the bank front to back twice is less effective than
reading the weak section three times.

**Use the local runner as a sparring partner.** `project/local_runner.py`
executes the course DAGs with a real dependency graph and a real XCom store,
without Airflow installed. Point it at a broken DAG and predict the states
before you run it. The prediction is the skill.

---

## What the interviewer is actually testing

Each theme in `top-50.md` probes a different mental model. Know which one you
are in, and you will know which details to lead with.

### "Architecture and the scheduler" — do you know where the work happens?

They are testing whether you understand that Airflow is a **control plane**
and that the executor is a *queue*, not a worker. The interesting answers are
about the scheduler's seven-step loop, the metadata DB as the single source
of truth, and what happens when the scheduler stalls (no new runs are
created — which looks identical to "the DAG is not scheduled"). A candidate
who says "Airflow runs Python on a worker" has described half of it. A
candidate who says "the scheduler writes task instances to the metadata DB,
the executor picks them up, and if the executor is Celery then a worker
process in the environment pulls the queue" is answering.

### "DAGs, schedules and the data interval" — do you know what a run *means*?

This is the most commonly botched area, and it is the cheapest to get right.
They are testing whether your model is **interval-based** or **wall-clock
based**. The tell is the SQL filter. A candidate who writes
`WHERE date(order_ts) = '{{ ds }}'` has the wrong model; one who writes
`WHERE order_ts >= '{{ data_interval_start }}' AND order_ts < '{{
data_interval_end }}'` has the right one. Follow-ups go to `catchup`,
`max_active_runs`, and `schedule=None` — all of which are only interesting
once the interval model is right.

### "XCom, branching and dynamic tasks" — do you know what belongs where?

They are testing **judgement about data size and control flow**. XCom is a
row in a database table; the interesting answer says "a count of 1245, a
partition name of 20260115, a GCS URI — not 5000 order rows, because a
200 KB XCom slows every DAG in the environment". Then the branching
questions test whether you know that `BranchOperator` returns task ids, that
the branch task itself succeeds, and that `skipped` propagates through
trigger rules in ways that surprise people.

### "Reliability: retries, SLAs and idempotency" — do you know what Airflow does *not* promise?

They are testing honesty about **delivery semantics**. The trap is
"exactly-once". The strong answer distinguishes at-least-once execution from
exactly-once *effect*, explains why a retry cannot undo a write, and then
says what makes "effectively once" true: partition-scoped writes, `MERGE` on
a business key, and a dedup key like `20260115:order_id`. The SLA question
has its own trap — Airflow measures the SLA from the **end of the data
interval**, not from the run's start — and that answer is worth more than
any amount of recital about `sla_miss_callback`.

### "Production: testing, cost, security and troubleshooting" — can you run and debug the thing?

They are testing **operational fluency**: what a 403 means, which signal
catches a "green but empty" run, why `dag.test()` really executed a
production load, what a variable versus a connection versus a param means for
encryption, and how you triage a DAG that will not appear. These questions
are often asked by people who have never written the pipeline but have paged
you at 3 a.m. about it.

### "Composer on GCP" — can you make the platform decision?

They are testing whether you can **defend a platform choice**: Composer
versus self-managed Airflow on GKE, what the environment size actually
controls, what a version bump costs you, and what happens to your code and
your connections when the environment is deleted. The strong answer has a
decision rule with a boundary — "Composer if you want the environment to be
someone else's problem; self-managed if the KubernetesExecutor's per-pod
configuration and the pod startup tax are worth the operational load".

### "Design and trade-offs" — can you defend a decision?

They are testing whether you can **make and justify a choice** under
competing constraints. "We used TaskFlow" is not an answer; "we used
`@task` because the pipeline has one branch and four joins, and the
alternative was passing four XCom keys through `task_id=` kwargs, which is
where we got the typo" is. Watch for the follow-up: they will ask what you
would do differently at 10× the data — and 10× the data is usually 5000
orders becoming 5,000,000, and the answer is BigQuery or Dataflow, not a
bigger worker.

---

## A note on versions

This bank was written against **Apache Airflow 2.x (2.8.2 / 2.9.3 / 2.10.x)
on Google Cloud Composer 2**, with Composer 3 (GKE-based) noted where it
differs.

The model — the data interval, the scheduler loop, XCom as a table, trigger
rules, the executor queue, the SLA clock — is stable across Airflow 2.x
releases, and the reasoning is what is being tested. The **API details are
not**: parameter names, defaults, and operator modules do change between
releases.

Specifically, note the renames this bank uses deliberately:

- **`schedule`** replaced `schedule_interval` in Airflow 2.4. Both work on
  2.8/2.9/2.10; only `schedule` is forward-looking.
- **`logical_date`** replaced `execution_date` in Airflow 2.2. `execution_date`
  is deprecated. Note that `dag.test()` still takes `execution_date` as its
  keyword argument in the 2.5–2.9 line, which is an inconsistency, not a
  mistake on your part.
- **Dynamic task mapping** (`.expand()` / `.expand_kwargs()`) requires
  Airflow 2.3+.
- **Datasets** require Airflow 2.4+.
- **Deferrable operators** and the triggerer require Airflow 2.2+.

So: **check every API detail against the Airflow version you have.** If a
snippet in these answers does not match your environment, the answer's
*reasoning* is still correct — but the code is not, and on an interview that
is the part that gets typed.

---

## Related material

- The course chapters — [../chapters/](../chapters/)
- The runnable project — [../project/](../project/)
- The Composer notebooks — [../notebooks/](../notebooks/)
- The night-before revision — [top-50.md](top-50.md)
