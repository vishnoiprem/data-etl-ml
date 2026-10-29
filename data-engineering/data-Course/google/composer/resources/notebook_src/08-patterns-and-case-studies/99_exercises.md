## Exercises

1. **Pick the trigger rule.** For each of these joins, state the `trigger_rule` and justify it in one sentence:
   (a) a join after a `BranchOperator` where either branch may be taken; (b) a cleanup task that must run even if the load failed; (c) a join where every upstream must have succeeded and you want to fail loudly otherwise; (d) a join where at least one upstream must have succeeded; (e) an alert task that should fire only if something failed; (f) a task that must run after every upstream has finished, successful or not.

2. **Harder — convert the branch to dynamic mapping.** Take the `patterns_branch` DAG's `full_load` / `incremental_load` branch and replace it with a dynamically-mapped `load_region` task that expands over the regions present in the data. Write the join with the correct trigger rule, and add an assertion that the join runs when one mapped instance fails and when all of them succeed.

3. **Harder — prove the loop anti-pattern is worse than it looks.** Write a DAG file that generates 50 tasks with a loop, and a second that generates one mapped task. Compare the number of task instances created when the data contains 4 regions, and explain what each DAG's scheduler load looks like at parse time.

4. **Harder — design a Dataset-based producer/consumer pair.** Write two DAGs: `orders_producer` (which writes a partition and updates the dataset) and `orders_consumer` (scheduled on the dataset). Then answer three questions in writing: (a) how does the consumer learn the producer's logical date? (b) what happens if the producer fails silently for a week? (c) how would you prevent the consumer from running twice for one producer update?

5. **Harder — make the backfill safe under concurrency.** A backfill of 30 dates runs with `max_active_runs=5`. Two dates write to the same partition decorator. Explain exactly how that happens, what the symptom would be in the output table, and which two settings prevent it. Then explain why raising `max_active_runs` to speed up the backfill makes the problem *more* likely, not less.

6. **Hardest — audit the course's DAGs against the pattern catalogue.** For each DAG in `project/dags/`, name the patterns it demonstrates and identify the one pattern each is *missing* that a production version would need. Then pick the DAG with the biggest gap and sketch the improvement.
