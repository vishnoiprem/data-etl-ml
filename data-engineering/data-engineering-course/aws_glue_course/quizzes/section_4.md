# Section 4 Quiz — Glue Catalog / Crawler / Job / Trigger / Workflow

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** What is the AWS Glue Data Catalog, at a high level?

- A. A managed NoSQL store used to cache Spark shuffle data
- B. A managed Hive metastore that holds databases, tables, and partitions for data in S3
- C. An S3 bucket with a special prefix that Glue writes schema files to
- D. A built-in replacement for Amazon Athena's query engine

---

**Q2.** You point a Glue Crawler at an S3 prefix containing `city_temperature.csv` (with a header row) and run it. Which statement best describes what the Crawler produces?

- A. A single Glue Database named after the bucket, with one Table per row of the CSV
- B. A Glue Table per S3 prefix, whose schema is inferred from the CSV (header row used as column names, types inferred from values)
- C. A fully-transformed Parquet dataset written back to S3, with the schema embedded in the file footer
- D. An Athena workgroup that points at the CSV file

---

**Q3.** When configuring a Glue Job, which property controls the IAM role that Glue assumes to read from S3, write logs, and access the Data Catalog?

- A. `ScriptLocation`
- B. `WorkerType`
- C. `Role`
- D. `GlueVersion`

---

**Q4.** You want a Glue Job to run every day at 06:00 UTC. Which Trigger type is the most appropriate?

- A. On-Demand
- B. Conditional
- C. Scheduled
- D. EventBridge

---

**Q5.** What is the main difference between a Glue Workflow and a Glue Trigger?

- A. A Workflow is a visual drag-and-drop editor (Glue Studio), while a Trigger is the underlying cron entry
- B. A Trigger fires a single Job on a schedule or event; a Workflow chains multiple Triggers across multiple Jobs into an end-to-end pipeline
- C. A Workflow is for streaming Jobs and a Trigger is for batch Jobs
- D. They are the same thing — "Workflow" is just the newer name for "Trigger"

---

# Answer Key

1. **B** — A managed Hive metastore that holds databases, tables, and partitions for data in S3. The Data Catalog is the central metadata layer that Athena, Redshift Spectrum, and EMR can all query.
2. **B** — A Glue Table per S3 prefix, with the schema inferred from the CSV (the built-in CSV classifier uses the first row as the header and infers column types from the values). A Crawler does not transform the data, it only discovers schema.
3. **C** — `Role`. This is the IAM role Glue assumes; it must have trust for `glue.amazonaws.com` and permissions on S3, CloudWatch Logs, and the Data Catalog. `ScriptLocation` is the S3 path to the .py file, `WorkerType` is G.025X / G.1X / G.2X / etc., and `GlueVersion` is the Glue/Spark runtime (4.0 in this course).
4. **C** — Scheduled. A Scheduled Trigger uses a cron expression in UTC, which is exactly the "every day at 06:00 UTC" use case. On-Demand is manual, Conditional predicates on another Job's state (e.g. `SUCCEEDED`), and EventBridge reacts to AWS events via a JSON event pattern.
5. **B** — A Trigger fires a single Job on a schedule or event; a Workflow chains multiple Triggers across multiple Jobs into an end-to-end pipeline. Workflows are the way to model multi-step ETL (Crawl → Job A → Job B → Job C) as a single unit you can start, stop, and monitor.
