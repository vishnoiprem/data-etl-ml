# Section 3 Quiz — S3 Buckets Hands-on

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** Which S3 bucket setting, when enabled, prevents a public bucket policy from making objects publicly readable?

- A. Versioning
- B. Server-side encryption
- C. Block public access
- D. Object lock

---

**Q2.** You upload `city_temperature.csv` (25 KB) to S3. You then run a Glue Crawler on the bucket. The crawler creates a table in the Glue Data Catalog. The table's schema has 0 columns. What is the most likely cause?

- A. The Glue Crawler IAM role is missing `s3:GetObject`
- B. The CSV file's first row is a header and the crawler didn't infer the schema
- C. The CSV file uses commas, but the crawler expects tabs
- D. The Glue Data Catalog is in a different region

---

**Q3.** Which S3 event notification target is the most common trigger for a Glue Job?

- A. SQS queue
- B. SNS topic
- C. EventBridge (via S3 event)
- D. Lambda function

---

**Q4.** You delete a file in an S3 bucket that has versioning enabled. What happens?

- A. The file is permanently deleted
- B. A delete marker is created; the file's previous version is preserved
- C. The bucket is emptied
- D. CloudFormation rolls back

---

**Q5.** You upload `city_temperature.csv` to `s3://my-bucket/input/`. The Glue Crawler crawls `s3://my-bucket/`. The crawler creates a table named `input` with the schema. You then upload another file to `s3://my-bucket/input/2026/`. The crawler re-runs. How many tables are in the catalog now?

- A. 1 (the table is updated in place)
- B. 2 (`input` and `input_2026`)
- C. 2 (`input` and `2026`)
- D. 0 (the crawler errors because the schema might have changed)

---

# Answer Key

1. **C** — Block public access. This is the safety net that overrides bucket policies and ACLs. AWS recommends it on for all buckets.
2. **B** — Header inference. The Glue Crawler by default treats the first row as a header and uses it to infer column names. If the file has *no* header (or the row is misformatted), the schema is empty.
3. **C** — EventBridge. The modern pattern: S3 → EventBridge → Glue Trigger → Glue Job. The older S3-to-Lambda pattern still works but is being deprecated.
4. **B** — Delete marker. Versioned delete is a soft delete; the previous version is recoverable.
5. **A** — 1 table. The Glue Crawler treats the entire bucket as a single table when there's a common prefix; the table schema is updated to include the new file's columns if any are added.
