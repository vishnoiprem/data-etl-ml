# Section 10 Quiz — Glue DataBrew

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** What is the primary use case for AWS Glue DataBrew?

- A. A managed Spark cluster for running PySpark ETL jobs
- B. A visual, no-code data preparation tool for analysts and business users
- C. A streaming ETL engine for real-time data pipelines
- D. A SQL-based query service for S3 data lakes

---

**Q2.** In DataBrew, what is a *Recipe*?

- A. A Dataset definition pointing at an S3 file or Glue table
- B. A versioned sequence of data transformations (e.g. FILL_NULLS, REMOVE_DUPLICATES, RENAME_COLUMN)
- C. A statistics artifact showing value distributions, null counts, and distinct counts
- D. A scheduled run that applies a Project to a Dataset

---

**Q3.** What is the difference between a DataBrew *Project* and a DataBrew *Recipe*?

- A. A Project is the input; a Recipe is the output target
- B. A Project is an interactive session where you click to build transformations; a Recipe is the versioned artifact produced by that session
- C. A Project is a Python script; a Recipe is a SQL query
- D. There is no difference — they are synonyms

---

**Q4.** You run a DataBrew Job whose Recipe has 3 steps (FILL_NULLS, FILTER_BY_VALUE, RENAME_COLUMN). The source Dataset has 100 rows, but the output S3 location is empty (0 rows). What is the most likely cause?

- A. The S3 output bucket does not exist
- B. The Glue Data Catalog table is missing
- C. The `FILTER_BY_VALUE` step in the Recipe drops every row (e.g. wrong condition or wrong column)
- D. DataBrew Jobs always run incrementally and never overwrite output

---

**Q5.** Which of the following are valid output targets for a DataBrew Job?

- A. S3 only (CSV format)
- B. S3 in CSV, JSON, Parquet, or ORC, OR a Glue Data Catalog table
- C. Redshift only
- D. DynamoDB only

---

# Answer Key

1. **B** — A visual, no-code data preparation tool for analysts and business users. DataBrew is positioned as the analyst-friendly counterpart to writing PySpark in a Glue Job. It is not a Spark cluster (that's Glue ETL), not a streaming engine (that's Kinesis/Glue Streaming), and not a SQL query service (that's Athena).
2. **B** — A versioned sequence of data transformations. A Recipe is the central artifact in DataBrew: a list of steps like FILL_NULLS, REMOVE_DUPLICATES, RENAME_COLUMN, CHANGE_DATA_TYPE, FILTER_BY_VALUE, GROUP_BY, JOIN, SCALE_VALUE, FLAG_OUTLIERS. (A) describes a Dataset, (C) describes a Profile, (D) describes a Job.
3. **B** — A Project is the interactive session in the DataBrew console where an analyst clicks through steps; a Recipe is the versioned artifact produced and saved from that session. You build the recipe *inside* a project, then publish it so it can be reused by a Job.
4. **C** — The `FILTER_BY_VALUE` step in the Recipe drops every row. This is the DataBrew analog of the Glue Job "job ran successfully but wrote 0 rows" debug pattern from Section 7: a transform filters out all rows before they reach the output. S3 bucket existence and the Data Catalog table are not required for S3 output, and DataBrew Jobs do overwrite output by default.
5. **B** — S3 in CSV, JSON, Parquet, or ORC, OR a Glue Data Catalog table. These are the two valid output families for a DataBrew Job: file-based output to S3 (in one of the four supported formats) or a registered Glue Data Catalog table.
