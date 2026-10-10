# Section 10 Quiz — DataBrew

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** What is the primary use case for AWS Glue DataBrew?

- A. Real-time data ingestion
- B. Visual data preparation (no-code transformations)
- C. Streaming ETL
- D. SQL-based analytics

---

**Q2.** In a DataBrew project, what is a *recipe*?

- A. A versioned collection of data transformations
- B. A SQL query
- C. A Glue Job
- D. A data source

---

**Q3.** A DataBrew job runs successfully but writes 0 rows to the output. The recipe has 3 steps. The source file has 100 rows. What is the most likely cause?

- A. The recipe's filter step dropped all rows
- B. The output S3 bucket is wrong
- C. The IAM role is wrong
- D. The DataBrew job is in the wrong region

---

**Q4.** Which DataBrew step would you use to replace nulls in the `country` column with `"UNKNOWN"`?

- A. `FILL_NULLS` or `IMPUTE`
- B. `DROP_NULL`
- C. `REPLACE`
- D. `MAP`

---

**Q5.** A DataBrew job's output is in CSV. The same job, with the same recipe, now produces JSON. What is the most likely cause?

- A. The job's output format setting was changed
- B. The recipe was changed
- C. The source data changed
- D. The IAM role was changed

---

# Answer Key

1. **B** — Visual data prep. DataBrew is the no-code sibling of Glue Jobs. Same data catalog, same sources, but the transformations are visual (point-and-click) and the output is a recipe (versioned).
2. **A** — Versioned transformations. A recipe is a sequence of steps; it can be versioned, published, and re-run.
3. **A** — Filter dropped all rows. The most common cause: a `FILTER` step with a condition that doesn't match any rows (e.g., `country = "USA"` when the source is `US`).
4. **A** — `FILL_NULLS`. DataBrew has a `FILL_NULLS` step (or `IMPUTE` for more advanced imputation).
5. **A** — Output format setting was changed. The recipe doesn't control the output format; the DataBrew Job's output configuration does.
