# Section 1 Quiz — Introduction

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** What is the primary abstraction AWS Glue uses to run ETL without provisioning servers?

- A. EC2 instances
- B. A managed Spark cluster
- C. Lambda functions
- D. ECS tasks

---

**Q2.** Which of the following is *not* a category of ETL covered in the course?

- A. Batch
- B. Streaming
- C. Data quality
- D. OLAP cube refresh

---

**Q3.** Which Glue version corresponds to Spark 3.3 + Python 3.10?

- A. 1.0
- B. 2.0
- C. 3.0
- D. 4.0

---

**Q4.** Which of the following is the 4th downloadable resource for the course?

- A. The course slide deck
- B. The Glue Job Python script
- C. The quiz answer key
- D. The role play video

---

**Q5.** The course is built around 3 production-grade pipelines. Which is *not* one of them?

- A. Batch ETL
- B. Streaming ETL
- C. Data quality pipeline
- D. ML training pipeline

---

# Answer Key

1. **B** — A managed Spark cluster. AWS Glue is serverless on top of Spark.
2. **D** — OLAP cube refresh. The 3 categories are batch, streaming, and data quality.
3. **D** — 4.0. (Glue 2.0 = Spark 2.4 + Python 3.7; Glue 3.0 = Spark 3.1 + Python 3.7; Glue 4.0 = Spark 3.3 + Python 3.10.)
4. **B** — The Glue Job Python script. The 4 are city_temperature.csv, the IAM trust policy, the CloudFormation template, and the Glue script.
5. **D** — ML training pipeline. The 3 are batch, streaming, and data quality.
