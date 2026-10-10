# Section 5 Quiz — CloudFormation Templates for Glue

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** What is the primary purpose of the AWS Glue Data Catalog?

- A. To store the actual data
- B. To store metadata (schema, location, partitions) about the data
- C. To run SQL queries
- D. To encrypt data at rest

---

**Q2.** A Glue Crawler runs against an S3 bucket with 3 different file types: CSV, JSON, and Parquet. How many tables does the crawler create by default?

- A. 1 (it merges all file types into a single table)
- B. 3 (one per file type, partitioned by file extension)
- C. 0 (the crawler errors on heterogeneous data)
- D. It depends on whether a classifier is configured

---

**Q3.** A Glue Job's `--source-bucket` argument is set to `my-bucket`. The job's script reads `s3://my-bucket/input/`. The job fails with `Unable to parse S3 path`. What is the most likely cause?

- A. The bucket does not exist
- B. The script is not using the argument correctly
- C. The IAM role is missing `s3:ListBucket`
- D. The Glue version is too old

---

**Q4.** A Glue Workflow has 3 Glue Jobs in sequence: Job A triggers Job B, Job B triggers Job C. Job A runs and succeeds. Job B does *not* run. What is the most likely cause?

- A. Job B's IAM role is wrong
- B. The Trigger from Job A to Job B is not configured (or is configured to fail)
- C. Job A's output is not in the expected location
- D. The Workflow is paused

---

**Q5.** A Glue Job's source is a 100-GB CSV file in S3. The job reads it, aggregates, and writes 200 MB of Parquet. The job takes 4 hours. What is the single most effective change to reduce runtime?

- A. Increase `NumberOfWorkers` from 2 to 10
- B. Convert the source CSV to Parquet
- C. Add a Glue Crawler
- D. Enable versioning on the bucket

---

# Answer Key

1. **B** — Metadata. The Glue Data Catalog is the central metadata store for AWS analytics services (Athena, EMR, Redshift Spectrum, Glue Jobs).
2. **D** — Depends on the classifier. By default, Glue uses built-in classifiers (CSV, JSON, Parquet, etc.) and creates a table per detected file type. A custom classifier can change this.
3. **B** — Script argument. The `--source-bucket` argument is passed to the script as a Job argument. The script must read `sys.argv` to extract it. If the script hardcodes a different path, it errors.
4. **B** — Trigger not configured. Workflows chain jobs via Triggers. If the A→B trigger is missing or in a "failed" state, B doesn't run.
5. **B** — Convert CSV to Parquet. CSV is row-based and not splittable in S3; Parquet is columnar and splittable. A 100-GB CSV takes 4 hours; the same data in Parquet typically takes 20-30 minutes.
